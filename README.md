# Mindful

Backend chatbot berbasis `FastAPI` dengan pola `RAG` sederhana, ditambah frontend `Streamlit` untuk pengujian antarmuka.

Project ini menerima pertanyaan pengguna, mengubahnya menjadi embedding, mencari konteks paling relevan di database `PostgreSQL + pgvector`, lalu meminta model LLM lokal untuk menyusun jawaban berdasarkan konteks tersebut.

## Ringkasan Fitur

- Endpoint `GET /health` untuk health check
- Endpoint `POST /chat` untuk tanya jawab
- Penyimpanan knowledge base pada PostgreSQL
- Similarity search menggunakan `pgvector`
- Embedding menggunakan `sentence-transformers`
- Generasi jawaban melalui LLM lokal via `Ollama`
- Frontend `Streamlit` untuk mencoba chat tanpa membuat frontend web terpisah
- Batas chat gratis per user

## Arsitektur Singkat

Alur request backend:

1. User mengirim pertanyaan ke endpoint `/chat`.
2. Backend membuat embedding dari pertanyaan user.
3. Backend mencari dokumen atau potongan pengetahuan terdekat di tabel `knowledge_base`.
4. Konteks hasil retrieval dikirim ke LLM lokal.
5. Backend mengembalikan jawaban, nama model, sisa kuota chat, dan `context_ids`.

Komponen utama:

- [main.py](/C:/Users/Lenovo/project/mindful/main.py): entry point FastAPI
- [app/interfaces/http/routers.py](/C:/Users/Lenovo/project/mindful/app/interfaces/http/routers.py): route API
- [app/application/usecases/chat_use_case.py](/C:/Users/Lenovo/project/mindful/app/application/usecases/chat_use_case.py): logika utama chat
- [app/application/usecases/ingest_use_case.py](/C:/Users/Lenovo/project/mindful/app/application/usecases/ingest_use_case.py): logika ingest data
- [app/infrastructure/llm/client.py](/C:/Users/Lenovo/project/mindful/app/infrastructure/llm/client.py): client ke Ollama dan embedding model
- [app/infrastructure/db/models.py](/C:/Users/Lenovo/project/mindful/app/infrastructure/db/models.py): model database
- [scripts/ingest.py](/C:/Users/Lenovo/project/mindful/scripts/ingest.py): script ingest `data.csv`
- [streamlit_app.py](/C:/Users/Lenovo/project/mindful/streamlit_app.py): frontend Streamlit

## Struktur Data

Tabel utama:

- `knowledge_base`: menyimpan konten teks, embedding, dan metadata
- `user_usage`: menyimpan identitas user, jumlah chat, whitelist, dan fingerprint

Dataset lama masih tersedia di [data.csv](/home/w11c/project/portofolio/mindful/data.csv), tetapi pipeline ingest default sekarang memakai dataset terstruktur [data/anxiety_knowledge.csv](/home/w11c/project/portofolio/mindful/data/anxiety_knowledge.csv:1). Dataset ini dapat disusun ulang dari file sumber mentah di [data/raw_sources](/home/w11c/project/portofolio/mindful/data/raw_sources) menggunakan Ollama.

## Prasyarat

Pastikan tersedia:

- Python `3.12`
- `uv`
- Docker Desktop
- Ollama lokal

Model default pada client saat ini adalah `llama3.1:8b`, dan embedding model default yang dipakai adalah `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

## Environment Variable

Buat file `.env` di root project. Minimal isi yang dibutuhkan:

```env
APP_ENV=local
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mindful_db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_VECTOR_SIZE=384
KNOWLEDGE_CSV_PATH=data/anxiety_knowledge.csv
RAW_SOURCE_DIR=data/raw_sources
MAX_FREE_CHAT_LIMIT=3
RETRIEVAL_TOP_K=3
ALLOWED_MODELS=llama3.1:8b
SUPER_USERS=["admin"]
```

Catatan:

- `DATABASE_URL` harus sesuai dengan database yang dijalankan lewat Docker.
- `OLLAMA_BASE_URL` adalah alamat server Ollama yang dipanggil backend.
- `EMBEDDING_MODEL_NAME` adalah model `sentence-transformers` yang dipakai untuk retrieval.
- `EMBEDDING_VECTOR_SIZE` harus cocok dengan dimensi kolom vector di database.
- `KNOWLEDGE_CSV_PATH` adalah file CSV terstruktur yang dipakai script ingest.
- `RAW_SOURCE_DIR` adalah folder file sumber mentah hasil ekstraksi halaman web.
- `MAX_FREE_CHAT_LIMIT` dipakai untuk membatasi kuota chat gratis per user.
- `RETRIEVAL_TOP_K` mengatur jumlah chunk knowledge base yang diambil saat retrieval.
- `RETRIEVAL_MAX_DISTANCE` opsional untuk memfilter hasil retrieval yang terlalu jauh; kosongkan untuk menonaktifkan threshold.

### Jika Backend di WSL dan Ollama di Windows

Jika backend berjalan di WSL tetapi Ollama berjalan di Windows, jangan gunakan `http://localhost:11434` kecuali forwarding `localhost` di mesin Anda memang aktif.

