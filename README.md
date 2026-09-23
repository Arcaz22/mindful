# Mindful

Mindful adalah aplikasi chatbot informasi kesehatan dan digital wellbeing.

Project ini membantu pengguna memahami pertanyaan kesehatan secara umum dengan memadukan:

- FastAPI sebagai backend;
- Ollama sebagai model AI lokal;
- Tavily untuk mencari sumber web tepercaya;
- PostgreSQL untuk menyimpan penggunaan dan audit sumber;
- Streamlit sebagai frontend sederhana.

Jawaban Mindful berbasis sumber, bukan diagnosis medis. Aplikasi tidak meresepkan obat, memberikan dosis personal, atau menggantikan dokter, apoteker, IGD, maupun layanan darurat.

Mindful juga memiliki guardrail untuk krisis, self-harm, overdosis, kondisi darurat, alergi berat, kehamilan, anak/bayi, interaksi obat, serta penyakit ginjal atau hati.

Alur penggunaan dan arsitektur runtime dijelaskan di [doc/CHAT_FLOW.md](/home/w11c/project/portofolio/mindful/doc/CHAT_FLOW.md). Rencana migrasi teknis tersedia di [doc/langchain-migration-plan.md](/home/w11c/project/portofolio/mindful/doc/langchain-migration-plan.md).
