import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useResetPassword } from '@/hooks/useAuth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { BRAND } from '@/config/brand';
import { extractDetail } from '@/api/client';

const schema = z
  .object({
    new_password: z.string().min(8, 'Minimal 8 karakter').max(128),
    confirm: z.string().min(1, 'Konfirmasi kata sandi'),
  })
  .refine((v) => v.new_password === v.confirm, {
    message: 'Kata sandi tidak sama',
    path: ['confirm'],
  });
type FormValues = z.infer<typeof schema>;

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const navigate = useNavigate();
  const reset = useResetPassword();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  if (!token) {
    return (
      <div className="mx-auto flex max-w-md flex-col gap-4 py-6">
        <Card className="text-center">
          <p className="text-sm text-ink-2" role="alert">
            Tautan atur ulang tidak valid atau sudah kedaluwarsa.
          </p>
          <p className="mt-4 text-sm">
            <Link to="/forgot-password" className="font-medium text-action hover:underline">
              Minta tautan baru
            </Link>
          </p>
        </Card>
      </div>
    );
  }

  const onSubmit = (values: FormValues) => {
    reset.mutate(
      { token, newPassword: values.new_password },
      { onSuccess: () => navigate('/login') },
    );
  };

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 py-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-ink">Atur ulang kata sandi</h1>
        <p className="mt-1 text-sm text-ink-3">Buat kata sandi baru untuk akun {BRAND.name}mu.</p>
      </div>
      <Card>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Kata sandi baru"
            type="password"
            autoComplete="new-password"
            error={errors.new_password?.message}
            hint="Minimal 8 karakter."
            {...register('new_password')}
          />
          <Input
            label="Konfirmasi kata sandi baru"
            type="password"
            autoComplete="new-password"
            error={errors.confirm?.message}
            {...register('confirm')}
          />
          {reset.isError ? (
            <p className="text-sm text-danger" role="alert">
              {extractDetail(reset.error as never)}
            </p>
          ) : null}
          <Button type="submit" fullWidth loading={reset.isPending}>
            Simpan kata sandi baru
          </Button>
          <p className="text-center text-sm text-ink-3">
            <Link to="/login" className="font-medium text-action hover:underline">
              Kembali ke halaman masuk
            </Link>
          </p>
        </form>
      </Card>
    </div>
  );
}
