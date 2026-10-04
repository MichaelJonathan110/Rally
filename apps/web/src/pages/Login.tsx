import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { useLogin } from '@/hooks/useAuth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { BRAND } from '@/config/brand';
import { extractDetail } from '@/api/client';

const schema = z.object({
  identifier: z.string().min(1, 'Masukkan email atau nama pengguna'),
  password: z.string().min(1, 'Masukkan kata sandi'),
});
type FormValues = z.infer<typeof schema>;

export default function Login() {
  const navigate = useNavigate();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = (values: FormValues) => {
    const isEmail = values.identifier.includes('@');
    login.mutate(
      {
        password: values.password,
        ...(isEmail ? { email: values.identifier } : { username: values.identifier }),
      },
      { onSuccess: () => navigate('/') },
    );
  };

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 py-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-ink">Selamat datang di {BRAND.name}</h1>
        <p className="mt-1 text-sm text-ink-3">{BRAND.tagline}</p>
      </div>
      <Card>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Email atau nama pengguna"
            placeholder="kamu@contoh.com"
            autoComplete="username"
            error={errors.identifier?.message}
            {...register('identifier')}
          />
          <Input
            label="Kata sandi"
            type="password"
            placeholder="Kata sandimu"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register('password')}
          />
          <div className="text-right">
            <Link to="/forgot-password" className="text-sm font-medium text-action hover:underline">
              Lupa password?
            </Link>
          </div>
          {login.isError ? (
            <p className="text-sm text-danger" role="alert">
              {extractDetail(login.error as never)}
            </p>
          ) : null}
          <Button type="submit" fullWidth loading={login.isPending}>
            Masuk
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-ink-3">
          Belum punya akun?{' '}
          <Link to="/register" className="font-medium text-action hover:underline">
            Daftar sekarang
          </Link>
        </p>
      </Card>
      <p className="text-center text-xs text-ink-3">
        Akun demo: admin@rally.app / host@rally.app / user@rally.app
      </p>
    </div>
  );
}
