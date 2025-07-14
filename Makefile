.PHONY: setup install scrape test run clean help

# Use bash instead of sh for source command
SHELL := /bin/bash

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup                    - Set up virtual environment and install dependencies"
	@echo "  install                  - Install dependencies in existing environment"
	@echo ""
	@echo "Scraping:"
	@echo "  scrape                   - Run the property scraper (legacy)"
	@echo "  scrape-pro               - Run professional scraper (recommended)"
	@echo "  scrape-quick             - Quick scraping (10 properties)"
	@echo "  scrape-full              - Comprehensive scraping (50 properties)"
	@echo ""
	@echo "Testing:"
	@echo "  test-status              - Quick system status check (FASTEST)"
	@echo "  test                     - Run all pytest tests"
	@echo "  test-functional          - Run functional test suite (RECOMMENDED)"
	@echo "  test-unit                - Run unit tests only"
	@echo "  test-integration         - Run integration tests only"
	@echo "  test-all                 - Run complete test suite (pytest + custom tests)"
	@echo "  test-quick               - Run quick smoke tests"
	@echo "  test-anti-overthinking   - Test anti-overthinking functionality"
	@echo "  test-url-citation        - Test URL citation functionality"
	@echo "  test-api                 - Test API functionality"
	@echo "  test-gpu                 - Test GPU performance"
	@echo ""
	@echo "Code Analysis:"
	@echo "  analyze-code             - Detect orphan functions and dead code (legacy)"
	@echo "  analyze-smart            - Smart code analysis with categorization"
	@echo "  analyze-cli              - Interactive CLI analysis with filters"
	@echo "  analyze-cli-production   - Focus on production code analysis"
	@echo "  analyze-cli-verbose      - Detailed CLI analysis with recommendations"
	@echo "  analyze-metrics          - Generate comprehensive code metrics"
	@echo "  analyze-advanced         - Advanced ML analysis (duplicates, quality, patterns)"
	@echo "  analyze-duplicates       - Focus on duplicate code detection"
	@echo "  analyze-duplicates-quick - Fast duplicate detection (no ML)"
	@echo "  analyze-duplicates-smart - Intelligent duplicate detection (refined)"
	@echo "  analyze-quality-advanced - Advanced quality scoring with antipatterns"
	@echo "  refactor-aggressive      - Run aggressive refactoring based on metrics"
	@echo ""
	@echo "Smart Dashboard:"
	@echo "  dashboard-smart          - Start smart categorized dashboard with RAG"
	@echo ""
	@echo "Code Analysis with RAG:"
	@echo "  setup-code-rag           - Install dependencies for RAG system"
	@echo "  code-assistant           - Interactive code assistant (chat mode)"
	@echo "  code-insights            - Generate automated code insights"
	@echo "  ask-code QUESTION='...'  - Ask quick question about code"
	@echo ""
	@echo "Runtime:"
	@echo "  run                      - Start the FastAPI server"
	@echo "  clean                    - Clean up generated files"

# Set up everything from scratch
setup:
	@echo "Setting up virtual environment and installing dependencies..."
	python3 -m venv env
	source env/bin/activate && pip install --upgrade pip
	source env/bin/activate && pip install -r requirements.txt
	@echo "Setup complete! Activate with: source env/bin/activate"

# Install dependencies
install:
	source env/bin/activate && pip install --upgrade pip
	source env/bin/activate && pip install -r requirements.txt

# Run the scraper (legacy)
scrape:
	@echo "Starting property scraper..."
	source env/bin/activate && python3 -m src.scraper.professional_scraper --quick --max-properties 10

# Run the professional scraper (recommended)
scrape-pro:
	@echo "Starting professional scraper..."
	source env/bin/activate && python3 -m src.scraper.professional_scraper

# Quick scraping (10 properties, fast mode)
scrape-quick:
	@echo "Quick scraping mode..."
	source env/bin/activate && python3 -m src.scraper.professional_scraper --quick --max-properties 10

# Comprehensive scraping (50 properties, full features)
scrape-full:
	@echo "Comprehensive scraping mode..."
	source env/bin/activate && python3 -m src.scraper.professional_scraper --comprehensive --max-properties 50

# Run all tests
test:
	@echo "Running all tests..."
	source env/bin/activate && pytest tests/ -v

# Run specific test suites
test-unit:
	@echo "Running unit tests..."
	source env/bin/activate && pytest tests/ -v -m "unit or not integration"

