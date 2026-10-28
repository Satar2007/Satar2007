# SATAR Profile V2 — setup & maintenance

Paket ini ditujukan hanya untuk repository profil publik `Satar2007/Satar2007`, branch `main`.

## Yang terpasang

| Bagian | Sumber | Update |
| --- | --- | --- |
| Header SATAR | SVG lokal, teks berganti dan kubus melayang | Selalu beranimasi di viewer yang mendukung CSS SVG |
| GitHub metrics | lowlighter/metrics: overview, languages, public activity | Harian, sekitar 07.57 WIB |
| Isometric calendar | lowlighter/metrics, full-year | Bersama Metrics |
| Skyline berputar | Generator Python sendiri, kalender kontribusi GitHub | Harian, sekitar 07.37 WIB |
| Pac-Man light/dark | abozanona/pacman-contribution-graph | Harian, sekitar 07.17 WIB |

GitHub dapat menunda jadwal Actions. Ketiganya juga bisa dijalankan dari tab Actions → pilih workflow → Run workflow. Animasi merupakan SVG/GIF yang dirender, bukan objek interaktif yang bisa diputar dengan mouse di README.

Skyline awal dalam paket berasal dari kalender publik Satar2007 yang diambil pada 30 September 2026: 28 September 2025–30 September 2026, 56 kontribusi. Setelah workflow berjalan, kalender diperbarui dari GitHub GraphQL. Rentang rolling dari API bisa sedikit berbeda dari rentang minggu penuh pada halaman GitHub. Satu blok mewakili satu hari; tinggi menggunakan akar kuadrat jumlah kontribusi supaya hari yang sangat aktif tidak menutupi semua blok. Hari tanpa kontribusi ditampilkan sebagai ubin rendah.

Metrics, kalender isometrik, dan Pac-Man memakai kartu status awal sampai workflow berhasil, bukan angka atau aktivitas contoh. Jangan menganggap kartu status sebagai hasil render akhir.

## 1. Tambahkan METRICS_TOKEN

Dokumentasi lowlighter/metrics meminta personal token untuk membaca data profil; token repository bawaan tidak mencakup semua kueri Metrics.

1. Masuk sebagai **Satar2007**. Buka https://github.com/settings/tokens/new.
2. Pilih **Generate new token (classic)** bila diminta. Isi note `Satar profile metrics` dan expiration sesuai kebutuhan, misalnya 90 hari.
3. Untuk plugin publik yang dipakai paket ini, **biarkan semua scope tidak dicentang**. Tidak perlu memberi akses `repo` atau `workflow` kepada token Metrics.
4. Generate token, lalu salin sekali.
5. Buka https://github.com/Satar2007/Satar2007/settings/secrets/actions.
6. Pilih **New repository secret**, Name: `METRICS_TOKEN`, Secret: token tersebut, lalu simpan.

Token baca ini hanya dipakai untuk mengambil data. Commit gambar memakai `GITHUB_TOKEN` dengan izin `contents: write` dari workflow. Jangan menaruh token di README, file, perintah yang masuk history, atau chat. Saat token kedaluwarsa, ganti nilai secret yang sama dan jalankan ulang Metrics.

## 2. Pasang melalui PowerShell

Extract ZIP. Jalankan installer yang berada di sebelah folder `repo`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\Install-Profile.ps1' -Publish
```

Perintah tersebut berlaku setelah PowerShell berada di folder hasil extract. Parameter ExecutionPolicy hanya berlaku untuk proses itu.

Secara default installer menggunakan `C:\Users\<nama-user>\Projects\Satar2007`. Jika folder belum ada, repository profil akan di-clone. Untuk menggunakan clone profil yang sudah ada:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\Install-Profile.ps1' -RepoDir 'C:\lokasi\Satar2007' -Publish
```

Installer memverifikasi origin, branch `main`, working tree bersih, dan tidak ada commit lokal yang belum dipush. File yang akan diganti dicadangkan ke `%USERPROFILE%\Profile-Backups\Satar2007-<timestamp>`. File repository lain tetap dipertahankan. Gambar hasil workflow yang sudah ada tidak ditimpa kartu awal pada pemasangan ulang.

`-Publish` melakukan stage **hanya file paket**, commit, dan push ke `main`. Jika login GitHub muncul saat push, selesaikan melalui Git Credential Manager. Tanpa `-Publish`, installer hanya memasang file lokal. Untuk mempublikasikan instalasi lokal tersebut, periksa `git diff`, lalu stage file paket, commit, dan push secara manual; installer menolak working tree kotor agar tidak menimpa perubahan pengguna.

