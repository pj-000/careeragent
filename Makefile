.PHONY: test-backend run-backend

test-backend:
	cd backend && pytest

run-backend:
	cd backend && uvicorn app.main:app --reload
