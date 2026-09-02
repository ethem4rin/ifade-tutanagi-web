-- ============================================================
-- İşçi İfade Tutanağı — Supabase kurulum
-- Supabase panelinde:  SQL Editor > New query > yapıştır > Run
-- ============================================================

-- Kullanıcı hesapları -----------------------------------------
create table if not exists public.kullanicilar (
  anahtar    text primary key,              -- normalize edilmiş kullanıcı adı
  ad         text not null,                 -- görünen kullanıcı adı
  tam_ad     text,                          -- Volkan AYDIN
  tuz        text not null,                 -- PBKDF2 tuzu (hex)
  ozet       text not null,                 -- PBKDF2 özeti (hex) — şifre DEĞİL
  olusturma  timestamptz default now()
);

-- Oturumlar (sunucusuz ortamda bellekte tutulamaz) -------------
create table if not exists public.oturumlar (
  jeton      text primary key,
  kullanici  text not null references public.kullanicilar(anahtar) on delete cascade,
  bitis      double precision not null      -- unix zaman damgası
);

create index if not exists oturumlar_kullanici_idx on public.oturumlar(kullanici);

-- Kullanıcı hafızası (işçi kayıtları, otomatik tamamlama) ------
create table if not exists public.hafiza (
  kullanici   text primary key references public.kullanicilar(anahtar) on delete cascade,
  veri        jsonb not null default '{}'::jsonb,
  guncelleme  timestamptz default now()
);

-- ============================================================
-- Güvenlik: RLS açık, hiçbir anonim erişim yok.
-- Uygulama service_role anahtarıyla bağlanır (RLS'i atlar) ve
-- yetkilendirmeyi kendi oturum jetonlarıyla yapar.
-- Bu sayede anon anahtar sızsa bile tablolar okunamaz.
-- ============================================================
alter table public.kullanicilar enable row level security;
alter table public.oturumlar    enable row level security;
alter table public.hafiza       enable row level security;

-- (Bilerek hiç policy tanımlanmadı: anon/authenticated erişemez.)

-- Süresi dolmuş oturumları temizlemek için (isteğe bağlı, elle çalıştırın):
--   delete from public.oturumlar where bitis < extract(epoch from now());
