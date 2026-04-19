# Task 12: Frontend API Client Update

## 1. Judul Task
Menambahkan Method Http Connector Styles Streamlit Backend Router

## 2. Deskripsi
Mengembangkan SDK/Class Helper connector local backend REST (file `client.py` Streamlit requests fetcher backend HTTP module interface) untuk mengenalkan jalur API Styles baru. 

## 3. Tujuan Teknis
Membentuk method functions python pada `app/streamlit_app/api/client.py` yang mendefinisikan pembungkusan routing wrapper library Requests CRUD operations format model API Backend layer di task 06.

## 4. Scope
* **Yang dikerjakan**: Update module wrapper request SDK python facade. Def class request API wrapper properties arguments typehints response conversion dict. 
* **Yang tidak dikerjakan**: Logic Backend. Logic UI Frontend rendering.

## 5. Langkah Implementasi
1. Buka file `streamlit_app/api/client.py`.
2. Pada Base URL mapping functions API class properties methods properties, assign functions `get_styles()`. Method ini throw GET REST URI endpoint base dan me-response parsing json request lists API respon object content payload structure nya. 
3. Assign Method `get_active_style()` -> Request API hit url spesifiknya response dict properties nya.
4. Assign functions mutator update config object -> list update parameters POST payload function requests method form format config style schema dict to URL hit endpoint format create config mutator API property uri params.
5. Assign action extraction module mutator parameter arguments POST multipart form bytes data properties requests upload extraction endpoint module module API facade method functions request arguments model args stream payloads multipart form properties content param list file blob response mapping.  

## 6. Output yang Diharapkan
Class SDK local frontend Client.py mempunyai function method proxy call wrapper list crud module yang bersih dengan validasi format dict dictionary yang ready digunakan streamlit component function module view.

## 7. Dependencies
- Tidak Ada / Tersedia doc spec list routing URL di design plan (API REST Endpoint structure docs task 06). 

## 8. Acceptance Criteria
- [ ] Method list di file class proper terbentuk tanpa dependency error module missing import list name functions proper python.
- [ ] Dapat terhubung jika Backend API routes terdeploy list endpoint schema property response hit property proper valid string url payload property uri request. 

## 9. Estimasi
Low
