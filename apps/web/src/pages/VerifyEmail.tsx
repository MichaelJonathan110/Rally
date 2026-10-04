import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import * as authApi from '@/api/auth';
import { useAuthStore } from '@/store/auth';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { extractDetail } from '@/api/client';

type Status = 'loading' | 'success' | 'error';

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const qc = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);
  const [status, setStatus] = useState<Status>(token ? 'loading' : 'error');
  const [message, setMessage] = useState<string>(
    token ? '' : 'Tautan verifikasi tidak valid atau sudah kedaluwarsa.',
  );
  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true;
    authApi
      .verifyEmail(token)
      .then(async (res) => {
        setMessage(res.message || 'Email kamu berhasil diverifikasi.');
        setStatus('success');
        try {
          const user = await authApi.me();
          setUser(user);
          await qc.invalidateQueries({ queryKey: ['me'] });
        } catch {
          /* not signed in - ignore */
        }
      })
      .catch((err) => {
        setMessage(extractDetail(err));
        setStatus('error');
      });
  }, [token, qc, setUser]);

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4 py-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-ink">Verifikasi email</h1>
      </div>
      <Card className="text-center">
        {status === 'loading' ? (
          <div className="flex flex-col items-center gap-3" role="status">
            <Loader2 className="h-8 w-8 animate-spin text-action" aria-hidden />
            <p className="text-sm text-ink-3">Memverifikasi emailmu...</p>
          </div>
        ) : status === 'success' ? (
          <div className="flex flex-col items-center gap-3" role="status">
            <CheckCircle2 className="h-8 w-8 text-success" aria-hidden />
            <p className="text-sm text-ink-2">{message}</p>
            <Link to="/login">
              <Button>Masuk</Button>
            </Link>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3" role="alert">
            <XCircle className="h-8 w-8 text-danger" aria-hidden />
            <p className="text-sm text-ink-2">{message}</p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <Link to="/login" className="text-sm font-medium text-action hover:underline">
                Kembali ke halaman masuk
              </Link>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
