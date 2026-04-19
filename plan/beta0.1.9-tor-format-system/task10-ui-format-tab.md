# Task 10: UI — Tab Format TOR

## 1. Judul Task
Pembuatan Komponen Tab Manajemen Format di Streamlit

## 2. Deskripsi
Membangun elemen antarmuka halaman view and editing Format TOR berstruktur state session variable pada platform Streamlit yang berinteraksi memanggil REST framework yang sudah dibangun.

## 3. Tujuan Teknis
Mendesain file modular ui di `streamlit_app/components/format_tab.py` dan menempelkannya ke navigasi streamlist module utama. UI mengandalkan komponen container form widget, lists text display, options selector control format, add remove layout, dsb.

## 4. Scope
* **Yang dikerjakan**: Menulis class/fungsi rendering View Mode, Edit Mode, Active Selector mode Streamlit UI. Injeksi halaman via entry point `app.py`.
* **Yang tidak dikerjakan**: Logic API backend. Logic Extraction Preview Flow.

## 5. Langkah Implementasi
1. Buat file `streamlit_app/components/format_tab.py`.
2. Bentuk layout rendering state: Dropdown Select list state `st.selectbox` "Format Aktif" memunculkan fetching style format dari DB (API HTTP Client pada scope call endpoint styles lists dari task 12) lalu push logic `set_active` saat user on_change memilih index nya.
3. Render Style Detail box: Render view list properties data metadata nama TOR Style format tersebut. Looping mapping array layout text checklist dari elemen array object `sections`.
4. Tambahkan logic Action buttons state (Edit ini, Copy ini as New Style, Hapus Style Ini). Mode Editable: ganti tampilan view text tadi dgn Streamlit Input field widget. Berikan fungsi tombol "Save Configuration" meng trigger api POST payload update config.
5. Daftarkan module view tab pada navigasi menu utama `app.py` streamlist rendering tabs (sejajar dengan tab Direct, tab Chat). 

## 6. Output yang Diharapkan
Tampilan menu Frontend dengan tab ke 4 ("Format Style TOR") dimana user streamlit bisa mengutak atik format preferensinya.

## 7. Dependencies
- [task12-frontend-api-client.md]

## 8. Acceptance Criteria
- [ ] Tab format tampil sempurna pada Streamlit dashboard.
- [ ] Default system file mengunci block UI (read-only mode), tidak bisa di edit property nya.
- [ ] Edit Custom properties bisa menambah sections, dan sukses hit HTTP request store saved data ke backend local disk service.

## 9. Estimasi
High
