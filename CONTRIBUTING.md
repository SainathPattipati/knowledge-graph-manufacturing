# Contributing

Development guidelines and setup instructions.

## Setup

```bash
git clone https://github.com/SainathPattipati/knowledge-graph-manufacturing.git
cd knowledge-graph-manufacturing
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Code Quality

- Format: `black src/`
- Lint: `ruff check src/`
- Type: `mypy src/`

## Testing

```bash
pytest tests/ -v --cov=src
```

## Commits

Use conventional commits for clarity and automation.
