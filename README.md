# İşçi İfade Tutanağı — Web Sürümü

Masaüstü (.exe) sürümünün tarayıcıda çalışan hâli. Kurulum/uyumluluk derdi yoktur;
her müfettiş kendi hesabıyla girer, girdiği işçi bilgileri **yalnızca kendi hesabında** saklanır.
Vercel'e deploy edilecek şekilde tek proje olarak düzenlenmiştir.

## Yapı

```
api/            → Vercel Python fonksiyonu (FastAPI)
  index.py        tüm uç noktalar
  auth.py         hesap, şifre hash'i, oturum
  depo.py         Supabase / yerel JSON veri katmanı
  hafiza_db.py    kullanıcı hafızası
  paket.py        ekler dizimi ZIP üretimi
  cekirdek/       PDF parser, docx üretici (masaüstü sürümüyle ortak)
  sablonlar/      T.C. amblemi
public/         → statik ön yüz (index.html, app.js, style.css)
vercel.json     → yönlendirme yapılandırması
supabase_kurulum.sql
requirements.txt
```

## 1) Supabase kurulumu

1. [supabase.com](https://supabase.com) → **New project** oluşturun.
2. **SQL Editor → New query** → `supabase_kurulum.sql` içeriğini yapıştırıp **Run**.
3. **Project Settings → API** bölümünden şunları alın:
   - `Project URL` → `SUPABASE_URL`
   - `service_role` anahtarı → `SUPABASE_KEY`

> `service_role` anahtarı yönetici yetkilidir; **yalnızca sunucu tarafında** kullanılır,
> ön yüze asla konmaz, `.env` dosyası git'e yüklenmez.

## 2) Vercel'e deploy

1. Projeyi GitHub'a yükleyin.
2. Vercel → **Add New → Project** → repoyu seçin (framework: *Other*, ayar değiştirmeyin).
3. **Settings → Environment Variables**'a ekleyin:

   | Ad | Değer |
   |---|---|
   | `SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `SUPABASE_KEY` | `service_role` anahtarı |

4. **Deploy**. Açılan adreste giriş ekranı gelir.

Kontrol: `https://<adresiniz>/api/saglik` → `{"ok":true,"supabase":true,"depo":"Supabase"}`
`supabase:false` görüyorsanız ortam değişkenleri okunmuyordur (ekledikten sonra **redeploy** gerekir).

## 3) Yerel çalıştırma

```
pip install -r requirements.txt
```

`baslat.bat` → `http://127.0.0.1:8000`

Ortam değişkeni tanımlamazsanız veriler `api/veri/` altında JSON olarak tutulur
(Supabase'e gerek kalmadan geliştirme yapabilirsiniz).

## Kullanım

1. **Hesap Oluştur** — kullanıcı adı + şifre (en az 6 karakter). Sonra **Giriş Yap**.
2. **Görev Listesi PDF** yükleyin → işyerleri listelenir, birini seçin.
3. **İşyeri Bilgileri** otomatik dolar (sicil, unvan, işveren, adres) — düzeltilebilir.
4. **İşçi Kimliği**: yazmaya başlayın, daha önce girdikleriniz alt alta çıkar.
   İsmi seçince o işçinin **tüm bilgileri** otomatik dolar.
   Alternatif: **İşveren Formu İndir** → işverene gönder → **Dolu Formu Yükle**.
5. **İfade Bilgileri**: 🟢 anahtarlar Evet/Hayır, 🔴 kutular elle doldurulur.
6. **Önizleme** oluşturun; standart cümleleri metin kutusunda düzenleyebilirsiniz.
7. **Tutanağı İndir** (tek işçi .docx) veya **Listeye Ekle** → **Ekler Dizimi ZIP İndir**
   (tüm işçiler + `ekler dizimi (işyeri)` klasör yapısı). ZIP'i masaüstüne çıkarın.

## Masaüstü sürümünden farkları

| | Masaüstü (.exe) | Web |
|---|---|---|
| Kurulum | exe'ye çift tıkla | tarayıcı, kurulum yok |
| Kullanıcı | tek | çok kullanıcılı, giriş ekranlı |
| Veri | `~/İfadeTutanagi_veri` | Supabase (yerelde JSON) |
| Klasörler | masaüstünde oluşur | ZIP indirilir, masaüstüne çıkarılır |

Word belgesinin sayfa düzeni iki sürümde de birebir aynıdır (ortak çekirdek).

## Güvenlik

- Şifreler PBKDF2-HMAC-SHA256 (rastgele tuz, 200.000 tur) ile saklanır; düz metin tutulmaz.
- Oturum jetonları veritabanında tutulur, 12 saat sonra düşer.
- Her kullanıcının hafızası ayrıdır; başka hesap göremez.
- Supabase tablolarında RLS açıktır ve hiçbir policy tanımlı değildir:
  anon anahtarla tablolara erişilemez, yalnızca sunucu `service_role` ile yazar.
- İşçi kimlik bilgileri kişisel veridir; `api/veri/` ve `.env` git'e yüklenmez
  (`.gitignore` içinde). Deploy ettiğiniz adresi herkese açık paylaşmayın.
