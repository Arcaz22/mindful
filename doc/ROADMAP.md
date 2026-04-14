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
- domain masih bertema psikologi umum
- guardrail belum kuat
- evaluasi hasil retrieval dan jawaban belum ada

## Tujuan Tahap Dekat

Target terdekat yang masuk akal:

1. Menentukan domain project secara tegas
2. Mengganti atau memperkaya sumber data
3. Menyesuaikan format dataset agar lebih rapi
4. Memperbaiki pipeline ingest
5. Menguji kualitas retrieval dan jawaban
6. Menyempurnakan UI `Streamlit`

## Langkah Kerja yang Disarankan

### 1. Tentukan Domain

Pilih salah satu lebih dulu:

- psikologi / wellbeing
- informasi medis umum
- informasi obat

Catatan:

- Jika memilih domain medis, tingkat risiko lebih tinggi.
- Domain medis membutuhkan sumber yang lebih ketat dan guardrail yang lebih kuat.

### 2. Cari Sumber Data Baru

Fokus utama project ini adalah kualitas knowledge base.

Yang perlu dilakukan:

- mencari sumber yang valid
- menghindari sumber anonim atau forum
- memastikan data relevan dengan domain
- mencatat asal sumber

Contoh target sumber:

- panduan resmi
- artikel edukasi dari institusi terpercaya
- FAQ resmi
- dokumen informasi pasien

### 3. Rapikan Format Dataset

Dataset saat ini masih sederhana. Format baru sebaiknya memiliki metadata.

Kolom minimum yang disarankan:

- `id`
- `category`
- `title`
- `content`
- `source_name`
- `source_url`
- `tags`
- `last_updated`

Tujuan metadata:

- memudahkan filtering
- memudahkan pelacakan sumber
- memudahkan sitasi
- memudahkan audit data

### 4. Sesuaikan Pipeline Ingest

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

### 5. Evaluasi Hasil Retrieval

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

### 6. Tambahkan Guardrail

Guardrail adalah pembatas agar sistem tidak memberi jawaban yang berbahaya atau menyesatkan.

Minimal yang perlu dilakukan:

- deteksi pertanyaan di luar domain
- deteksi permintaan diagnosis pasti
- deteksi gejala darurat
- paksa sistem mengaku tidak tahu jika konteks tidak cukup

Jika nanti domain menjadi medis, guardrail wajib diperketat.

### 7. Rapikan Streamlit

Setelah data dan retrieval lebih stabil:

- perjelas branding aplikasi
- tampilkan sumber jawaban
- tampilkan peringatan jika konteks lemah
- tambahkan status koneksi backend
- tambahkan disclaimer bila domain sensitif

### 8. Putuskan Perlu LangChain atau Tidak

Untuk tahap sekarang, `LangChain` belum wajib.

Gunakan `LangChain` hanya jika:

- workflow mulai bercabang banyak
- ada banyak sumber data dengan perlakuan berbeda
- ada routing berdasarkan jenis pertanyaan
- ada agent atau tools tambahan

Jika alur masih sederhana, kode Python biasa lebih mudah dirawat.

## Urutan Pengerjaan yang Direkomendasikan

Urutan kerja yang paling efisien:

1. Tetapkan domain
2. Cari sumber data
3. Buat format dataset baru
4. Ubah script ingest
5. Ingest data
6. Uji retrieval
7. Tambahkan guardrail
8. Rapikan UI
9. Evaluasi apakah butuh framework tambahan

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

- dataset baru yang valid
- script ingest versi baru
- knowledge base yang lebih kaya
- daftar pertanyaan evaluasi
- guardrail minimum
- Streamlit yang lebih informatif

