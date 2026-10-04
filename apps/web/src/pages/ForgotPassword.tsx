import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { useForgotPassword } from '@/hooks/useAuth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { BRAND } from '@/config/brand';
import { extractDetail } from '@/api/client';

const schema = z.object({
  email: z.string().email('Masukkan email yang valid'),
});
type FormValues = z.infer<typeof schema>;

export default function ForgotPassword() {
  const forgot = useForgotPassword();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const sent = forgot.isSuccess;

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 py-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-ink">Lupa kata sandi</h1>
        <p className="mt-1 text-sm text-ink-3">
          Kami akan mengirim tautan untuk mengatur ulang kata sandi {BRAND.name}mu.
        </p>
      </div>
      <Card>
        {sent ? (
          <div className="space-y-4 text-center">
            <p className="text-sm text-ink-2" role="status">
              Jika email tersebut terdaftar, kami sudah mengirim tautan atur ulang. Cek email Anda
              (termasuk folder spam).
            </p>
            <Link to="/login" className="text-sm font-medium text-action hover:underline">
              Kembali ke halaman masuk
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit((v) => forgot.mutate(v.email))} className="space-y-4">
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="kamu@contoh.com"
              error={errors.email?.message}
              {...register('email')}
            />
            {forgot.isError ? (
              <p className="text-sm text-danger" role="alert">
                {extractDetail(forgot.error as never)}
              </p>
            ) : null}
            <Button type="submit" fullWidth loading={forgot.isPending}>
              Kirim tautan atur ulang
            </Button>
            <p className="text-center text-sm text-ink-3">
              Ingat kata sandimu?{' '}
              <Link to="/login" className="font-medium text-action hover:underline">
                Masuk
              </Link>
            </p>
          </form>
        )}
      </Card>
    </div>
  );
}
