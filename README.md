# Aplikasi Grafika Komputer

Aplikasi ini adalah editor grafika 2D berbasis desktop untuk mata kuliah Grafika Komputer. Aplikasi dibuat dengan Python, Tkinter, dan CustomTkinter. Fitur utamanya adalah menggambar objek primitif, mengatur atribut objek, memilih banyak objek, melakukan transformasi 2D, membuat salinan refleksi, memberi warna area perpotongan, menjalankan animasi, serta menyimpan dan membuka kanvas dalam format JSON.

Entry point aplikasi tetap sederhana:

```bash
python app.py
```

## Fitur Utama

- Menggambar objek primitif: garis, persegi, persegi panjang, lingkaran, elips, segitiga, dan poligon bebas.
- Mengatur atribut objek: warna isi, warna garis, ketebalan garis, dan tipe garis.
- Seleksi objek tunggal maupun banyak objek.
- Memindahkan objek dengan drag.
- Rubber-band selection untuk memilih objek dengan area kotak.
- Mengubah urutan layer: bring to front dan send to back.
- Transformasi 2D: translasi, rotasi, skala, skew, dan refleksi.
- Refleksi objek terhadap sumbu X, sumbu Y, garis `y = x`, garis `y = -x`, dan garis kustom `y = mx + b`.
- Preview garis cermin untuk refleksi.
- Membuat salinan objek hasil pencerminan.
- Mewarnai area perpotongan objek terpilih.
- Animasi objek: rotasi, translasi kanan-kiri, skala pulse, dan skew kiri-kanan.
- Undo dan redo.
- Simpan dan buka kanvas sebagai JSON.

## Kebutuhan

Aplikasi ini membutuhkan:

- Python 3.10 atau lebih baru.
- Tkinter, biasanya sudah ikut terpasang bersama Python desktop.
- CustomTkinter.

Install dependency utama:

```bash
pip install customtkinter
```

Jika Tkinter tidak tersedia, install Python dari installer resmi yang menyertakan Tcl/Tk, atau aktifkan paket Tkinter sesuai sistem operasi yang dipakai.

## Cara Menjalankan

Dari folder proyek:

```bash
python app.py
```

Saat aplikasi terbuka:

1. Pilih bentuk objek di panel kiri.
2. Klik dan drag di kanvas untuk menggambar.
3. Ubah warna, outline, ketebalan, atau tipe garis dari panel kiri.
4. Pilih objek dengan mode `Pilih Objek`.
5. Gunakan panel kanan untuk transformasi, animasi, dan daftar objek.

## Struktur Folder

Struktur proyek saat ini:

```text
TA_GRAFIKA/
  app.py
  README.md
  .gitignore
  grafika/
    constants.py
    models.py
    renderer.py
    transforms.py
    controllers/
      animation.py
      drawing.py
      geometry.py
      selection.py
      state.py
      transform.py
    ui/
      components.py
```

Penjelasan singkat:

- `app.py` adalah entry point dan shell utama aplikasi.
- `grafika/constants.py` menyimpan konfigurasi global seperti warna, ukuran kanvas, daftar bentuk, daftar transformasi, dan tipe garis.
- `grafika/models.py` berisi model data `GrafisObjek`.
- `grafika/renderer.py` bertanggung jawab menggambar objek ke `tk.Canvas`.
- `grafika/transforms.py` berisi operasi matriks transformasi 2D.
- `grafika/ui/components.py` berisi komponen UI reusable seperti panel kiri, panel kanan, tombol, label, input, combo box, dan color swatch.
- `grafika/controllers/drawing.py` menangani event menggambar dan drag objek.
- `grafika/controllers/selection.py` menangani seleksi objek dan sinkronisasi listbox.
- `grafika/controllers/transform.py` menangani panel parameter transformasi dan penerapan transformasi.
- `grafika/controllers/geometry.py` menangani operasi geometri tambahan seperti area perpotongan.
- `grafika/controllers/animation.py` menangani animasi objek.
- `grafika/controllers/state.py` menangani undo, redo, delete, layer order, warna, save JSON, dan load JSON.

