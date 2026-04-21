.PHONY: setup run test clean logs status backup

setup:
	pip install -r requirements.txt
	pip install python-dotenv
	cp .env.example .env
	@echo " Setup complete! Edit .env with your API keys"

run:
	python bot/main.py

test:
	python -m pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf logs/*.txt logs/*.xlsx data/*.json backups/*.json 2>/dev/null || true

logs:
	tail -f logs/ethusdt.txt

status:
	@echo " Bot Status:"
	@ps aux | grep "python bot/main.py" | grep -v grep || echo "Bot not running"
	@echo ""
	@echo " Active Trades:"
	@cat data/active_trades.json 2>/dev/null | python -m json.tool | grep -E "(buy_price|quantity)" || echo "No active trades"

backup:
	@mkdir -p backups
	@cp data/active_trades.json backups/active_trades_$$(date +%Y%m%d_%H%M%S).json 2>/dev/null || true
	@echo " Backup created"

docker-build:
	docker build -t trading-bot .

docker-run:
	docker-compose up -d

docker-logs:
	docker-compose logs -f

docker-stop:
	docker-compose down