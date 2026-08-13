# Gala Tahmin

Küçük bir arkadaş grubunun Galatasaray'ın resmî maç sonuçlarını tahmin etmesi için React/Vite, Neon PostgreSQL, Drizzle, Clerk ve Vercel üzerinde çalışan uygulama.

## Mimari

Tarayıcı yalnızca `/api` endpoint'lerine istek yapar. Neon bağlantısı, API-Football anahtarı, Clerk secret ve cron secret sadece Vercel fonksiyonlarında kullanılır. Maç başlamadan önce tahmin endpoint'i yalnızca oturum sahibinin tahminini döndürür. Tahmin yazımı, tek SQL ifadesinde veritabanı zamanı ile kilitlenir.

## Kurulum

```bash
cp .env.example .env
npm install
npm run db:migrate
npm run db:seed
npm run dev
```

Windows PowerShell'de `cp` yerine `Copy-Item .env.example .env` kullanın.

### Environment değişkenleri

| Değişken | Nerede kullanılır |
| --- | --- |
| `DATABASE_URL` | Neon serverless PostgreSQL bağlantısı |
| `FOOTBALL_API_KEY` | Yalnızca fixture sync fonksiyonu |
| `TARGET_TEAM_ID` | API-Football takım ID'si (Galatasaray için varsayılan `645`) |
| `VITE_CLERK_PUBLISHABLE_KEY` | İstemci tarafı Clerk anahtarı |
| `CLERK_SECRET_KEY` | Vercel tarafında Clerk doğrulaması |
| `CRON_SECRET` | Vercel Cron endpoint koruması |

Hiçbir secret'ı `VITE_` ile başlatmayın ve `.env` dosyasını commit etmeyin.

## Neon ve Drizzle

1. [Neon](https://neon.tech) üzerinde proje oluşturup connection string'i `DATABASE_URL` olarak ekleyin.
2. `npm run db:migrate` ile `users`, `matches`, `predictions` tablolarını oluşturun.
3. Şema değişikliği için `npm run db:generate`, ardından `npm run db:migrate` çalıştırın.
4. Yerel görsel veri için `npm run db:seed` çalıştırın. Seed Clerk kullanıcısı oluşturmaz.

İlk yöneticiyi güvenle oluşturmak için giriş yaptıktan sonra Neon SQL Editor'da ilgili kullanıcıyı güncelleyin: `UPDATE users SET role = 'admin' WHERE clerk_user_id = 'user_...';` Bu işlemden sonra admin endpoint'i veritabanındaki rolü doğrular.

## Clerk

Clerk'te uygulama oluşturun, e-posta ile oturum açmayı açın ve publishable/secret key'leri `.env` ve Vercel Environment Variables'a ekleyin. Vercel'de Clerk'in ilgili production domainine izin verildiğini doğrulayın. İlk API çağrısında uygulama kullanıcısı server-side olarak oluşturulur.

## API-Football ve ücretsiz fixture sync

[API-Sports](https://www.api-football.com/) hesabından API anahtarını alın. `FOOTBALL_API_KEY` ve `TARGET_TEAM_ID` değerlerini tanımlayın. Ücretsiz Vercel Hobby planı günde tek cron çağrısı ile sınırlı olduğundan, zamanlama için ücretsiz Upstash QStash kullanılır. Adminler `POST /api/admin/sync-fixtures` ile elle sync başlatabilir.

Sync API'nin takım fikstür listesini normalize eder, `api_fixture_id` ile idempotent upsert mantığı uygular ve `manual_override` işaretli maçları ezmez. Başarısız API isteği mevcut verileri silmez.

### QStash kurulumu (günlük 90 çağrı)

1. Uygulamayı önce Vercel'e deploy edin ve üretim adresinizi alın: `https://PROJE.vercel.app`.
2. [Upstash Console](https://console.upstash.com/) üzerinden ücretsiz bir QStash hesabı oluşturun.
3. **QStash → Schedules → Create Schedule** bölümünde aşağıdaki dört schedule'ı oluşturun. Her birinde Destination URL: `https://PROJE.vercel.app/api/cron/sync-fixtures`, Method: `GET`, Retry: `0` olmalıdır.
4. Her schedule'a `Authorization` header'ını `Bearer <CRON_SECRET>` olarak ekleyin. `<CRON_SECRET>`, Vercel Environment Variables'daki `CRON_SECRET` değeriyle aynı olmalıdır.

| Cron (UTC) | Günlük çağrı |
| --- | ---: |
| `0,15,30,45 0-5 * * *` | 24 |
| `0,15,30,45 6-11 * * *` | 24 |
| `0,15,30,45 12-17 * * *` | 24 |
| `0,20,40 18-23 * * *` | 18 |

Toplam 90 çağrıdır. QStash Free günlük 1.000 mesaj destekler; retry değeri `0` olmalıdır, aksi hâlde tekrarlar API-Football kotasından harcar.

## Deployment

```bash
npm run build
npm test
npx vercel --prod
```

Vercel dashboard'da yukarıdaki tüm environment değerlerini Production ve Preview için girin. Deployment öncesi `npm run db:migrate` çalıştırın. Vercel build komutu `npm run build`, output directory `dist` olmalıdır.

## Puanlama

Tam skor 5 puandır. Sonuç doğruysa 2 puan, gol farkı da doğruysa 1 ek puan verilir; tam skora bonus eklenmez. Beraberlikte doğru ama farklı skor 3 puandır. Uygulama sonucu tahminlerden hesaplar; puanları ayrı bir cache tablosuna yazmaz. “İyimser/kötümser” istatistiği eklendiğinde Galatasaray için tahmin edilen ve gerçek gol farkı arasındaki ortalama sapma esas alınmalıdır.

## Kontroller

`npm test` puanlama ve kilit kurallarını kapsar. `npm run build` strict TypeScript kontrolü ve Vite üretim derlemesini çalıştırır.
