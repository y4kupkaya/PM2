# Contributing to PM2 Python Library

We love your input! We want to make contributing to PM2 Python Library as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 🚀 Quick Start for Contributors

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/PM2.git
   cd PM2
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv pm2-dev
   source pm2-dev/bin/activate  # On Windows: pm2-dev\Scripts\activate
   ```
4. **Install development dependencies**:
   ```bash
   pip install -e .[dev]
   ```
5. **Create a feature branch**:
   ```bash
   git checkout -b feature/awesome-feature
   ```

## 🧪 Development Setup

### Prerequisites

- Python 3.8+
- PM2 installed globally (`npm install -g pm2`)
- Git

### Install Development Dependencies

```bash
# Install in development mode with all dependencies
pip install -e .[dev,test,docs]

# Or install manually
pip install pytest mypy black flake8 pre-commit sphinx
```

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 🧪 Testing

We use pytest for testing. Please ensure all tests pass before submitting a PR.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pm2 --cov-report=html

# Run specific test file
pytest tests/test_pm2.py -v

# Run integration tests (requires PM2)
pytest tests/test_integration.py -v -m integration
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test names
- Include both unit and integration tests
- Aim for high test coverage

Example test:

```python
import pytest
from pm2 import PM2Manager, PM2Exception

def test_pm2_manager_initialization():
    """Test PM2Manager initializes correctly."""
    manager = PM2Manager()
    assert manager is not None
    assert hasattr(manager, 'start_app')

def test_invalid_pm2_binary():
    """Test PM2Manager raises error with invalid binary path."""
    with pytest.raises(PM2Exception):
        PM2Manager(pm2_binary_path="/invalid/path/pm2")
```

## 📝 Code Style

We follow Python best practices and use automated formatting:

### Code Formatting

```bash
# Format code with black
black pm2/ tests/

# Check formatting
black --check pm2/ tests/
```

### Linting

```bash
# Lint with flake8
flake8 pm2/ tests/

# Type checking with mypy
mypy pm2/
```

### Style Guidelines

- Follow PEP 8
- Use type hints for all public APIs
- Write docstrings for all public methods
- Keep lines under 88 characters (black default)
- Use meaningful variable and function names

## 📚 Documentation

Documentation is built with Sphinx and hosted at [pm2.docs.yakupkaya.me](https://pm2.docs.yakupkaya.me).

### Building Documentation Locally

```bash
cd docs/
make html
# Open docs/_build/html/index.html in browser
```

### Documentation Guidelines

- Update docstrings for any new/changed public APIs
- Add examples to docstrings when helpful
- Update the changelog for user-facing changes
- Use proper Sphinx formatting

## 🐛 Bug Reports

We use GitHub issues to track bugs. Report a bug by [opening a new issue](https://github.com/y4kupkaya/PM2/issues/new).

### Great Bug Reports Include:

- **Summary**: Quick summary of the issue
- **Environment**: OS, Python version, PM2 version, library version
- **Steps to reproduce**: Detailed steps
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Code sample**: Minimal code that reproduces the issue

### Bug Report Template

```markdown
## Summary
Brief description of the bug

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.2]
- PM2 Version: [e.g., 5.2.0]
- Library Version: [e.g., 1.0.0]

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Code Sample
```python
# Minimal code to reproduce the issue
```

## Additional Context
Any other relevant information
```

## 🚀 Feature Requests

We welcome feature requests! Please:

1. **Check existing issues** to avoid duplicates
2. **Describe the feature** in detail
3. **Explain the use case** - why is this needed?
4. **Consider the scope** - does it fit the library's goals?

## 📋 Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is formatted with black
- [ ] Type checking passes with mypy
- [ ] Documentation is updated if needed
- [ ] Changelog is updated for user-facing changes

### Pull Request Guidelines

1. **Create a feature branch** from `main`
2. **Keep changes focused** - one feature/fix per PR
3. **Write clear commit messages**
4. **Include tests** for new functionality
5. **Update documentation** if needed
6. **Add changelog entry** for user-facing changes

### Commit Message Format

We follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(manager): add support for custom PM2 binary paths
fix(process): handle edge case when process has no PID
docs(readme): update installation instructions
```

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Tested manually

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Changelog updated
```

## 🏷️ Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release after merge
5. Publish to PyPI
6. Update documentation

## 🤝 Community Guidelines

### Code of Conduct

Be respectful and inclusive. We follow the [Python Community Code of Conduct](https://www.python.org/psf/conduct/).

### Getting Help

- 📚 [Documentation](https://pm2.docs.yakupkaya.me)
- 💬 [GitHub Discussions](https://github.com/y4kupkaya/PM2/discussions)
- 🐛 [Issue Tracker](https://github.com/y4kupkaya/PM2/issues)

### Recognition

Contributors are recognized in:
- README acknowledgments
- Release notes
- Documentation credits

## ❓ Questions?

Don't hesitate to ask questions! We're here to help:

- Create a [GitHub Discussion](https://github.com/y4kupkaya/PM2/discussions)
- Open an [issue](https://github.com/y4kupkaya/PM2/issues) with the "question" label
- Check our [documentation](https://pm2.docs.yakupkaya.me)

Thank you for contributing to PM2 Python Library! 🎉