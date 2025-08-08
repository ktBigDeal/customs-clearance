# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Korean customs law document processing system that converts legal documents from JSON format into intelligently chunked documents for AI processing. The system specializes in processing three main Korean legal documents: 관세법 (Customs Law), 관세법시행령 (Customs Law Enforcement Decree), and 관세법시행규칙 (Customs Law Enforcement Rules).

## Architecture

### Core Components

**Document Processing Pipeline**:

- `CustomsLawLoader` (src/data_processing/document_loader.py): Main class that intelligently chunks Korean legal documents at article (조) or paragraph (항) level based on content complexity
- `chunking_utils.py`: Analysis and validation utilities for processed chunks
- `process_documents.py`: CLI script orchestrating the entire workflow

**Configuration & Utilities**:

- `config.py`: Environment management, file path resolution, and settings
- `file_utils.py`: JSON I/O operations with Korean encoding support

### Data Structure

```
data/
├── DCM/
│   ├── raw_json/           # Source legal documents in JSON format
│   │   ├── 관세법.json
│   │   ├── 관세법시행령.json
│   │   └── 관세법시행규칙.json
│   ├── chunk_json/         # Processed chunked documents
│   └── PDF/                # Original PDF documents
└── IMAGE/INVOICE/          # OCR invoice images
```

### Intelligent Chunking Logic

The system uses a sophisticated chunking strategy:

- **Article-level chunking**: For simple articles with <3 paragraphs
- **Paragraph-level chunking**: For complex articles with ≥3 paragraphs
- **Legal hierarchy parsing**: Automatically extracts 편(doc) → 장(chapter) → 절(section) → 관(subsection) structure
- **Cross-reference extraction**: Identifies internal law references (법 제X조, 영 제X조) and external law references (「외부법령」)

## Development Commands

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file from example (if not exists)
python -c "from src.utils.config import create_env_example; create_env_example()"

# Validate environment setup
python scripts/process_documents.py --validate-env
```

### Document Processing

```bash
# Process all legal documents
python scripts/process_documents.py --all

# Process specific law
python scripts/process_documents.py --law 관세법

# Process with sample output
python scripts/process_documents.py --all --samples

# Process with custom output path
python scripts/process_documents.py --law 관세법 --output custom_output.json

# Verbose logging
python scripts/process_documents.py --all --verbose
```

### Testing and Validation

```bash
# Run document integrity validation
python -c "
from src.data_processing.chunking_utils import validate_chunk_integrity
from src.utils.file_utils import load_json_data
data = load_json_data('data/DCM/chunk_json/customs_law.json')
if data: print('Issues:', validate_chunk_integrity(data))
"

# Analyze chunking statistics
python -c "
from src.data_processing.chunking_utils import analyze_chunking_results, get_chunk_statistics
from src.utils.file_utils import load_json_data
data = load_json_data('data/DCM/chunk_json/customs_law.json')
if data:
    analyze_chunking_results(data)
    print('Stats:', get_chunk_statistics(data))
"
```

## Key Technical Details

### Korean Legal Document Structure

- Uses specialized regex patterns for Korean legal numbering (①②③ → 1,2,3)
- Handles complex legal references with proper hierarchy resolution
- Supports Korean legal document formatting with proper encoding (UTF-8)

### Environment Variables

Required:

- `OPENAI_API_KEY`: OpenAI API key for AI processing

Optional:

- `HF_TOKEN`: Hugging Face token for additional model access

### Output Format

Each processed chunk contains:

```json
{
    "index": "제1조" | "제5조제1항",
    "subtitle": "조문 제목",
    "content": "정제된 법조문 내용",
    "metadata": {
        "law_name": "관세법",
        "law_level": "법률" | "시행령" | "시행규칙",
        "hierarchy_path": "제1장 총칙>제1절 통칙>제1조",
        "chunk_type": "article_level" | "paragraph_level",
        "internal_law_references": {...},
        "external_law_references": [...],
        "effective_date": "YYYY.MM.DD"
    }
}
```

### Error Handling Patterns

- Comprehensive validation at each processing stage
- Korean encoding handling throughout the pipeline
- File existence checks before processing
- JSON structure validation with meaningful error messages
- Graceful degradation when optional data is missing

## Development Guidelines

### Code Conventions

- Korean comments and docstrings for domain-specific logic
- Type hints throughout for better maintainability
- Logging with both English (for logs) and Korean (for user output)
- Consistent error handling with try/catch blocks
- Path handling using pathlib for cross-platform compatibility

### Adding New Legal Documents

1. Place JSON file in `data/DCM/raw_json/`
2. Add entry to `get_law_data_paths()` and `get_output_paths()` in config.py
3. Update CLI choices in `process_documents.py`
4. Test with `--law` flag for single document processing

### Extending Chunking Logic

- Modify `determine_chunking_strategy()` for new chunking rules
- Update regex patterns in `extract_internal_law_references()` for new reference types
- Add new hierarchy levels in `extract_hierarchy_context()` if needed

# When configuring RAG Agent or Agentic RAG, please implement it by following the Langchain standard as much as possible.

# Please use the GPT 4.1-mini model when using llm using the OpenAI API. Use the text-embedding-3-small model for embedding.
