test:
	docker compose exec api /bin/bash -c "source .venv/bin/activate && pytest ."

start: 
	docker compose up --watch