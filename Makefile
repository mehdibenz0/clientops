.PHONY: install api ui test up demo

install:
	python -m pip install -r requirements.txt

api:
	PYTHONPATH=src uvicorn clientops_desk.app:app --reload

ui:
	PYTHONPATH=src streamlit run ui/app.py

test:
	PYTHONPATH=src pytest -q

up:
	docker compose up --build

demo:
	PYTHONPATH=src python scripts/demo_cli.py --scenario roster
