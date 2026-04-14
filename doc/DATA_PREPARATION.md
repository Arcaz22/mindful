# Panduan Persiapan Data

Dokumen ini fokus pada apa yang perlu dilakukan untuk menyiapkan data baru untuk sistem `RAG`.

## Tujuan

Membangun knowledge base yang:

- lebih valid
- lebih lengkap
- lebih mudah ditelusuri sumbernya
- lebih aman dipakai untuk menghasilkan jawaban

## Prinsip Utama

Dalam project `RAG`, kualitas jawaban sangat dipengaruhi oleh kualitas data.

Artinya:

- data lemah menghasilkan jawaban lemah
- data salah bisa menghasilkan jawaban menyesatkan
- data tanpa sumber sulit diaudit

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

## Format Data yang Disarankan

Gunakan format seperti CSV dengan kolom berikut:

```csv
id,category,title,content,source_name,source_url,language,tags,last_updated
1,psychology,Harga Diri Rendah,"Isi pengetahuan...",Kemenkes,https://contoh.id,id,"emosi;harga-diri",2026-04-14
```

Arti kolom:

- `id`: ID unik
- `category`: kategori utama
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

## Checklist Sebelum Ingest

Pastikan hal-hal ini sudah benar:

- encoding file konsisten
- tidak ada baris duplikat besar
- sumber tercatat
- kolom wajib terisi
- isi teks sudah dibersihkan
- format CSV valid

## Evaluasi Awal Dataset

Sebelum data di-ingest penuh, uji beberapa sampel:

- apakah kontennya benar
- apakah bahasanya layak
- apakah sumbernya jelas
- apakah satu chunk cukup fokus
- apakah metadata konsisten

## Hubungan dengan Sistem Saat Ini

Dataset baru ini nantinya akan dipakai untuk:

1. dibaca oleh script ingest
2. dibuat embedding
3. disimpan ke database
4. dicari kembali saat user bertanya
5. dijadikan konteks untuk LLM

## Prioritas Kerja Anda

Jika ingin bergerak efisien, urutannya:

1. pilih domain
2. kumpulkan sumber
3. salin ke format CSV terstruktur
4. bersihkan isi data
5. cek metadata
6. baru ingest ke sistem

## Keputusan Penting

Yang paling penting untuk ditentukan dari awal:

- domain apa yang dipilih
- seberapa sensitif domainnya
- sumber mana yang dianggap valid
- siapa target pengguna aplikasi

Jawaban atas keputusan ini akan memengaruhi bentuk dataset dan guardrail.
