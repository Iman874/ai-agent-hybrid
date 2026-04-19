# Task 09: GenerateService Integration

## 1. Judul Task
Integrasi Penuh Format Provider ke Generation Orchestration Service

## 2. Deskripsi
Menggabungkan seluruh modul pipeline logic backend. Data JSON style bacaan File Sistem disalurkan via orchestrator fungsi untuk dipakai (string building render properties ke format) oleh Module Prompter Injector Gemini, dan memompa config dynamic rule post-processor engine pasca run output AI text.

## 3. Tujuan Teknis
Menyuntikkan instance parameter variabel service `StyleManager` ke Constructor dependency class service `GenerateService` (`app/services/generate_service.py`), untuk fetch active ID style model, convert properties data method prompt build function string injection, dan memforward ke postprocessor execution parameter attribute style argument.

## 4. Scope
* **Yang dikerjakan**: Injection depedensi parameter backend `GenerateService` constructor dan modify code workflow `generate_tor`.
* **Yang tidak dikerjakan**: Testing Frontend.

## 5. Langkah Implementasi
1. Update injection point (contoh di `main.py` atau IOC dependency factory file FastAPI Router call dependency provider endpoint instansiasi objects) -> Berikan instansiasi objek `StyleManager` sebagai argumen yang dibutuhkan `GenerateService`.
2. Buka `app/services/generate_service.py`. Modify def inisialisasi parameter menambahkan args internal untuk assignment objek kelas `style_manager`.
3. Dalam root execution coroutine method `generate_tor(...)`: panggil properti function self `get_active_style()`.
4. Berikan property class list section dan template configurations di atas ke module object formatting text render yaitu Call `.to_prompt_spec()` properties objek yang dihasilkan get_active_style. 
5. Inject properti rendered specs di atas jadi tambahan list property fungsi build args call pada file GeminiPromptBuilder pemroses string payload format instruksi arg parameter (seperti parameter pada Task 05 design plan).
6. Sesudah eksekusi await async execution hit payload output selesai, update call arguments `PostProcessor.process()` mem-pasokan parameter data active object rules style ke `style=objek`.

## 6. Output yang Diharapkan
Kode terupdate menghubung secara harmoni menggerakkan pipeline alur yang secara dinamis mengubah output berdasarkan config disk storage runtime.

## 7. Dependencies
- [task03-style-manager-crud.md]
- [task05-prompt-injector.md]
- [task08-postprocessor-update.md]

## 8. Acceptance Criteria
- [ ] API Generate berjalan tanpa mematahkan logika internal eksisting.
- [ ] Output doc AI secara konstan berisikan susunan yang akurat merepresentasikan file disk storage default json maupun style lain yang kebetulan sedang set active.

## 9. Estimasi
Medium
