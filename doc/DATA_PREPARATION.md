# Panduan Persiapan Data

Dokumen ini fokus pada apa yang perlu dilakukan untuk menyiapkan data baru untuk sistem `RAG`.

## Tujuan

Membangun knowledge base yang:

- lebih valid
- lebih lengkap
- lebih mudah ditelusuri sumbernya
- lebih aman dipakai untuk menghasilkan jawaban
- spesifik untuk topik `anxiety`

## Prinsip Utama

Dalam project `RAG`, kualitas jawaban sangat dipengaruhi oleh kualitas data.

Artinya:

- data lemah menghasilkan jawaban lemah
- data salah bisa menghasilkan jawaban menyesatkan
- data tanpa sumber sulit diaudit

Untuk project ini, kualitas data lebih penting daripada menambah banyak fitur baru.

## Domain yang Dipakai

Domain yang dipakai untuk tahap ini adalah:

- `anxiety education`

Batas domain:

- fokus pada informasi edukasi tentang kecemasan
- boleh memuat gejala umum, faktor risiko, self-help umum, treatment umum, dan kapan mencari bantuan
- tidak diposisikan untuk diagnosis pasti
- tidak diposisikan untuk rekomendasi obat yang spesifik

## Sumber yang Sudah Dipilih

Tiga sumber awal yang dipakai:

- `Mayo Clinic`
- `WHO`
- `NHS Every Mind Matters`

URL sumber:

- `https://www.mayoclinic.org/diseases-conditions/anxiety/symptoms-causes/syc-20350961`
- `https://www.who.int/news-room/fact-sheets/detail/anxiety-disorders`
- `https://www.nhs.uk/every-mind-matters/mental-health-issues/anxiety/`

## Sumber Data yang Disarankan

Cari data dari sumber yang:

- resmi
- kredibel
- terbaru
- sesuai domain
- bisa dipakai secara legal

Contoh bentuk sumber:

- halaman edukasi institusi
- guideline
- FAQ resmi
- artikel penjelasan pasien
- dokumen obat atau penyakit

## Sumber yang Sebaiknya Dihindari

Hindari sumber seperti:

- forum anonim
- blog tanpa otoritas jelas
- artikel clickbait
- data yang tidak jelas asalnya
- konten lama yang sudah usang

## Proses Persiapan Data yang Harus Dilalui

Urutan kerja yang disarankan:

1. pilih topik
2. cari sumber kredibel
3. buka halaman web
4. ambil isi penting
5. clean text
6. normalisasi metadata
7. chunking
8. deduplikasi
9. masukkan ke CSV
10. validasi
11. ingest ke database

Untuk project ini, langkah `masukkan ke CSV` bisa dibantu oleh Ollama, tetapi hanya setelah teks sumber sudah diekstrak dan dibersihkan lebih dulu.

## Cara Mengambil Isi dari Halaman Web

Jangan menyalin seluruh halaman mentah.

Ambil bagian yang memang relevan untuk knowledge base, misalnya:

- definisi anxiety
- gejala umum
- penyebab atau faktor risiko
- langkah self-help
- treatment umum
- kapan harus mencari bantuan

Jangan ambil:

- menu navigasi
- footer
- banner
- ajakan berlangganan atau CTA
- daftar link yang tidak menjelaskan isi utama

## Peran Ollama dalam Persiapan Data

Ollama tidak dipakai sebagai sumber pengetahuan utama.

Peran yang aman:

- merangkum section sumber menjadi chunk singkat
- membantu memberi judul chunk
- membantu memberi tags
- membantu mengubah section mentah menjadi row CSV yang lebih rapi

Peran yang tidak disarankan:

- membuat isi knowledge base langsung dari URL tanpa ekstraksi sumber
- menambahkan fakta dari luar teks yang sedang diproses
- menggantikan validasi manual

Workflow yang dipakai di repo ini:

1. simpan hasil ekstraksi halaman ke `data/raw_sources/*.md`
2. jalankan `scripts/prepare_dataset.py`
3. review hasil `data/anxiety_knowledge.csv`
4. baru ingest ke database

## Langkah Eksekusi Praktis

Berikut urutan kerja yang bisa langsung dijalankan dari root project.

### 1. Siapkan file sumber mentah

Pastikan file berikut tersedia:

- `data/raw_sources/who_anxiety.md`
- `data/raw_sources/mayo_anxiety.md`
- `data/raw_sources/nhs_anxiety.md`

Format tiap file:

```text
source_name: WHO
source_url: https://www.who.int/news-room/fact-sheets/detail/anxiety-disorders
language: en
last_updated: 2025-09-08
category: psychology
topic: anxiety
---
## Overview
Isi section...
```

Checkpoint:

- metadata lengkap
- ada pemisah `---`
- isi dipisah per `## Section`

### 2. Pastikan environment siap

