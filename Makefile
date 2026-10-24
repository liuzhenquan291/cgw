.PHONY: install start stop restart status logs profiles switch web clean

DIR := $(shell pwd)
PID_FILE := $(DIR)/gateway.pid
LOG := $(DIR)/gateway.log
PY := $(DIR)/.venv/bin/python

install:
	@bash $(DIR)/install.sh

start:
	@if [ -f "$(PID_FILE)" ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "Gateway already running (PID: $$(cat $(PID_FILE)))"; \
	else \
		cd $(DIR) && source .venv/bin/activate && \
		set -a && [ -f .env ] && source .env; set +a; \
		nohup python -m uvicorn gateway:app --host 127.0.0.1 --port 8787 > $(LOG) 2>&1 & \
		echo $$! > $(PID_FILE) && sleep 2 && \
		echo "Gateway started (PID: $$(cat $(PID_FILE)))"; \
	fi

stop:
	@if [ -f "$(PID_FILE)" ]; then \
		PID=$$(cat $(PID_FILE)); \
		if kill -0 $$PID 2>/dev/null; then kill $$PID && echo "Gateway stopped"; \
		else echo "Gateway not running"; fi; \
		rm -f $(PID_FILE); \
	else echo "Gateway not running"; fi

restart: stop start

status:
	@$(PY) $(DIR)/cli.py status

profiles:
	@$(PY) $(DIR)/cli.py profiles

switch:
	@$(PY) $(DIR)/cli.py switch $(PROFILE)

active:
	@$(PY) $(DIR)/cli.py active

web:
	@$(PY) $(DIR)/cli.py web

logs:
	@tail -f $(LOG)

clean:
	@rm -f $(PID_FILE)
	@echo "Cleaned up"
