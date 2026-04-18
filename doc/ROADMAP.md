# Roadmap Pengembangan Project

Dokumen ini menjelaskan apa saja yang perlu dilakukan untuk mengembangkan project `mindful` dari versi saat ini ke versi yang lebih layak dipakai.

## Kondisi Saat Ini

Project saat ini sudah memiliki:

- backend `FastAPI`
- database `PostgreSQL + pgvector`
- pipeline `RAG` sederhana
- script ingest dari `data.csv`
- frontend `Streamlit`

Kondisi yang masih perlu diperbaiki:

- knowledge base masih terbatas
- kualitas sumber data belum meyakinkan
- domain perlu dipersempit agar retrieval lebih akurat
- guardrail belum kuat
- evaluasi hasil retrieval dan jawaban belum ada

## Tujuan Tahap Dekat

Target terdekat yang masuk akal:

1. Menetapkan domain project menjadi `anxiety education`
2. Mengganti `data.csv` lama dengan dataset yang bersumber jelas
3. Menyusun format dataset baru yang lebih rapi dan dapat diaudit
4. Memperbaiki pipeline ingest agar sesuai format baru
5. Menguji kualitas retrieval dan jawaban
6. Menambahkan guardrail minimum untuk topik sensitif
7. Menyempurnakan UI `Streamlit`

## Langkah Kerja yang Disarankan

### 1. Tetapkan Domain Secara Tegas

Untuk tahap ini, domain project ditetapkan menjadi:

- `anxiety education`

Catatan:

- Domain ini masih sensitif, tetapi lebih sempit dan lebih mudah dijaga daripada `wellbeing` umum.
- Jawaban sistem harus berfokus pada edukasi dasar, self-help umum, dan arahan mencari bantuan profesional.
- Sistem tidak boleh diposisikan sebagai alat diagnosis.

### 2. Tetapkan Sumber Data Utama

Fokus utama project ini adalah kualitas knowledge base.

Sumber awal yang sudah dipilih:

- `Mayo Clinic`: penjelasan gejala, penyebab, dan gambaran umum gangguan kecemasan
- `WHO`: fact sheet resmi untuk overview, treatment, dan konteks kesehatan masyarakat
- `NHS Every Mind Matters`: panduan praktis, self-help, dan kapan mencari bantuan

URL yang digunakan:

- `https://www.mayoclinic.org/diseases-conditions/anxiety/symptoms-causes/syc-20350961`
- `https://www.who.int/news-room/fact-sheets/detail/anxiety-disorders`
- `https://www.nhs.uk/every-mind-matters/mental-health-issues/anxiety/`

Yang perlu dilakukan pada tahap ini:

- memastikan setiap halaman memang membahas `anxiety`
- mencatat `source_name`, `source_url`, dan tanggal pembaruan jika tersedia
- menghindari mengambil teks navigasi, footer, promosi, atau CTA yang tidak relevan
- memeriksa apakah konten legal dipakai sebagai bahan ekstraksi pengetahuan internal

### 3. Ekstraksi Isi Penting dari Halaman Web

Setelah halaman dipilih, buka dan petakan struktur isinya.

Bagian yang layak diambil biasanya:

- definisi atau overview
- gejala
- penyebab atau faktor risiko
- kapan harus mencari bantuan
- self-help atau coping strategies
- treatment options

Bagian yang sebaiknya tidak ikut:

- header dan menu
- link promosi
- ajakan membuat akun atau layanan tambahan
- daftar tautan yang tidak menambah pengetahuan inti

### 4. Bersihkan dan Normalisasi Teks

Sebelum masuk ke dataset:

- hapus spasi berlebih
- hilangkan kalimat duplikat
- buang artefak scraping
- pertahankan bahasa asli sumber
- pastikan satu potongan teks tetap jelas dibaca tanpa konteks halaman penuh

### 5. Lakukan Chunking per Subtopik

Jangan simpan satu halaman penuh sebagai satu baris.

Chunk yang disarankan:

- satu chunk untuk `what is anxiety`
- satu chunk untuk `symptoms`
- satu chunk untuk `causes`
- satu chunk untuk `self-help`
- satu chunk untuk `when to seek help`
- satu chunk untuk `treatment`

Tujuan chunking:

- retrieval lebih presisi
- konteks ke LLM lebih fokus
- sumber lebih mudah dilacak

### 6. Rapikan Format Dataset

Dataset saat ini masih sederhana. Format baru sebaiknya memiliki metadata.

Kolom minimum yang disarankan:

- `id`
- `category`
- `topic`
- `title`
- `content`
- `source_name`
- `source_url`
- `language`
- `tags`
- `last_updated`

Tujuan metadata:

- memudahkan filtering
- memudahkan pelacakan sumber
- memudahkan sitasi
- memudahkan audit data

Contoh struktur:

```csv
id,category,topic,title,content,source_name,source_url,language,tags,last_updated
1,psychology,anxiety,Symptoms of Anxiety,"Common symptoms may include...",WHO,https://www.who.int/news-room/fact-sheets/detail/anxiety-disorders,en,"anxiety;symptoms",2025-08-13
```

### 7. Validasi Dataset Sebelum Ingest

Sebelum dataset dipakai:

- cek semua kolom wajib terisi
- cek tidak ada duplikasi besar
- cek tiap chunk fokus pada satu ide
- cek `source_url` benar
- cek teks tidak terlalu pendek atau terlalu panjang
- cek encoding CSV konsisten

### 8. Sesuaikan Pipeline Ingest

Setelah dataset baru siap:

- ubah script ingest agar membaca format baru
- tambahkan penyimpanan metadata
- pastikan chunking masuk akal
- simpan embedding ke `knowledge_base`