## Gambaran Arsitektur

Kelas utama aplikasi adalah `GrafikaApp` di `app.py`. Kelas ini tidak menampung semua fitur secara langsung, tetapi menggabungkan beberapa mixin controller:

```python
class GrafikaApp(
    TransformControllerMixin,
    DrawingControllerMixin,
    SelectionControllerMixin,
    GeometryControllerMixin,
    AnimationControllerMixin,
    StateCommandMixin,
):
    ...
```

Pola ini dipakai agar `app.py` tetap menjadi pusat aplikasi, tetapi detail fiturnya tersebar rapi berdasarkan tanggung jawabnya.

Alur sederhananya:

1. `app.py` membuat window, panel, canvas, renderer, status bar, menu, dan shortcut.
2. `ui/components.py` membuat panel kiri dan panel kanan.
3. User berinteraksi dengan kanvas atau panel.
4. Event masuk ke controller yang sesuai.
5. Controller mengubah data `GrafisObjek`.
6. `Renderer` menggambar ulang objek di canvas.
7. Jika aksi mengubah objek, state lama disimpan ke history untuk undo/redo.

## Model Data Objek

Semua objek gambar direpresentasikan oleh class `GrafisObjek` di `grafika/models.py`.

Field penting:

- `id`: nomor unik objek.
- `shape`: nama bentuk, misalnya `Garis`, `Lingkaran`, atau `Poligon Bebas`.
- `points`: daftar titik objek dalam koordinat canvas.
- `fill`: warna isi.
- `outline`: warna garis.
- `line_width`: ketebalan garis.
- `line_dash`: pola garis.
- `canvas_ids`: id item canvas yang sedang mewakili objek.
- `name`: nama tampilan di daftar objek.

Objek juga punya method:

- `clone()` untuk membuat salinan state objek saat undo/redo.
- `center()` untuk menghitung titik pusat objek.
- `to_dict()` untuk menyimpan objek ke JSON.
- `from_dict()` untuk membaca objek dari JSON.

## Rendering

Rendering dilakukan oleh `Renderer` di `grafika/renderer.py`.

Tugas renderer:

- Menggambar objek ke `tk.Canvas`.
- Mengubah rectangle dan oval menjadi polygon agar transformasi lebih konsisten.
- Menghapus dan membuat ulang canvas item saat objek berubah.
- Menyinkronkan koordinat canvas saat objek dipindahkan.
- Menampilkan highlight seleksi.
- Menampilkan grid dan sumbu.
- Menampilkan garis cermin saat mode refleksi.
- Mengatur layer visual dengan bring front dan send back.

Catatan penting: `GrafisObjek.points` adalah sumber data utama. `canvas_ids` hanya representasi visual di canvas.

## Transformasi 2D

Transformasi matematis ada di `grafika/transforms.py`.

Modul ini menggunakan matriks homogen 3x3 untuk:

- translasi
- rotasi
- skala
- skew
- refleksi

Fungsi utama:

- `translate_matrix(tx, ty)`
- `rotate_matrix(deg, cx, cy)`
- `scale_matrix(sx, sy, cx, cy)`
- `skew_matrix(shx, shy, cx, cy)`
- `reflect_matrix(axis, m, b, canvas_w, canvas_h)`
- `apply_matrix(points, matrix)`

Controller transformasi membaca parameter dari UI, membuat matriks yang sesuai, lalu menerapkannya ke `obj.points`.

## Controller

### `drawing.py`

Menangani interaksi langsung dengan canvas:

- klik mouse
- drag mouse
- release mouse
- double click untuk menutup poligon bebas
- preview saat menggambar
- drag objek terpilih
- rubber-band selection
- update koordinat kursor

### `selection.py`

Menangani pilihan objek:

- single select
- multi select
- pilih semua
- batal pilih
- sinkronisasi pilihan dari canvas ke listbox
- sinkronisasi pilihan dari listbox ke canvas
- refresh daftar objek

### `transform.py`

