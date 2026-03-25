# Admin Data Storage
Direktori ini digunakan untuk menyimpan data administratif yang akan diproses ke dalam Knowledge Base MCP.

## Struktur Direktori:
- `/korespondensi/`: Tempat menyimpan file spreadsheet (.xlsx) atau dokumen (.pdf/.docx) terkait surat-menyurat.
- `/struktur_organisasi/`: Tempat menyimpan data organisasi Ditjen Bina Bangda.
- `/templates/`: Tempat menyimpan template spreadsheet untuk standarisasi data.

## Cara Ingest ke Knowledge Base:
Setiap file yang diletakkan di sini bisa dimasukkan ke memori bot dengan perintah:
`knowledge_ingest_spreadsheet(file_path="/home/aseps/MCP/storage/admin_data/...")`