Hal yang perlu ditinjau:

- ukuran chunk
- duplikasi data
- kebersihan teks
- strategi commit batch
- penyimpanan `source_name` atau metadata tambahan
- kecocokan dimensi embedding dengan kolom vector database

### 9. Ganti Model Embedding Jika Diperlukan

Karena target pengguna kemungkinan memakai bahasa Indonesia, embedding multilingual layak dipertimbangkan.

Yang harus dicek:

- apakah model baru lebih cocok untuk teks Indonesia dan Inggris
- berapa dimensi vector model tersebut
- apakah dimensi itu sama dengan skema database saat ini

Jika dimensi embedding berubah:

- ubah model database
- buat migrasi Alembic
- kosongkan data lama
- lakukan ingest ulang penuh

### 10. Evaluasi Hasil Retrieval

Sebelum memperbaiki LLM, cek dulu apakah retrieval sudah benar.

Yang perlu diuji:

- apakah pertanyaan menemukan konteks yang relevan
- apakah `context_ids` sesuai
- apakah chunk yang diambil memang membantu menjawab
- apakah ada topik penting yang tidak terjangkau

Contoh evaluasi sederhana:

- buat 10 sampai 20 pertanyaan uji
- catat dokumen mana yang diambil
- cek apakah hasilnya relevan

Contoh pertanyaan uji:

- "Apa gejala umum anxiety?"
- "Kapan saya harus mencari bantuan profesional?"
- "Apa perbedaan anxiety biasa dan anxiety disorder?"
- "Apa langkah self-help yang aman?"

### 11. Tambahkan Guardrail

Guardrail adalah pembatas agar sistem tidak memberi jawaban yang berbahaya atau menyesatkan.

Minimal yang perlu dilakukan:

- deteksi pertanyaan di luar domain `anxiety education`
- deteksi permintaan diagnosis pasti
- deteksi gejala darurat atau krisis
- paksa sistem mengaku tidak tahu jika konteks tidak cukup
- arahkan user ke bantuan profesional jika pertanyaan menyangkut keselamatan
- tampilkan sumber jawaban bila tersedia

Contoh kasus guardrail:

- user minta diagnosis gangguan tertentu
- user menyebut ingin menyakiti diri sendiri
- user meminta saran pengobatan spesifik yang tidak ada di knowledge base
- user bertanya topik di luar domain seperti obat, penyakit fisik, atau hukum

### 12. Rapikan Prompt dan Jawaban Model

Setelah retrieval dan guardrail dasar stabil:

- perjelas bahwa model hanya boleh menjawab dari konteks
- minta model menyebut keterbatasan bila konteks lemah
- pastikan model tidak terdengar seperti tenaga medis yang memberi kepastian klinis

### 13. Rapikan Streamlit

Setelah data dan retrieval lebih stabil:

- perjelas branding aplikasi
- tampilkan sumber jawaban
- tampilkan peringatan jika konteks lemah
- tambahkan status koneksi backend
- tambahkan disclaimer bila domain sensitif

### 14. Putuskan Perlu LangChain atau Tidak

Untuk tahap sekarang, `LangChain` belum wajib.

Gunakan `LangChain` hanya jika:

- workflow mulai bercabang banyak
- ada banyak sumber data dengan perlakuan berbeda
- ada routing berdasarkan jenis pertanyaan
- ada agent atau tools tambahan

Jika alur masih sederhana, kode Python biasa lebih mudah dirawat.

## Urutan Pengerjaan yang Direkomendasikan

Urutan kerja yang paling efisien:

1. Tetapkan domain `anxiety`
2. Kunci daftar sumber utama
3. Ekstrak isi penting dari halaman web
4. Bersihkan teks
5. Lakukan chunking
6. Masukkan ke CSV terstruktur
7. Validasi dataset
8. Sesuaikan script ingest
9. Putuskan model embedding
10. Jika perlu, migrasikan vector database
11. Ingest ke database
12. Uji retrieval
13. Tambahkan guardrail
14. Rapikan UI
15. Evaluasi apakah butuh framework tambahan

## Langkah Operasional

Urutan eksekusi yang disarankan di terminal:

1. Jalankan database

```bash
docker compose up -d
```

2. Jalankan migrasi

```bash
uv run alembic upgrade head
```

3. Pastikan Ollama aktif

```bash
curl http://localhost:11434/api/tags
```

4. Siapkan atau edit file sumber mentah di `data/raw_sources/*.md`

5. Generate dataset CSV

```bash
uv run python scripts/prepare_dataset.py
```

6. Review hasil `data/anxiety_knowledge.csv`

7. Ingest ke database

```bash
uv run python scripts/ingest.py
```

8. Jalankan backend

```bash
uv run fastapi dev main.py
```

9. Jalankan frontend

```bash
uv run streamlit run streamlit_app.py
```

10. Uji pertanyaan `anxiety` dan evaluasi retrieval

## Yang Belum Perlu Diprioritaskan

Hal yang belum perlu dikerjakan sekarang:

- migrasi ke `LangChain`
- agent yang kompleks
- fitur multi-user yang rumit
- deployment production
- optimasi UI yang berlebihan

Masalah inti project ini saat ini adalah kualitas pengetahuan, bukan framework.

## Deliverable yang Sebaiknya Dibuat

Hasil kerja yang ideal untuk tahap berikutnya:

- dataset `anxiety` baru yang valid
- CSV terstruktur dengan metadata sumber
- script ingest versi baru
- knowledge base yang lebih fokus
- daftar pertanyaan evaluasi
- guardrail minimum
- Streamlit yang lebih informatif