Installer tidak masuk ke folder JIMNY COFFEE maupun repository portofolio web. Tidak membuat repository baru dan tidak mengubah visibility repository. Profil ini sudah terverifikasi tersedia secara publik pada saat paket dibuat.

## 3. Cek setelah push

1. Buka https://github.com/Satar2007/Satar2007/actions.
2. Tunggu `Profile - Pac-Man`, `Profile - Metrics`, dan `Profile - Rotating Skyline` selesai.
3. Jika diminta GitHub, aktifkan Actions untuk repository ini. Jika suatu workflow tidak terpicu karena tidak ada perubahan file, jalankan manual.
4. Buka https://github.com/Satar2007 dan refresh. Proxy gambar GitHub kadang memerlukan waktu untuk memperbarui cache.

Ketiga workflow menulis ke `assets/generated` di branch `main`. Tidak memerlukan branch `output`, GitHub Pages, server, Laragon, atau Python di laptop. Python/Pillow hanya dipasang pada runner GitHub untuk skyline.

Workflow dipisahkan agar kegagalan Metrics tidak menghalangi Pac-Man atau skyline. Commit aset memakai pesan `[skip ci]`, pemicu dibatasi file generator/workflow, dan proses push me-rebase commit aset terhadap perubahan branch terbaru tanpa force-push.

## Troubleshooting

| Gejala | Langkah |
| --- | --- |
| `Add repository Actions secret METRICS_TOKEN` | Tambahkan secret lalu jalankan ulang Metrics |
| `Bad credentials`, API 401 | Periksa token kedaluwarsa atau salah salin, lalu ganti secret |
| API 403 | Periksa izin Actions, pembatasan akun/organisasi, dan rate limit pada log |
| `Resource not accessible by integration` pada skyline | Tambahkan `METRICS_TOKEN` agar generator memakai personal token |
| Push workflow ditolak | Periksa Settings → Actions → General → Workflow permissions dan branch rules; workflow meminta `contents: write` |
| Push installer ditolak karena workflow scope | Gunakan login Git Credential Manager/GitHub CLI dengan izin mengubah workflow; ini berbeda dari token baca Metrics |
| Gambar masih menampilkan kartu status | Buka log workflow terkait; kartu diganti hanya setelah generation berhasil |
| Branch dilindungi | Ikuti proses PR repository; jangan menonaktifkan proteksi secara sembarang |
| Dirty working tree | Simpan atau commit perubahan profil yang ada, lalu ulang installer |
| Push installer gagal setelah commit | Masuk ke folder profil, lihat `git status`, lalu ulang `git push origin main` setelah masalah autentikasi selesai |
| Pac-Man sedikit titik atau skyline rendah | Banyak hari memang belum memiliki kontribusi; gambar mengikuti data GitHub |

## Pemeliharaan

- README: ubah `README.md`.
- Header: ubah `assets/header.svg`.
- Jadwal: field `schedule` pada `.github/workflows/*.yml` menggunakan UTC.
- Dependensi: action pihak ketiga dirujuk dengan commit SHA yang diverifikasi 30 September 2026. Perbarui setelah membaca perubahan upstream; Docker image Metrics masih ditentukan upstream.
- Pillow dipatok pada 11.3.0 untuk render yang dapat direproduksi.
- Jika GitHub menonaktifkan scheduled workflows setelah repository lama tidak aktif, aktifkan kembali melalui tab Actions.
- Rollback perubahan pemasangan: `git log --oneline`, temukan commit `feat: add animated SATAR profile, metrics and 3D contributions`, lalu `git revert <SHA>` dan `git push origin main`. Jika muncul konflik karena aset diperbarui bot, selesaikan konflik sebelum melanjutkan; backup file asli juga tersedia di folder backup.

## Validasi paket

Paket diperiksa untuk struktur YAML, nama input dibandingkan dengan action upstream yang dirujuk, sintaks Python dan shell, integritas SVG/GIF, serta render skyline dari kalender publik. Alur push aset diuji menggunakan repository Git lokal. GitHub Actions produksi dan installer Windows tetap harus dijalankan di akun/laptop pengguna; paket belum dipush dari sesi pembuatannya.

## Referensi

- https://github.com/abozanona/pacman-contribution-graph
- https://github.com/lowlighter/metrics
- https://github.com/lowlighter/metrics/blob/master/.github/readme/partials/documentation/setup/action.md
- https://github.com/lowlighter/metrics/blob/master/source/plugins/isocalendar/README.md
- https://github.com/lowlighter/metrics/blob/master/source/plugins/languages/README.md
- https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme

Generator skyline pada paket ini adalah implementasi sendiri. Ia tidak menggunakan plugin `plugin_skyline` atau mengklaim sebagai produk resmi GitHub Skyline.
