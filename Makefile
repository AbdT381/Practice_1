.PHONY: run test

run:
	python src/emulator.py

test:
	python -m unittest discover -s tests -v
