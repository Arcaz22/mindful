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

Dataset awal berasal dari file [data.csv](/C:/Users/Lenovo/project/mindful/data.csv), lalu dimasukkan ke database melalui script ingest.

## Prasyarat

Pastikan tersedia:

- Python `3.12`
- `uv`
- Docker Desktop
- Ollama lokal

Model default pada client saat ini adalah `gpt-oss:20b`, dan embedding model yang dipakai adalah `all-MiniLM-L6-v2`.

## Environment Variable

Buat file `.env` di root project. Minimal isi yang dibutuhkan:

```env
APP_ENV=local
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mindful_db
MAX_FREE_CHAT_LIMIT=3
ALLOWED_MODELS=["gpt-oss:20b"]
SUPER_USERS=["admin"]
```

Catatan:

- `DATABASE_URL` harus sesuai dengan database yang dijalankan lewat Docker.
- `MAX_FREE_CHAT_LIMIT` saat ini ada di konfigurasi, tetapi implementasi use case masih memakai batas `3` secara langsung.

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

Setelah database siap, masukkan data awal dari `data.csv`:

```powershell
uv run python scripts/ingest.py
```

Script ini akan:

- membersihkan data lama di tabel `knowledge_base`
- membaca setiap baris dari `data.csv`
- membuat embedding
- menyimpan hasilnya ke database

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
- Frontend `Streamlit` saat ini adalah UI tipis untuk menguji backend, belum memuat autentikasi atau manajemen sesi yang kompleks.
