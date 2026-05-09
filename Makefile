.PHONY: dev dev-frontend build-frontend dev-backend clean

# Frontend development
dev-frontend:
	cd frontend && npm run dev

# Backend development
dev-backend:
	uvicorn app.presentation.main:app --reload --host 0.0.0.0 --port 8000

# Run both frontend + backend
dev:
	$(MAKE) dev-backend & $(MAKE) dev-frontend

# Build frontend for production
build-frontend:
	cd frontend && npm run build

# Full production build + serve
serve: build-frontend
	uvicorn app.presentation.main:app --host 0.0.0.0 --port 8000

# Clean frontend build artifacts
clean:
	rm -rf frontend/dist
