# Task 07 — Makefile & DevX: Development Shortcuts

## 1. Judul Task

Buat `Makefile` dengan shortcuts: `make run`, `make test`, `make ingest`, `make setup`, `make health`.

## 2. Deskripsi

Developer experience shortcuts agar team bisa cepat menjalankan tugas umum tanpa mengingat perintah panjang. Juga update `requirements.txt` untuk memastikan semua dependencies tercatat.

## 3. Tujuan Teknis

- `make run` → start dev server
- `make test` → jalankan semua tests
- `make ingest` → ingest sample documents ke RAG
- `make setup` → install deps + pull models + copy .env
- `make health` → curl health check

## 4. Scope

### Yang dikerjakan
- `Makefile` di root project
- Verifikasi `requirements.txt` lengkap

### Yang tidak dikerjakan
- Docker
- CI/CD

## 5. Langkah Implementasi

### Step 1: Buat `Makefile`

```makefile
.PHONY: run test ingest setup health

# Run development server
run:
	uvicorn app.main:app --reload --port 8000

# Run all tests
test:
	pytest tests/ -v

# Ingest example TOR documents
ingest:
	python scripts/ingest_documents.py --dir data/documents/ --category tor_example

# First-time setup
setup:
	pip install -r requirements.txt
	ollama pull qwen2.5:7b-instruct
	ollama pull bge-m3
	cp .env.example .env
	@echo "Edit .env dan set GEMINI_API_KEY sebelum make run"

# Health check
health:
	curl -s http://localhost:8000/api/v1/health | python -m json.tool
```

### Step 2: Verifikasi

```bash
make health  # harus return JSON health response
```

## 6. Output yang Diharapkan

Makefile yang berfungsi untuk semua shortcut.

## 7. Dependencies

- Semua task sebelumnya selesai

## 8. Acceptance Criteria

- [ ] `Makefile` ada di root project
- [ ] `make run` start server
- [ ] `make test` jalankan pytest
- [ ] `make health` curl health check

## 9. Estimasi

**Low** — ~20 menit
