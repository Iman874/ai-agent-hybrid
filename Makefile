.PHONY: run test ingest setup health ui

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

# Run Streamlit UI
ui:
	streamlit run streamlit_app.py --server.port 8501

