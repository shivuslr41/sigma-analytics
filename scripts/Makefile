SHELL := /bin/bash

venv := ../.venv/bin/python3

run:
	$(venv) $(file).py

depend:
	pip install -r ../requirements.txt

freeze:
	pip freeze > ../requirements.txt
