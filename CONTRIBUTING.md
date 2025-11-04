# Contributing to Hyperliquid TWAP API

This document provides guidelines for contributing to the Hyperliquid TWAP API project.

## Code of Conduct

Be respectful, inclusive, and constructive. This is an open-source project for the DeFi community.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages and logs

### Suggesting Enhancements

1. Open an issue with the `enhancement` label
2. Describe the feature:
   - Use case and motivation
   - Proposed implementation
   - Potential drawbacks
   - Alternatives considered

### Pull Requests

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes:
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new features
   - Update documentation
4. Test your changes:
   ```bash
   poetry run pytest
   poetry run black src/
   poetry run flake8 src/
   ```
5. Commit your changes:
   ```bash
   git commit -m "feat: add new feature"
   ```
   Follow [Conventional Commits](https://www.conventionalcommits.org/)
6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.9+
- Poetry
- Docker (optional)
- PostgreSQL (optional, SQLite works for dev)

### Setup

```bash
# Clone your fork
git clone https://github.com/shelteredcorgi/HL-TWAP-API.git
cd HL-TWAP-API

# Install dependencies
poetry install

# Copy environment config
cp .env.example .env

# Initialize database
poetry run python -c "from src.hl_twap_api.models.database import init_db; init_db()"

# Run tests
poetry run pytest
```

## Code Style

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Use type hints where appropriate

### Code Formatting

```bash
# Format code
poetry run black src/ tests/

# Check linting
poetry run flake8 src/ tests/
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_api.py

# Run specific test
poetry run pytest tests/test_api.py::test_get_trades_with_auth
```

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 80%
- Use fixtures from `conftest.py`
- Test edge cases and error conditions

Example:

```python
def test_my_feature(client, test_db):
    """Test my new feature."""
    # Arrange
    test_data = {...}

    # Act
    response = client.get("/api/v1/endpoint")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_data
```

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat: add CSV export endpoint
fix: resolve timezone conversion bug
docs: update API reference
test: add tests for data processor
```

## Project Structure

```
src/hl_twap_api/
├── api/              # FastAPI routes and schemas
├── models/           # Database models
├── services/         # Business logic
├── utils/            # Utilities
├── config.py         # Configuration
└── main.py           # Entry point
```

When adding new features:
- API endpoints go in `api/app.py`
- Schemas go in `api/schemas.py`
- Database models go in `models/`
- Business logic goes in `services/`
- Utilities go in `utils/`

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Include type hints
- Document exceptions
- Provide usage examples

### User Documentation

When adding features, update:
- `README.md` - High-level overview
- `API_REFERENCE.md` - API endpoint docs
- `SETUP.md` - Setup instructions (if needed)

## Review Process

1. Automated checks must pass:
   - Tests
   - Code formatting (Black)
   - Linting (Flake8)

2. Manual review by maintainers:
   - Code quality
   - Test coverage
   - Documentation
   - Breaking changes

3. Feedback and iteration:
   - Address review comments
   - Update as needed
   - Re-request review

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open an issue for questions
- Start a discussion on GitHub Discussions
- Tag maintainers in your PR

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes
- Project documentation