Langkah yang aman:

1. Pastikan Ollama di Windows berjalan dan port `11434` terbuka.
2. Di WSL, cari IP host Windows:

```bash
cat /etc/resolv.conf
```

Biasanya nilai `nameserver` adalah IP Windows host, misalnya `10.x.x.x`.

3. Uji koneksi dari WSL:

```bash
curl http://IP_WINDOWS:11434/api/tags
```

4. Jika berhasil, set `.env` backend menjadi:

```env
OLLAMA_BASE_URL=http://IP_WINDOWS:11434
```

5. Restart backend FastAPI.

Jika `curl` gagal, biasanya penyebabnya salah satu dari berikut:

- Ollama belum berjalan di Windows
- firewall Windows masih memblokir port `11434`
- Ollama hanya bind ke `127.0.0.1` dan belum bisa diakses dari WSL

## Menjalankan Database

Jalankan PostgreSQL dengan `pgvector`:

```powershell
docker compose up -d
```

Untuk memastikan container aktif:

```powershell
docker compose ps
```

## Menjalankan Migrasi

Jika database baru pertama kali digunakan, jalankan migrasi:

```powershell
uv run alembic upgrade head
```

## Ingest Dataset

Setelah database siap, buat atau perbarui dataset CSV terstruktur dari sumber mentah:

```powershell
uv run python scripts/prepare_dataset.py
```

Script ini akan:

- membaca file `.md` di `RAW_SOURCE_DIR`
- memecah isi per section
- meminta Ollama merangkum tiap section menjadi chunk terstruktur
- menulis hasil akhir ke `KNOWLEDGE_CSV_PATH`

Setelah itu, masukkan data awal ke database:

```powershell
uv run python scripts/ingest.py
```

Script ini akan:

- membersihkan data lama di tabel `knowledge_base`
- membaca setiap baris dari file pada `KNOWLEDGE_CSV_PATH`
- memvalidasi kolom dataset dan menghindari duplikasi sederhana
- membuat embedding
- menyimpan hasilnya ke database beserta metadata sumber

## Menjalankan Backend FastAPI

Jalankan server API:

```powershell
uv run fastapi dev main.py
```

Secara default backend akan berjalan di:

```text
http://localhost:8000
```

Endpoint yang tersedia:

- `GET /health`
- `POST /chat`

Contoh body request ke `/chat`:

```json
{
  "user_id": "guest-user",
  "message": "Saya merasa cemas terus menerus, apa yang bisa saya lakukan?",
  "visitor_id": "browser-123"
}
```

## Menjalankan Frontend Streamlit

Setelah backend aktif, jalankan frontend:

```powershell
uv run streamlit run streamlit_app.py
```

Secara default Streamlit akan terbuka di:

```text
http://localhost:8501
```

Di sidebar Streamlit, Anda bisa mengatur:

- `Backend URL`
- `User ID`
- `Visitor ID`

Frontend ini akan mengirim request ke endpoint `/chat` milik backend.

## Urutan Menjalankan Project

Urutan paling aman:

1. Jalankan Docker database.
2. Jalankan migrasi Alembic.
3. Pastikan Ollama aktif.
4. Jalankan ingest data.
5. Jalankan backend FastAPI.
6. Jalankan frontend Streamlit.

## Catatan Pengembangan

- `README` ini menjelaskan implementasi saat ini, yang masih berfokus pada domain psikologi/digital wellbeing.
- Jika domain diubah ke medis, sumber data dan guardrail perlu diperketat karena risikonya lebih tinggi.
- Guardrail dasar untuk self-harm/krisis sudah ada, tetapi masih berbasis rule sederhana dan belum setara moderation pipeline penuh.
- Frontend `Streamlit` saat ini adalah UI tipis untuk menguji backend, belum memuat autentikasi atau manajemen sesi yang kompleks.
