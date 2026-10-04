import { useCallback, useEffect, useRef, useState } from 'react';
import { ImagePlus, Loader2, UploadCloud, X } from 'lucide-react';
import { resolveMediaUrl, uploadFile, type MediaPurpose } from '@/api/media';
import { cn } from '@/lib/utils';
import { extractDetail } from '@/api/client';

const MAX_BYTES = 5 * 1024 * 1024;

export interface ImageUploadProps {
  /** Backend namespace the file is stored under. */
  purpose: MediaPurpose;
  /** Current image URL (absolute or stored relative '/media/...'). */
  value?: string | null;
  /** Called with the returned relative URL after a successful upload. */
  onChange: (url: string) => void;
  label?: string;
  hint?: string;
  className?: string;
  /** Rendered preview shape: round for avatars, rounded rect otherwise. */
  shape?: 'circle' | 'rect';
}

/**
 * Drag-or-click image picker with client-side validation, preview, upload
 * progress and a callback carrying the stored URL back to the parent form.
 */
export function ImageUpload({
  purpose,
  value,
  onChange,
  label,
  hint,
  className,
  shape = 'rect',
}: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(resolveMediaUrl(value) ?? null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setPreview(resolveMediaUrl(value) ?? null);
  }, [value]);

  const pick = useCallback(
    async (file: File | undefined | null) => {
      if (!file) return;
      setError(null);
      if (!file.type.startsWith('image/')) {
        setError('File harus berupa gambar (JPG, PNG, WEBP, atau GIF).');
        return;
      }
      if (file.size > MAX_BYTES) {
        setError('Ukuran gambar maksimal 5 MB.');
        return;
      }
      const localUrl = URL.createObjectURL(file);
      setPreview(localUrl);
      setUploading(true);
      try {
        const res = await uploadFile(file, purpose);
        setPreview(resolveMediaUrl(res.url) ?? res.url);
        onChange(res.url);
      } catch (err) {
        setPreview(resolveMediaUrl(value) ?? null);
        setError(extractDetail(err) || 'Gagal mengunggah gambar.');
      } finally {
        setUploading(false);
        URL.revokeObjectURL(localUrl);
      }
    },
    [purpose, onChange, value],
  );

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    void pick(e.dataTransfer.files?.[0]);
  };

  const clear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreview(null);
    setError(null);
    onChange('');
  };

  const round = shape === 'circle';

  return (
    <div className={cn('w-full', className)}>
      {label ? <p className="mb-1.5 block text-sm font-medium text-ink-2">{label}</p> : null}
      <div
        role="button"
        tabIndex={0}
        aria-label={label ?? 'Unggah gambar'}
        onClick={() => !uploading && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !uploading) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          'group relative flex cursor-pointer flex-col items-center justify-center overflow-hidden',
          'border border-dashed bg-surface transition-colors',
          round ? 'h-28 w-28 rounded-full' : 'min-h-40 w-full rounded-xl',
          dragging ? 'border-action bg-action/5' : 'border-line hover:border-ink/25 hover:bg-ink/[0.02]',
          uploading && 'cursor-wait',
        )}
      >
        {preview ? (
          <>
            <img src={preview} alt="" className="h-full w-full object-cover" />
            {uploading ? (
              <span className="absolute inset-0 grid place-items-center bg-ink/40 text-ink-inv">
                <Loader2 className="h-6 w-6 animate-spin" aria-hidden />
              </span>
            ) : (
              <button
                type="button"
                onClick={clear}
                aria-label="Hapus gambar"
                className="absolute right-2 top-2 grid h-7 w-7 place-items-center rounded-full bg-ink/70 text-ink-inv transition-colors hover:bg-ink"
              >
                <X className="h-4 w-4" aria-hidden />
              </button>
            )}
          </>
        ) : (
          <span className="flex flex-col items-center gap-1.5 px-4 text-center text-ink-3">
            {uploading ? (
              <Loader2 className="h-6 w-6 animate-spin text-action" aria-hidden />
            ) : (
              <UploadCloud className="h-6 w-6 text-action" aria-hidden />
            )}
            <span className="text-xs font-medium text-ink-2">
              {uploading ? 'Mengunggah…' : 'Klik atau seret gambar'}
            </span>
            {!round ? <span className="text-2xs">JPG, PNG, WEBP · maks 5 MB</span> : null}
          </span>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          void pick(e.target.files?.[0]);
          e.target.value = '';
        }}
      />
      {error ? (
        <p className="mt-1 text-xs text-danger" role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="mt-1 text-xs text-ink-3">{hint}</p>
      ) : null}
    </div>
  );
}

export { ImagePlus };
export default ImageUpload;
