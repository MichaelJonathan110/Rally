import { useState } from 'react';
import { MailWarning, X } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useResendVerification } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';

/** Dismissible banner shown to signed-in users whose email is not yet verified. */
export function EmailVerifyBanner() {
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.accessToken);
  const [dismissed, setDismissed] = useState(false);
  const resend = useResendVerification();

  if (!token || !user || user.email_verified !== false || dismissed) return null;

  return (
    <div
      role="status"
      className="mb-4 flex flex-wrap items-center gap-3 rounded-2xl border border-warning/40 bg-warning/10 px-4 py-3"
    >
      <MailWarning className="h-5 w-5 shrink-0 text-warning" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-ink">Verifikasi emailmu</p>
        <p className="text-xs text-ink-3">
          {resend.isSuccess
            ? 'Email verifikasi terkirim. Cek kotak masukmu.'
            : 'Kami perlu memastikan alamat email ini benar.'}
        </p>
      </div>
      <Button
        size="sm"
        variant="outline"
        loading={resend.isPending}
        onClick={() => resend.mutate()}
      >
        Kirim ulang email verifikasi
      </Button>
      <button
        onClick={() => setDismissed(true)}
        aria-label="Tutup pemberitahuan"
        className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-ink-3 hover:bg-ink/[0.05] hover:text-ink"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
