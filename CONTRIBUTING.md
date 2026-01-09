# Contributing to Sidedoc

Thank you for your interest in contributing to Sidedoc! This document outlines the contribution process and guidelines for the project.

## Development Philosophy

### Test-Driven Development (TDD) is Mandatory

**All code contributions must follow Test-Driven Development (TDD).**

This means:
1. **Write the test first** — Before any implementation code
2. **See it fail** — Run the test and verify it fails (Red)
3. **Make it pass** — Write minimal code to pass the test (Green)
4. **Refactor** — Clean up while keeping tests green

**Do not submit pull requests with:**
- Implementation code that lacks corresponding tests
- Tests written after the implementation
- Failing tests

See [CLAUDE.md](CLAUDE.md) for detailed TDD workflow and examples.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally: `git clone https://github.com/YOUR-USERNAME/sidedoc.git`
3. Install development dependencies: `pip install -e ".[dev]"` (once available)
4. Create a branch for your contribution (see [Branching Strategy](#branching-strategy) below)
5. **Always write tests first** before implementing features

## Branching Strategy

We use a simplified GitFlow workflow:

- **`main`** — The main development branch. All feature branches are created from and merged back to `main`.
- **Feature branches** — Create branches from `main` for new features, fixes, or documentation updates.

### Branch Naming

Use descriptive branch names with prefixes:

- `feature/` — New features (e.g., `feature/add-sync-command`)
- `fix/` — Bug fixes (e.g., `fix/issue-42`)
- `docs/` — Documentation updates (e.g., `docs/contributing-guide`)
- `refactor/` — Code refactoring (e.g., `refactor/extract-logic`)
- `test/` — Test additions or improvements (e.g., `test/sync-edge-cases`)

### Workflow

```bash
# Create a feature branch from main
git checkout main
git pull origin main
git checkout -b feature/my-new-feature

# Make your changes
# ... edit files ...

# Commit with conventional commits (see below)
git add .
git commit -m "feat: add new feature description"

# Push and create a pull request
git push -u origin feature/my-new-feature
gh pr create
```

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) to maintain a clear and structured commit history.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat:** A new feature
- **fix:** A bug fix
- **docs:** Documentation only changes
- **style:** Code style changes (formatting, missing semicolons, etc.)
- **refactor:** Code changes that neither fix a bug nor add a feature
- **perf:** Performance improvements
- **test:** Adding or modifying tests
- **build:** Changes to build system or dependencies
- **ci:** Changes to CI configuration files
- **chore:** Other changes that don't modify src or test files

### Examples

```bash
# Feature addition
git commit -m "feat: add extract command to CLI"

# Bug fix
git commit -m "fix: resolve issue #42 - handle empty documents"

# Documentation
git commit -m "docs: update README with installation instructions"

# Refactoring with scope
git commit -m "refactor(sync): simplify block matching algorithm"

# Breaking change (note the ! and BREAKING CHANGE footer)
git commit -m "feat!: change sidedoc file structure

BREAKING CHANGE: structure.json schema updated to v2"
```

### Guidelines

- Use imperative mood ("add feature" not "added feature")
- Keep the first line under 72 characters
- Reference issue numbers when applicable (e.g., "fix: resolve issue #42")
- Use the body to explain *what* and *why*, not *how*

## Pull Request Process

1. **Verify TDD compliance** — Confirm all tests were written before implementation
2. Ensure your code follows the project style and conventions
3. Update documentation if you've changed functionality
4. **Ensure all tests pass:** `pytest --cov=sidedoc`
5. **Verify test coverage** — Aim for >80% coverage on new code
6. Write a clear PR description explaining:
   - What problem you're solving
   - How you've solved it
   - How you followed TDD (mention that tests were written first)
   - Any relevant context or decisions
7. Link related issues (e.g., "Fixes #2" or "Closes #42")
8. Wait for code review and address feedback

### PR Checklist

- [ ] Tests written **before** implementation (TDD followed)
- [ ] All tests pass locally
- [ ] Test coverage >80% for new code
- [ ] Documentation updated
- [ ] Conventional commit messages used
- [ ] No failing tests or linting errors

## Testing

### TDD Workflow

**Always follow the Red-Green-Refactor cycle:**

```bash
# 1. RED: Write a failing test
# Edit the test file (e.g., tests/test_extract.py)

# Run the test and see it fail
pytest tests/test_extract.py::test_your_new_test -v

# 2. GREEN: Write minimal code to pass
# Edit the implementation file (e.g., src/sidedoc/extract.py)

# Run the test and see it pass
pytest tests/test_extract.py::test_your_new_test -v

# 3. REFACTOR: Clean up while keeping tests green
# Improve the code, run tests after each change
pytest tests/test_extract.py::test_your_new_test -v
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage (aim for >80%)
pytest --cov=sidedoc

# Run specific test file
pytest tests/test_extract.py

# Run specific test
pytest tests/test_extract.py::test_extract_heading -v

# Watch mode (run tests on file changes) - requires pytest-watch
ptw
```

### Test Requirements

- Tests must be written **before** implementation code
- Each test should focus on one behavior
- Tests should be independent and able to run in any order
- Use descriptive test names: `test_extract_heading_preserves_level`
- Keep tests fast (avoid unnecessary file I/O, use fixtures)

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code
- Use meaningful variable and function names
- Add docstrings to public functions and classes
- Keep functions focused and concise

## Documentation

- Update the README.md if you change functionality
- Update docstrings when modifying functions
- Add comments for complex logic
- Keep the [PRD](docs/slidedoc-prd.md) in sync with implementation decisions

## For Claude Code

If you're Claude Code contributing to this project, follow these requirements:

### TDD is Non-Negotiable

**You MUST follow Test-Driven Development:**

1. **Always write the test first** — Never write implementation code before the test
2. **Run the test and see it fail** — Verify the test fails for the right reason
3. **Write minimal code to pass** — Implement only what's needed
4. **Refactor while keeping tests green** — Improve the code incrementally

### Contribution Process

1. Create a feature branch from `main` with an appropriate prefix
2. **Start with a failing test** for every feature or bug fix
3. Use conventional commits for all changes
4. Run `pytest --cov=sidedoc` before creating PR
5. Create a pull request with a clear description
6. Reference the issue you're fixing (e.g., "Fixes #2")
7. In your PR description, explicitly mention that you followed TDD

Your contributions must follow the same TDD standards as human contributors. This is not optional.

## Questions or Issues?

If you have questions or run into issues:

- Check existing [issues](https://github.com/jogardn/sidedoc/issues)
- Open a new issue with a clear description
- Reach out to the maintainers

## License

By contributing to Sidedoc, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Sidedoc! 🎉
