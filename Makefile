# c:\Users\parth\OneDrive\Desktop\one\CallGPT\Makefile
PYTHON = python   # use the Windows interpreter name

.PHONY: install api frontend format lint

# install dependencies
install:
	uv add -r requirements.txt


# run FastAPI app
api:
	uv run uvicorn app.main:app --reload

 
# run frontend
frontend:
	npm --prefix frontend run dev

# format code
format:
	uv run ruff format .

# lint code
lint:
	uv run flake8 --config .flake8 .
