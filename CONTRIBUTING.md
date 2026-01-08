# Contributing to Sidedoc

Thank you for your interest in contributing to Sidedoc! This document outlines our contribution process and guidelines.

## Getting Started

1. Fork the repository and clone your fork
2. See [README.md](README.md) for development setup instructions
3. Look for issues labeled `good first issue` or `help wanted`

## GitFlow Branching Strategy

We use a simplified GitFlow model with `main` as the primary branch. All work should be done in feature branches.

### Branch Types

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New features | `feature/add-sync-command` |
| `bugfix/` | Bug fixes | `bugfix/fix-empty-paragraph-handling` |
| `hotfix/` | Critical production fixes | `hotfix/security-patch` |
| `docs/` | Documentation changes | `docs/update-installation-guide` |
| `release/` | Release preparation | `release/v1.0.0` |

### Workflow

1. Create a branch from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. Make your changes with conventional commits (see below)

3. Push and open a Pull Request to `main`:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. After review and CI passes, your PR will be merged

## Conventional Commits

We use [Conventional Commits](https://www.conventionalcommits.org/) for clear, structured commit messages.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `chore` | Maintenance tasks (dependencies, config, etc.) |

### Examples

```
feat(cli): add sync command for updating docx files
fix(extract): handle empty paragraphs in source documents
docs: update installation instructions in README
test(sync): add integration tests for conflict detection
refactor(models): simplify block structure representation
chore: update python-docx dependency to 1.1.0
```

## For Claude Code (AI Contributors)

Claude Code and other AI assistants **MUST** follow the same contribution process as human contributors:

1. **Always create feature branches** — Never commit directly to `main`
2. **Branch from `main`** — Start all work from an up-to-date `main` branch
3. **Use conventional commits** — Follow the commit format described above
4. **Open Pull Requests** — All changes go through PR review
5. **Follow code standards** — Adhere to existing patterns and test requirements

This ensures consistent code quality and maintains a clear project history regardless of who (or what) is contributing.

## Pull Request Process

1. **Write a clear description** — Explain what your PR does and why
2. **Reference related issues** — Use `Fixes #123` or `Relates to #456`
3. **Ensure CI passes** — All tests must pass before merge
4. **Request review** — Wait for approval from a maintainer
5. **Keep PRs focused** — One feature or fix per PR when possible

## Code Standards

- Follow existing patterns in the codebase
- Add tests for new functionality
- Update documentation when adding or changing features
- Ensure `pytest` passes before submitting

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
