Bot Python telegram modular yang berjalan di python3 dengan database sqlalchemy.

Awalnya bot manajemen grup sederhana dengan beberapa fitur admin, dan telah berkembang, menjadi sangat modular dan
mudah digunakan. Perhatikan bahwa proyek ini menggunakan bot Telegram terkenal pada masanya @BanhammerMarie_bot dari Paul Larson sebagai basisnya.

Dapat ditemukan di telegram sebagai [FerbotInd] (https://t.me/FerBotInd_bot).
Laporkan bug ke [👤] (https://t.me/Fernans1)

## Kredit

Skyleebot Untuk Bot Luar Biasa, Dan Basis Ini Di Dalamnya

Skittbot untuk modul Stiker dan modul meme.

1maverick1 untuk banyak hal.

AyraHikari untuk modul cuaca dan beberapa barang lainnya.

RealAkito untuk modul pencarian terbalik.

MrYacha untuk modul koneksi

ATechnoHazard untuk banyak barang

Corsicanu dan Nunopenim untuk modul android

UserIndoBot untuk kode sumber

Kredit lain yang hilang dapat dilihat di komit!

## Memulai bot

Setelah Anda mengatur database Anda dan konfigurasi Anda (lihat di bawah) selesai, jalankan saja:

`python3 -m ferbot`

## Menyiapkan bot Baca ini sebelum mencoba menggunakan

Harap pastikan untuk menggunakan python3.6 di atas, karena saya tidak dapat menjamin semuanya akan berfungsi seperti yang diharapkan pada versi Python yang lebih lama!
Ini karena penguraian penurunan harga dilakukan dengan iterasi melalui dict, yang diurutkan secara default di 3.6.

### Konfigurasi

Ada dua cara yang mungkin untuk mengonfigurasi bot Anda: file config.py, atau variabel ENV.

Versi yang disukai adalah menggunakan file `config.py`, karena ini lebih memudahkan untuk melihat semua pengaturan Anda secara bersamaan.
File ini harus ditempatkan di folder `UserindoBot` Anda, di samping file` __main __. Py`.
Di sinilah token bot Anda akan dimuat, serta URI database Anda (jika Anda menggunakan database), dan sebagian besar
pengaturan Anda yang lain.

Direkomendasikan untuk mengimpor sample_config dan memperluas kelas Config, karena ini akan memastikan konfigurasi Anda berisi semuanya
default diatur di sample_config, sehingga membuatnya lebih mudah untuk ditingkatkan.

Contoh file `config.env` bisa jadi:

`` python
    API_KEY = "" # Token bot Anda dari BotFather
    OWNER_ID = "1234567" # Jika Anda tidak tahu, jalankan bot dan lakukan / id dalam obrolan pribadi Anda dengannya
    OWNER_USERNAME = "ferbot" # nama pengguna telegram Anda
    SQLALCHEMY_DATABASE_URI = "sqldbtype: // username: pw @ hostname: port / db_name"
    MONGO_DB_URI = "mongodb + srv: // nama pengguna: pwd@host.port.mongodb.net/db_name"
    MESSAGE_DUMP = "-100987654" # diperlukan untuk memastikan pesan 'simpan dari' tetap ada
    LOAD = "" # daftar modul yang dimuat (pisahkan dengan spasi)
    NO_LOAD = "afk android" # daftar modul yang dibongkar (pisahkan dengan spasi)
    STRICT_GBAN = Benar
``

### Dependensi Python

Instal dependensi Python yang diperlukan dengan berpindah ke direktori proyek dan menjalankan:

`pip3 install -r requirement.txt`.

Ini akan menginstal semua paket python yang diperlukan.

### Database

#### MongoDB

[MongoDB] (https://cloud.mongodb.com/) di sini digunakan untuk menyimpan pengguna, obrolan, status afk, daftar hitam, larangan global, data.

#### SQL

Jika Anda ingin menggunakan modul yang bergantung pada database (misalnya: kunci, catatan, filter, selamat datang),
Anda harus memiliki database yang terpasang di sistem Anda. Saya menggunakan Postgres, jadi saya sarankan menggunakannya untuk kompatibilitas optimal.

Dalam kasus Postgres, inilah cara Anda mengatur database pada sistem Debian / Ubuntu. Distribusi lain mungkin berbeda.

- instal PostgreSQL:

`sudo apt-get update && sudo apt-get install postgresql`

- ubah ke pengguna Postgres:

`sudo su - postgres`

- buat pengguna database baru (ubah YOUR_USER dengan benar):

`createuser -P -s -e YOUR_USER`

Ini akan diikuti oleh Anda perlu memasukkan kata sandi Anda.

- buat tabel database baru:

`Createdb -O YOUR_USER YOUR_DB_NAME`

Ubah YOUR_USER dan YOUR_DB_NAME dengan benar.

- akhirnya:

`psql YOUR_DB_NAME -h YOUR_HOST YOUR_USER`

Ini akan memungkinkan Anda untuk terhubung ke database Anda melalui terminal Anda.
Secara default, YOUR_HOST harus 0.0.0.0:5432.

Anda sekarang harus dapat membangun URI database Anda. Ini akan menjadi:

`sqldbtype: // username: pw @ hostname: port / db_name`

Ganti SqlDbType dengan DB mana pun yang Anda gunakan (mis. Postgres, MySQL, SQLite, dll)
ulangi untuk nama pengguna, kata sandi, nama host (localhost?), port (5432?), dan nama DB Anda.

## Modul

### Menyetel urutan pemuatan

Urutan pemuatan modul dapat diubah melalui pengaturan konfigurasi `LOAD` dan` NO_LOAD`.
Keduanya harus mewakili daftar.

Jika `LOAD` adalah daftar kosong, semua modul dalam` modules / `akan dipilih untuk dimuat secara default.

Jika `NO_LOAD` tidak ada atau merupakan daftar kosong, semua modul yang dipilih untuk dimuat akan dimuat.

Jika modul ada di `LOAD` dan` NO_LOAD`, modul tidak akan dimuat - `NO_LOAD` diprioritaskan.

### Membuat modul Anda sendiri

Membuat modul telah disederhanakan semaksimal mungkin - tetapi jangan ragu untuk menyarankan penyederhanaan lebih lanjut.

Yang diperlukan hanyalah file .py Anda ada di folder modul.

Untuk menambahkan perintah, pastikan untuk mengimpor petugas operator melalui

`from dispatcher import ferbot`.

Anda kemudian dapat menambahkan perintah menggunakan biasa

`dispatcher.add_handler ()`.

Menetapkan variabel `__help__` ke string yang menjelaskan ketersediaan modul ini
perintah akan memungkinkan bot memuatnya dan menambahkan dokumentasinya
modul Anda ke perintah `/help`. Menyetel variabel `__mod_name__` juga akan memungkinkan Anda menggunakan variabel yang lebih bagus,
nama yang mudah digunakan untuk modul.

Fungsi `__migrate __ ()` digunakan untuk memigrasi obrolan - saat obrolan ditingkatkan ke supergrup, ID berubah, jadi
perlu untuk memigrasikannya di DB.

Fungsi `__stats __ ()` adalah untuk mengambil statistik modul, misalnya jumlah pengguna, jumlah obrolan. Ini diakses
melalui perintah `/stats`, yang hanya tersedia untuk pemilik bot.
