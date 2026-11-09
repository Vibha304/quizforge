.PHONY: dev backend frontend install test lint seed create-sample

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

dev:
	start /B cmd /c "cd backend && python -m uvicorn app.main:app --reload --port 8000"
	cd frontend && npm run dev

backend:
	cd backend && python -m uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest tests/ -v
	cd frontend && npm run test

seed:
	cd backend && python seed.py

create-sample:
	cd backend && python scripts/create_sample_pdf.py
