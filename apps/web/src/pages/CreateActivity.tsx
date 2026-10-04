import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useCreateActivity } from '@/hooks/useActivities';
import { useVenues } from '@/hooks/useVenues';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader } from '@/components/ui/Card';
import { ImageUpload } from '@/components/ImageUpload';
import { extractDetail } from '@/api/client';
import { CATEGORIES } from '@/config/categories';
import type { ActivityCategory } from '@/api/types';

const CATEGORY_IDS = CATEGORIES.map((c) => c.id) as [ActivityCategory, ...ActivityCategory[]];

const schema = z.object({
  title: z.string().min(3, 'Judul minimal 3 karakter').max(140),
  description: z.string().max(2000).optional(),
  category: z.enum(CATEGORY_IDS),
  skill_level: z.enum(['beginner', 'intermediate', 'advanced', 'expert', 'any']),
  venue_id: z.string().optional(),
  starts_at: z.string().min(1, 'Pilih waktu mulai'),
  max_participants: z.coerce.number().int().min(2, 'Minimal 2').max(200),
  cost: z.coerce.number().min(0, 'Tidak boleh negatif').max(100000000),
});
type FormValues = z.infer<typeof schema>;

export default function CreateActivity() {
  const navigate = useNavigate();
  const venues = useVenues({ limit: 100 });
  const create = useCreateActivity();
  const [coverUrl, setCoverUrl] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      category: CATEGORIES[0].id,
      skill_level: 'any',
      max_participants: 10,
      cost: 0,
    },
  });

  const onSubmit = (v: FormValues) => {
    create.mutate(
      {
        title: v.title,
        description: v.description || undefined,
        category: v.category,
        skill_level: v.skill_level,
        venue_id: v.venue_id || null,
        starts_at: new Date(v.starts_at).toISOString(),
        max_participants: v.max_participants,
        cost_per_person_cents: Math.round(v.cost),
        cover_url: coverUrl || undefined,
      },
      { onSuccess: (a) => navigate(`/activities/${a.id}`) },
    );
  };

  const venueOptions = [
    { value: '', label: 'Tanpa venue / belum ditentukan' },
    ...(venues.data?.items.map((v) => ({ value: v.id, label: `${v.name} - ${v.city}` })) ?? []),
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-ink">Selenggarakan kegiatan</h1>
        <p className="mt-1 text-sm text-ink-3">
          Isi detailnya dan kegiatan langsung tayang di jaringan RALLY.
        </p>
      </div>
      <Card>
        <CardHeader title="Detail kegiatan" />
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input label="Judul" error={errors.title?.message} {...register('title')} />
          <ImageUpload
            purpose="activity"
            label="Foto sampul"
            hint="Tampil di kartu kegiatan. Opsional."
            value={coverUrl}
            onChange={setCoverUrl}
          />
          <div>
            <label htmlFor="description" className="label">
              Deskripsi
            </label>
            <textarea
              id="description"
              rows={4}
              className="input resize-y"
              placeholder="Apa yang bisa peserta harapkan?"
              {...register('description')}
            />
            {errors.description ? (
              <p className="mt-1 text-xs text-danger">{errors.description.message}</p>
            ) : null}
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select
              label="Kategori"
              options={CATEGORIES.map((c) => ({ value: c.id, label: c.label }))}
              error={errors.category?.message}
              {...register('category')}
            />
            <Select
              label="Tingkat keahlian"
              options={[
                { value: 'any', label: 'Semua' },
                { value: 'beginner', label: 'Pemula' },
                { value: 'intermediate', label: 'Menengah' },
                { value: 'advanced', label: 'Mahir' },
                { value: 'expert', label: 'Ahli' },
              ]}
              error={errors.skill_level?.message}
              {...register('skill_level')}
            />
          </div>
          <Select label="Venue" options={venueOptions} {...register('venue_id')} />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Input
              label="Mulai"
              type="datetime-local"
              error={errors.starts_at?.message}
              {...register('starts_at')}
            />
            <Input
              label="Maks peserta"
              type="number"
              min={2}
              error={errors.max_participants?.message}
              {...register('max_participants')}
            />
            <Input
              label="Biaya per orang (Rp)"
              type="number"
              step="1"
              min={0}
              error={errors.cost?.message}
              {...register('cost')}
            />
          </div>
          {create.isError ? (
            <p className="text-sm text-danger" role="alert">
              {extractDetail(create.error)}
            </p>
          ) : null}
          <Button type="submit" fullWidth loading={create.isPending}>
            Terbitkan kegiatan
          </Button>
        </form>
      </Card>
    </div>
  );
}
