# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Korean customs HS code recommendation system that uses machine learning to suggest appropriate HS (Harmonized System) codes for product descriptions. The system processes Korean customs data and provides intelligent recommendations using various ML techniques.

## Core Architecture

### Main Components

- **main.py**: The main application file containing the HS code recommendation engine
- **src/**: Source code directory containing modular components
  - **hs_recommender.py**: Core recommendation engine
  - **data_processor.py**: Data loading and processing
  - **search_engine.py**: Hybrid search implementation
  - **cache_manager.py**: Caching system management
- **data/**: Data directory containing Korean customs files
  - **관세청_HS부호_2025.csv**: Korean customs HS code database for 2025
  - **관세청_표준품명_20250101.xlsx**: Standard product names from Korean customs authority
- **cache/**: Cache directory for processed data and models
- **output/**: Output directory for generated reports and exports

### Technology Stack

- **Machine Learning**: scikit-learn (TF-IDF, cosine similarity), SentenceTransformers for semantic similarity
- **Data Processing**: pandas, numpy for data manipulation
- **AI Integration**: OpenAI API for enhanced recommendations
- **Language**: Python with Korean text processing capabilities

### Key Features

The system implements multiple recommendation approaches:
- TF-IDF vectorization with cosine similarity for text matching
- Sentence transformers for semantic understanding
- OpenAI integration for advanced language understanding
- Support for Korean customs classification standards

## Development Commands

This project now uses UV for modern Python package management with enhanced compatibility and reproducibility.

### Using UV (Recommended)

Install dependencies and run the application:
```bash
# Install all dependencies in a virtual environment
uv sync

# Run the main CLI application
uv run python main.py

# Run the Gradio UI (웹 인터페이스)
uv run python ui_app.py
# 또는
uv run python run_ui.py

# Run with the convenience script
uv run hs-recommend

# Run quick test
uv run python main.py --test
```

### Gradio UI Interface

The system now includes a modern web-based user interface:

```bash
# Start the Gradio UI
uv run python ui_app.py

# Access via browser
http://localhost:7860
```

**UI Features:**
- 🔍 **Interactive Search**: Easy-to-use web interface for HS code recommendations
- 🤖 **AI Integration**: Optional OpenAI-powered advanced recommendations
- 📊 **Visual Results**: Formatted tables with confidence scores and detailed information
- ⚙️ **System Management**: Built-in system initialization and status monitoring
- 🇰🇷 **Korean Support**: Full Korean language interface and data processing
- 📱 **Responsive Design**: Works on desktop and mobile devices

### Development tools with UV:
```bash
# Format code with Black
uv run black .

# Lint code with Ruff
uv run ruff check .

# Run tests
uv run pytest
```

### Legacy method (fallback)

If UV is not available, install dependencies manually:
```bash
pip install -r requirements.txt
python main.py
```

## Working with Korean Text

- The codebase handles Korean product names and descriptions
- File names and data contain Korean characters (UTF-8 encoding)
- When modifying text processing logic, ensure proper Korean language support
- The customs data follows Korean government standards and classifications

## Project Structure

```
hs-code-recommender/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── pyproject.toml         # UV project configuration
├── uv.lock               # Locked dependencies
├── src/                   # Source code modules
│   ├── __init__.py
│   ├── hs_recommender.py  # Core recommendation engine
│   ├── data_processor.py  # Data loading and processing
│   ├── search_engine.py   # Hybrid search implementation
│   ├── cache_manager.py   # Cache management
│   └── ...
├── data/                  # Data files
│   ├── 관세청_HS부호_2025.csv
│   ├── 관세청_표준품명_20250101.xlsx
│   └── 관세청_HSK별_신성질별_성질별_분류_20250101.xlsx
├── cache/                 # Cache directory
│   ├── hs_code_cache/    # Main cache
│   └── test_cache/       # Test cache
├── output/               # Output files
├── docs/                 # Documentation
│   ├── CLAUDE.md
│   ├── README.md
│   └── Aivle-api.txt
└── requirements.txt      # Legacy dependency file
```

## Data Files

- **data/관세청_HS부호_2025.csv**: Contains the official HS code mappings for 2025
- **data/관세청_표준품명_20250101.xlsx**: Standard product nomenclature from Korean customs
- These files are essential for the recommendation system and should not be modified without understanding the Korean customs classification system

## Package Management with UV

This project uses UV for modern Python package management, providing:

- **Fast dependency resolution**: UV resolves dependencies much faster than pip
- **Reproducible builds**: `uv.lock` ensures exact same versions across environments
- **Integrated virtual environments**: Automatic venv management
- **Cross-platform compatibility**: Works consistently on Windows, macOS, and Linux
- **Development tools integration**: Built-in support for formatting, linting, and testing

### Project Structure with UV

- `pyproject.toml`: Project configuration and dependencies
- `uv.lock`: Locked dependency versions for reproducible installs
- `.venv/`: Virtual environment (auto-created by UV)

## API Configuration

The system requires an OpenAI API key for enhanced recommendations. The key is requested at runtime if not already configured.