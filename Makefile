# c:\Users\parth\OneDrive\Desktop\one\CallGPT\Makefile
PYTHON = python   # use the Windows interpreter name

# install dependencies
install:
	uv add -r requirements.txt


# run FastAPI app
api:
	uv run uvicorn app.main:app --reload

 
# run Streamlit app
frontend:
	$(PYTHON) -m streamlit run streamlit_app.py

# format code
format:
	uv run ruff format .

# lint code
lint:
	uv run flake8 --config .flake8 .