test-integration:
	@echo "Running integration tests..."
	source env/bin/activate && pytest tests/ -v -m "integration"

# Run our custom test suites
test-anti-overthinking:
	@echo "Testing anti-overthinking functionality..."
	source env/bin/activate && python3 tests/test_anti_overthinking.py

test-url-citation:
	@echo "Testing URL citation functionality..."
	source env/bin/activate && python3 tests/test_url_citation.py

test-api:
	@echo "Testing API functionality..."
	source env/bin/activate && python3 tests/test_api_direct.py

test-gpu:
	@echo "Testing GPU performance..."
	source env/bin/activate && python3 tests/test_gpu_performance.py

# Run complete test suite
test-all:
	@echo "Running complete test suite..."
	source env/bin/activate && pytest tests/ -v
	@echo "Running custom anti-overthinking tests..."
	source env/bin/activate && python3 tests/test_anti_overthinking.py
	@echo "Running URL citation tests..."
	source env/bin/activate && python3 tests/quick_url_test.py
	@echo "All tests completed!"

# Quick smoke tests
test-quick:
	@echo "Running quick smoke tests..."
	source env/bin/activate && pytest tests/test_vectorstore.py tests/test_api.py -v
	source env/bin/activate && python3 tests/quick_url_test.py

# Run functional test suite (recommended)
test-functional:
	@echo "Running functional test suite..."
	source env/bin/activate && python3 tests/test_suite_runner.py

# Quick system status check
test-status:
	@echo "Checking system status..."
	source env/bin/activate && python3 tests/test_status.py

# Code analysis and refactoring
analyze-code:
	@echo "Analyzing code for orphan functions and dead code..."
	source env/bin/activate && python3 tools/detect_orphan_code.py

analyze-metrics:
	@echo "Analyzing code metrics..."
	source env/bin/activate && python3 tools/code_analysis/code_metrics_analyzer.py

refactor-aggressive:
	@echo "Running aggressive refactoring..."
	source env/bin/activate && python3 tools/aggressive_refactor.py

# Smart CLI Analysis
analyze-cli:
	@echo "Running smart CLI analysis..."
	source env/bin/activate && python3 tools/smart_cli_analyzer.py

analyze-cli-production:
	@echo "Analyzing production code only..."
	source env/bin/activate && python3 tools/smart_cli_analyzer.py --production-only --verbose

analyze-cli-verbose:
	@echo "Running detailed CLI analysis..."
	source env/bin/activate && python3 tools/smart_cli_analyzer.py --verbose

# Advanced ML Analysis
analyze-advanced:
	@echo "Running advanced ML analysis..."
	source env/bin/activate && python3 tools/advanced_code_analyzer.py --verbose

analyze-duplicates:
	@echo "Analyzing duplicate code..."
	source env/bin/activate && python3 tools/advanced_code_analyzer.py --duplicates-only --verbose

analyze-duplicates-quick:
	@echo "Quick duplicate detection..."
	source env/bin/activate && python3 tools/quick_duplicate_detector.py --verbose

analyze-duplicates-smart:
	@echo "Intelligent duplicate detection..."
	source env/bin/activate && python3 tools/refined_duplicate_detector.py --verbose

analyze-quality-advanced:
	@echo "Advanced quality analysis..."
	source env/bin/activate && python3 tools/quality_scorer.py --verbose

analyze-advanced-save:
	@echo "Running advanced analysis with detailed output..."
	source env/bin/activate && python3 tools/advanced_code_analyzer.py --verbose --output tools/advanced_report.json

# RAG System for Code Analysis
setup-code-rag:
	@echo "Setting up RAG system for code analysis..."
	source env/bin/activate && pip install sentence-transformers numpy faiss-cpu

code-assistant:
	@echo "Starting interactive code assistant..."
	source env/bin/activate && python3 tools/utilities/code_assistant.py

code-insights:
	@echo "Generating code insights..."
	source env/bin/activate && python3 tools/code_analysis/code_insights.py

ask-code:
	@echo "Quick code question..."
	source env/bin/activate && python3 tools/utilities/code_assistant.py --question "$(QUESTION)"


# Smart Categorized Analysis
analyze-smart:
	@echo "Running smart code analysis..."
	source env/bin/activate && python3 tools/code_analysis/smart_code_analyzer.py

dashboard-smart:
	@echo "Starting smart categorized dashboard..."
	source env/bin/activate && python3 tools/categorized_dashboard_server.py

# Start the API server
run:
	@echo "Starting FastAPI server..."
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__ .pytest_cache
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete