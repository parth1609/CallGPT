# c:\Users\parth\OneDrive\Desktop\one\CallGPT\Makefile
PYTHON = python   # use the Windows interpreter name

# install dependencies
install:
	uv add -r requirements.txt

# backend app.py
backend:
	$(PYTHON) app.py

# backend with parameter
backend-rag:
	$(PYTHON) app.py --input input.txt --rebuild --llm-provider groq --question "Where vecotr is used?"


# run Streamlit app
frontend:
	$(PYTHON) -m streamlit run streamlit_app.py

# format code
format:
	uv run flake8 --config .flake8 .
