# IF3170_G27_AyamTerbang
Tugas Besar 1 IF3170 Artificial Intelligence

## Jalankan aplikasi

```sh
docker compose up --build
```

Buka http://localhost:8080 di browser.

## Setelah mengubah kode Python

```sh
docker compose restart app
```

Refresh browser untuk melihat perubahan.

Jika menambah library, masukkan ke `requirements.txt`,
lalu jalankan kembali `docker compose up --build`.

## Lihat log atau error

```sh
docker compose logs -f app
```

## Jalankan file Python lain

```sh
docker compose run --rm app python src/nama_file.py
```

Ganti `nama_file.py` dengan nama file yang ingin dijalankan.

## Hentikan aplikasi

```sh
docker compose down
```

Hasil disimpan di folder `output/` 