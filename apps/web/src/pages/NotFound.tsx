import { Link } from 'react-router-dom';
import { Compass, Home as HomeIcon } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { BRAND } from '@/config/brand';

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <p className="text-6xl font-extrabold text-action/30">404</p>
      <h1 className="text-2xl font-bold text-ink">Halaman tidak ditemukan</h1>
      <p className="max-w-sm text-sm text-ink-3">
        Halaman yang kamu cari tidak ada di {BRAND.name}. Mungkin sudah dipindahkan atau dihapus.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <Link to="/">
          <Button>
            <HomeIcon className="h-4 w-4" /> Kembali ke beranda
          </Button>
        </Link>
        <Link to="/discover">
          <Button variant="outline">
            <Compass className="h-4 w-4" /> Jelajah
          </Button>
        </Link>
      </div>
    </div>
  );
}