Menangani transformasi objek:

- membangun panel parameter transformasi dinamis
- membaca input parameter
- menerapkan transformasi ke objek terpilih
- menampilkan preview garis refleksi
- membuat salinan objek hasil pencerminan

### `geometry.py`

Menangani fitur geometri tambahan:

- menghitung luas polygon
- mencari titik potong garis
- clipping polygon
- mencari area perpotongan objek terpilih
- membuat objek baru dari area perpotongan yang diberi warna

### `animation.py`

Menangani animasi:

- mulai animasi
- berhenti animasi
- loop animasi
- mengembalikan snapshot objek setelah animasi berhenti

Animasi diterapkan ke objek terpilih dengan transformasi kecil berulang.

### `state.py`

Menangani state aplikasi dan command umum:

- undo
- redo
- delete selected
- clear all
- new canvas
- bring front
- send back
- pilih warna
- save JSON
- load JSON

History disimpan sebagai daftar clone objek. Saat undo/redo, snapshot lama direstore lalu objek dirender ulang.

## Komponen UI

Komponen UI ada di `grafika/ui/components.py`.

Isi utamanya:

- Helper widget seperti `section_label`, `dim_label`, `hint_label`, `make_btn`, `make_entry`, dan `make_combo`.
- `LeftPanel` untuk alat gambar, warna, atribut garis, aksi cepat, dan petunjuk.
- `RightPanel` untuk transformasi, animasi, layer order, dan daftar objek.
- `ColorSwatch` untuk preview dan pemilihan warna.
- Helper parameter transformasi seperti `build_param` dan `build_radio_center`.

Panel menerima instance `GrafikaApp` sebagai `app`, lalu menghubungkan tombol dan input ke method controller di aplikasi utama.

## Shortcut

Shortcut yang tersedia:

