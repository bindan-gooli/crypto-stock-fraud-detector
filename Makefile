.PHONY: setup scalp dashboard targets clean

setup:
	bash setup_project.sh

scalp:
	PYTHONPATH=. python3 src/ultra_scalper.py

dashboard:
	python3 -m streamlit run src/bot_dashboard.py --server.port 8502

targets:
	PYTHONPATH=. python3 src/check_targets.py

clean:
	rm -rf *_results/
	rm -rf src/__pycache__
	rm -rf __pycache__
