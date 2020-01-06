.PHONY: all help install uninstall clean

PLAYBOOK=ansible-playbook

all: help install

help:
	@echo "make command options"
	@echo "  install               install this collection to the users path (~/.ansible/collections)"
	@echo "  uninstall             uninstall this collection from the users path (~/.ansible/collections)"
	@echo ""

clean:
	rm -rf log/*
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

install: uninstall
	$(PLAYBOOK) installer/install.yml

uninstall:
	$(PLAYBOOK) installer/uninstall.yml
