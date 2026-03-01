# ── Student Insight System — Make Targets ──────────────────────
# Usage:  make dev | make test | make seed | make migrate

.PHONY: dev test seed migrate shell clean

# Start development server
dev:
	python app.py

# Run tests with coverage
test:
	python -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

# Seed the database
seed:
	python seed.py --students --teacher --skills-catalog

# Create a new migration
migrate:
	flask db migrate -m "$(msg)"

# Apply pending migrations
upgrade:
	flask db upgrade

# Open Flask shell
shell:
	flask shell

# Remove cached files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