Minimal cek file `.env` sudah berisi:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mindful_db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
DATA_PREP_MODEL=llama3.1:8b
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_VECTOR_SIZE=384
KNOWLEDGE_CSV_PATH=data/anxiety_knowledge.csv
RAW_SOURCE_DIR=data/raw_sources
```

### 3. Jalankan database

```bash
docker compose up -d
```

Opsional cek status:

```bash
docker compose ps
```

### 4. Jalankan migrasi database

```bash
uv run alembic upgrade head
```

Checkpoint:

- tabel `knowledge_base` dan `user_usage` sudah ada
- kolom vector masih cocok dengan `EMBEDDING_VECTOR_SIZE`

### 5. Pastikan Ollama aktif

Jika Ollama berjalan lokal, cek dengan:

```bash
curl http://localhost:11434/api/tags
```

Jika backend ada di WSL dan Ollama di Windows, gunakan IP host Windows sesuai penjelasan di `README`.

### 6. Buat CSV dari raw sources dengan Ollama

Jalankan:

```bash
uv run python scripts/prepare_dataset.py
```

Script ini akan:

- membaca `data/raw_sources/*.md`
- memecah isi per section
- mengirim section ke Ollama
- menulis hasil ke `data/anxiety_knowledge.csv`

Checkpoint:

- file `data/anxiety_knowledge.csv` terbuat
- setiap row punya `title`, `content`, dan `tags`
- tidak ada row kosong

### 7. Review hasil CSV

Periksa file hasil:

```bash
sed -n '1,40p' data/anxiety_knowledge.csv
```

Yang perlu dicek:

- `title` jelas
- `content` tidak mengarang
- `tags` konsisten
- `source_url` benar
- topik tetap `anxiety`

### 8. Ingest ke database

Setelah CSV lolos review, jalankan:

```bash
uv run python scripts/ingest.py
```

Script ini akan:

- menghapus isi lama `knowledge_base`
- membaca `data/anxiety_knowledge.csv`
- memvalidasi kolom
- membuat embedding
- menyimpan content dan metadata ke database

Checkpoint:

- proses selesai tanpa error
- jumlah row yang diproses sesuai ekspektasi

### 9. Jalankan backend

```bash
uv run fastapi dev main.py
```

### 10. Uji retrieval dan jawaban

Anda bisa uji lewat frontend atau langsung ke API:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "guest-user",
    "message": "Apa gejala umum anxiety?",
    "visitor_id": "browser-123"
  }'
```

Pertanyaan uji yang disarankan:

- `Apa itu anxiety?`
- `Apa gejala umum anxiety?`
- `Kapan saya perlu mencari bantuan profesional?`
- `Apa langkah self-help yang aman untuk anxiety?`

### 11. Evaluasi hasil

Jika hasil retrieval belum bagus:

- rapikan lagi `data/raw_sources/*.md`
- jalankan ulang `uv run python scripts/prepare_dataset.py`
- review CSV lagi
- ingest ulang

Jika retrieval sudah bagus tetapi jawaban masih lemah:

- evaluasi prompt chat
- evaluasi model chat di Ollama

Jika retrieval lemah untuk pertanyaan Indonesia:

- evaluasi model embedding multilingual

## Aturan Clean Text

Setelah isi penting diambil, bersihkan teks dengan aturan berikut:

- hapus spasi berlebih
- hilangkan karakter aneh hasil copy atau scrape
- gabungkan kalimat yang terpotong tidak wajar
- buang kalimat promosi
- pertahankan arti asli sumber
- jangan menerjemahkan manual jika belum ada aturan yang konsisten

Tujuan clean text:

- teks lebih mudah di-embed
- retrieval lebih stabil
- isi chunk lebih mudah dipahami model

## Aturan Chunking

Chunking harus dilakukan berdasarkan subtopik, bukan berdasarkan panjang halaman saja.

Contoh chunk yang baik untuk topik `anxiety`:

- `What is anxiety`
- `Symptoms of anxiety`
- `Possible causes and risk factors`
- `Self-help techniques`
- `When to seek professional help`
- `Treatment overview`

Aturan praktis:

- satu chunk membahas satu ide utama
- satu chunk tetap bisa dipahami tanpa membaca chunk lain
- hindari chunk yang sangat pendek
- hindari chunk yang terlalu panjang dan berisi banyak ide campur

Contoh buruk:

- satu chunk berisi definisi, gejala, treatment, hotline, dan disclaimer sekaligus

## Normalisasi Metadata

Sebelum masuk CSV, metadata perlu dibuat konsisten.

Field yang perlu dinormalisasi:

- `category`
- `topic`
- `title`
- `source_name`
- `source_url`
- `language`
- `tags`
- `last_updated`

Contoh aturan:

- `category` tetap `psychology`
- `topic` tetap `anxiety`
- `tags` dipisahkan dengan `;`
- `language` gunakan kode seperti `en` atau `id`
- `last_updated` gunakan format `YYYY-MM-DD`

## Format Data yang Disarankan

Gunakan format seperti CSV dengan kolom berikut:

```csv
id,category,topic,title,content,source_name,source_url,language,tags,last_updated
1,psychology,anxiety,Symptoms of Anxiety,"Common symptoms include...",WHO,https://www.who.int/news-room/fact-sheets/detail/anxiety-disorders,en,"anxiety;symptoms",2025-08-13
```

Arti kolom:

- `id`: ID unik
- `category`: kategori utama
- `topic`: topik sempit agar retrieval lebih terarah
- `title`: judul topik
- `content`: isi pengetahuan utama
- `source_name`: nama sumber
- `source_url`: link sumber
- `language`: bahasa
- `tags`: kata kunci
- `last_updated`: tanggal sumber atau ingest

## Aturan Menulis Content

Isi kolom `content` sebaiknya:

- fokus pada satu topik
- jelas dan bersih
- tidak terlalu pendek
- tidak terlalu panjang
- tidak mencampur terlalu banyak ide berbeda

Contoh yang baik:

- satu chunk khusus tentang gejala
- satu chunk khusus tentang penanganan awal
- satu chunk khusus tentang kapan harus ke dokter

Contoh yang kurang baik:

- satu baris sangat panjang yang mencampur definisi, gejala, obat, komplikasi, dan disclaimer sekaligus

## Strategi Chunking

Jika sumber berupa dokumen panjang:

- pecah menjadi beberapa bagian
- setiap bagian harus masih punya makna yang utuh
- hindari chunk terlalu pendek
- hindari chunk terlalu besar

Tujuan chunking:

- retrieval lebih akurat
- konteks lebih relevan
- prompt ke LLM lebih efisien

## Deduplikasi

Sebelum ingest, cek apakah ada baris yang terlalu mirip atau identik.

Yang perlu dihindari:

- dua chunk dari sumber berbeda tetapi isinya hampir sama persis
- satu chunk yang terduplikasi karena proses copy
- judul berbeda tetapi konten sama

Jika ada duplikasi:

- simpan versi yang paling jelas
- prioritaskan sumber yang lebih otoritatif
- pertahankan metadata sumber jika memang perlu audit manual

## Metadata yang Penting

Selain `content`, metadata sangat berguna.

Metadata yang direkomendasikan:

- sumber
- kategori
- tanggal
- tags
- tingkat prioritas

Untuk domain sensitif seperti medis, Anda bisa tambah:

- `severity`
- `requires_disclaimer`
- `audience`

Untuk topik `anxiety`, tambahan metadata opsional yang berguna:

- `content_type` seperti `definition`, `symptoms`, `self_help`, `treatment`
- `requires_guardrail` untuk topik yang menyentuh risiko tinggi
- `audience` seperti `general_public`

## Checklist Sebelum Ingest

Pastikan hal-hal ini sudah benar:

- encoding file konsisten
- tidak ada baris duplikat besar
- sumber tercatat
- kolom wajib terisi
- isi teks sudah dibersihkan
- format CSV valid
- `topic` konsisten bernilai `anxiety`
- `source_url` dapat dilacak
- isi tiap chunk masih sesuai domain
- tidak ada klaim diagnosis pasti di dalam konten yang Anda tulis ulang

## Evaluasi Awal Dataset

Sebelum data di-ingest penuh, uji beberapa sampel:

- apakah kontennya benar
- apakah bahasanya layak
- apakah sumbernya jelas
- apakah satu chunk cukup fokus
- apakah metadata konsisten

Contoh pertanyaan evaluasi awal:

- "Apa itu anxiety?"
- "Apa saja gejala anxiety?"
- "Apa langkah self-help sederhana untuk anxiety?"
- "Kapan seseorang perlu mencari bantuan profesional?"

## Hubungan dengan Sistem Saat Ini

Dataset baru ini nantinya akan dipakai untuk:

1. dibaca oleh script ingest
2. dibuat embedding
3. disimpan ke database
4. dicari kembali saat user bertanya
5. dijadikan konteks untuk LLM

## Prioritas Kerja Anda

Jika ingin bergerak efisien, urutannya:

1. ambil isi penting dari 3 sumber utama
2. bersihkan teks
3. pecah menjadi chunk
4. isi metadata secara konsisten
5. masukkan ke CSV terstruktur
6. validasi isi CSV
7. sesuaikan ingest
8. baru ingest ke sistem

## Keputusan Penting

Yang paling penting untuk ditentukan dari awal:

- topik sempit apa yang dipakai
- seberapa sensitif domainnya
- sumber mana yang dianggap valid
- bahasa utama pengguna
- model embedding apa yang akan dipakai

Jawaban atas keputusan ini akan memengaruhi bentuk dataset dan guardrail.
