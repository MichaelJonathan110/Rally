import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { useRegister } from '@/hooks/useAuth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { BRAND } from '@/config/brand';
import { extractDetail } from '@/api/client';

const schema = z.object({
  username: z.string().min(3, 'Minimal 3 karakter').max(50),
  email: z.string().email('Masukkan email yang valid'),
  password: z.string().min(8, 'Minimal 8 karakter').max(128),
});
type FormValues = z.infer<typeof schema>;

export default function Register() {
  const navigate = useNavigate();
  const signup = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 py-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-ink">Gabung {BRAND.name}</h1>
        <p className="mt-1 text-sm text-ink-3">Buat akunmu dalam hitungan detik</p>
      </div>
      <Card>
        <form
          onSubmit={handleSubmit((v) => signup.mutate(v, { onSuccess: () => navigate('/') }))}
          className="space-y-4"
        >
          <Input label="Nama pengguna" error={errors.username?.message} {...register('username')} />
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />
          <Input
            label="Kata sandi"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password')}
          />
          {signup.isError ? (
            <p className="text-sm text-danger" role="alert">
              {extractDetail(signup.error as never)}
            </p>
          ) : null}
          <Button type="submit" fullWidth loading={signup.isPending}>
            Buat akun
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-ink-3">
          Sudah punya akun?{' '}
          <Link to="/login" className="font-medium text-action hover:underline">
            Masuk
          </Link>
        </p>
      </Card>
    </div>
  );
}
