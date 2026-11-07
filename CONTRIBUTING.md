# Contributing to CodeMind AI

Thank you for your interest in contributing to **CodeMind AI**! We welcome community contributions, bug reports, feature requests, and pull requests.

---

## Code of Conduct

We are dedicated to providing a welcoming, diverse, and harassment-free environment for everyone. Please be respectful and constructive in all interactions.

---

## How to Contribute

### 1. Reporting Bugs
- Search existing GitHub Issues before opening a new one.
- Provide a clear, reproducible example with sample Python source code.
- Include environment details (OS, Python version, dependency versions).

### 2. Suggesting Features
- Open an Issue with the prefix `[Feature Request]`.
- Clearly explain the problem the feature solves and how it fits with Hindsight memory.

### 3. Submitting Pull Requests
1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Set up** your development environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or .\.venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. **Make your changes** following PEP 8 conventions.
4. **Run the test suite**:
   ```bash
   python -m pytest tests/ -v
   ```
5. **Commit** using conventional commit messages:
   - `feat: add new convention filter`
   - `fix: handle edge case in ast visitor`
   - `docs: update setup guide`
6. **Push** to your fork and submit a Pull Request targeting the `main` branch.

---

## Development Guidelines

- **Memory Integrity**: All persistent memory logic must integrate with the Hindsight SDK (`hindsight-client`). Do not introduce ad-hoc local in-memory hacks that bypass the Hindsight memory bank.
- **Security**: Never commit real API keys, passwords, or credentials. Use `.env` with `.env.example`.
- **Typing**: Use Python type annotations (`typing`) across all new functions and methods.
- **Tests**: Add unit tests for any new parser, engine, or API features in the `tests/` directory.

---

## Questions?

Feel free to open an issue or reach out via [GitHub Discussions](https://github.com/rdharshinir/CodeMind-AI/issues).