| Shortcut | Fungsi |
| --- | --- |
| `Ctrl+N` | Kanvas baru |
| `Ctrl+S` | Simpan JSON |
| `Ctrl+O` | Buka JSON |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+A` | Pilih semua objek |
| `Delete` | Hapus objek terpilih |
| `Escape` | Batalkan seleksi |
| `Page Up` | Bring to front |
| `Page Down` | Send to back |
| `Ctrl+Klik` | Tambah atau hapus objek dari multi-select |
| `Double Click` | Tutup poligon bebas |

## Format File JSON

Saat kanvas disimpan, aplikasi menulis daftar objek ke file JSON.

Contoh struktur satu objek:

```json
{
  "id": 1,
  "shape": "Persegi Panjang",
  "points": [[100, 100], [200, 100], [200, 180], [100, 180]],
  "fill": "#60a5fa",
  "outline": "#1e40af",
  "line_width": 2,
  "line_dash": [],
  "name": "Persegi Panjang #1"
}
```

File JSON hanya menyimpan data objek, bukan state UI seperti tab aktif, status bar, atau objek yang sedang dipilih.

## Cara Menambah Bentuk Baru

Untuk menambah bentuk baru, biasanya perlu mengubah beberapa tempat:

1. Tambahkan nama bentuk di `SHAPES` pada `grafika/constants.py`.
2. Tambahkan preview bentuk di `_draw_preview()` pada `grafika/controllers/drawing.py`.
3. Tambahkan pembuatan titik final di `_build_points()` pada `grafika/controllers/drawing.py`.
4. Pastikan `Renderer.render()` di `grafika/renderer.py` tahu cara menggambar bentuk tersebut.

Jika bentuk dapat direpresentasikan sebagai polygon, usahakan simpan sebagai list titik. Ini membuat transformasi lebih mudah dan konsisten.

## Cara Menambah Transformasi Baru

Untuk menambah transformasi baru:

1. Tambahkan nama transformasi di `TRANSFORMS` pada `grafika/constants.py`.
2. Tambahkan input parameter di `_update_transform_panel()` pada `grafika/controllers/transform.py`.
3. Tambahkan fungsi matriks baru di `grafika/transforms.py` jika perlu.
4. Tambahkan cabang penerapan transformasi di `_apply_transform()` pada `grafika/controllers/transform.py`.

Prinsipnya: UI hanya mengumpulkan parameter, sedangkan operasi matematis tetap berada di `transforms.py`.

## Cara Menambah Animasi Baru

Untuk menambah animasi:

1. Tambahkan nama animasi di `ANIM_TYPES` pada `grafika/constants.py`.
2. Tambahkan cabang baru di `_anim_loop()` pada `grafika/controllers/animation.py`.
3. Gunakan fungsi transformasi yang sudah ada jika memungkinkan.

Animasi sebaiknya bersifat sementara dan dapat berhenti dengan mengembalikan snapshot awal.

## Cara Menambah Tombol atau Kontrol UI

Jika ingin menambah kontrol di panel:

- Panel kiri ada di `LeftPanel` pada `grafika/ui/components.py`.
- Panel kanan ada di `RightPanel` pada `grafika/ui/components.py`.
- Gunakan helper `make_btn`, `make_entry`, dan `make_combo` agar gaya UI tetap konsisten.
- Aksi tombol sebaiknya memanggil method di controller, bukan menaruh logika besar langsung di UI.

## Catatan Tentang `__pycache__`

Python akan membuat folder `__pycache__` secara otomatis saat aplikasi dijalankan atau file dikompilasi. Folder ini hanya cache bytecode, bukan source code.

Folder dan file cache sudah diabaikan lewat `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
```

Jika `__pycache__` muncul lagi di folder lokal, itu normal dan aman dihapus.

## Catatan Tentang `__init__.py`

Folder `grafika`, `grafika/controllers`, dan `grafika/ui` tidak memakai `__init__.py`. Pada Python modern, struktur seperti ini tetap bisa dipakai sebagai namespace package selama aplikasi dijalankan dari root proyek.

Jika suatu saat proyek ingin dipaketkan untuk distribusi, misalnya dengan `pip install -e .`, menambahkan kembali `__init__.py` bisa dipertimbangkan.

## Tips Debugging

- Jika objek tidak muncul, cek apakah `Renderer.render()` dipanggil dan `obj.points` valid.
- Jika transformasi salah, cek matriks di `grafika/transforms.py` dan parameter pusat transformasi.
- Jika undo/redo tidak bekerja, pastikan aksi yang mengubah objek memanggil `_save_history()` sebelum perubahan.
- Jika list objek tidak sinkron, cek `_refresh_listbox()` dan `_sync_listbox_selection()`.
- Jika warna atau atribut tidak berubah, cek target seleksi: `selected_set` atau `selected`.
- Jika aplikasi gagal start karena `customtkinter`, jalankan `pip install customtkinter`.

## Validasi Kode

Untuk mengecek sintaks semua file Python:

```bash
python -m py_compile app.py grafika/constants.py grafika/models.py grafika/renderer.py grafika/transforms.py grafika/controllers/animation.py grafika/controllers/drawing.py grafika/controllers/geometry.py grafika/controllers/selection.py grafika/controllers/state.py grafika/controllers/transform.py grafika/ui/components.py
```

Pada Windows PowerShell, bisa juga memakai:

```powershell
$files = Get-ChildItem -Recurse -Filter *.py | ForEach-Object { $_.FullName }
python -m py_compile $files
```

## Ringkasan Untuk Developer Baru

Jika baru membuka proyek ini, mulai dari urutan berikut:

1. Buka `app.py` untuk memahami struktur window dan bagaimana controller digabungkan.
2. Buka `grafika/models.py` untuk memahami bentuk data objek.
3. Buka `grafika/renderer.py` untuk memahami cara objek digambar.
4. Buka controller sesuai fitur yang ingin diubah.
5. Buka `grafika/ui/components.py` jika ingin mengubah layout panel.
6. Buka `grafika/transforms.py` jika ingin mengubah matematika transformasi.

Dengan struktur ini, perubahan fitur bisa dilakukan di file yang sesuai tanpa membuat `app.py` kembali terlalu panjang.
