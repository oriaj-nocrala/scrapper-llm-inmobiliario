# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python web scraping project that uses Selenium WebDriver to scrape real estate data from websites. The project is structured as a simple single-file application with a virtual environment for dependency management.

## Architecture

- **main.py**: Single entry point containing the web scraper implementation using Selenium WebDriver
- **env/**: Python virtual environment containing project dependencies
- The scraper targets real estate websites (currently configured for assetplan.cl)
- Uses headless Chrome browser automation for scraping

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source env/bin/activate

# Install dependencies (Selenium should be installed)
pip install selenium

# Deactivate environment when done
deactivate
```

### Running the Application
```bash
# Activate environment and run scraper
source env/bin/activate && python3 main.py

# Run with makefile
make scrape-quick              # Quick scraping (10 properties)
make run                       # Start FastAPI API
```

### Testing and Analysis
```bash
make test-status               # Quick system check
make analyze-metrics           # Generate code metrics
make dashboard-metrics         # Generate visual dashboard
make refactor-aggressive       # Automated refactoring
```

### Development Requirements
- Python 3.13.3
- Chrome/Chromium browser installed for Selenium WebDriver
- ChromeDriver (handled automatically by Selenium 4+)

## Key Implementation Notes

- The scraper runs in headless mode by default (no browser window)
- Chrome options include `--disable-gpu` and `--no-sandbox` for compatibility
- WebDriver service is initialized without explicit driver path (auto-managed)
- Main scraping logic is currently minimal and needs extension for specific data extraction
- Error handling uses try/finally pattern to ensure browser cleanup