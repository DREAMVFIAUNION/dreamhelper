# Contributing to DreamHelper

Thank you for your interest in contributing to DreamHelper.

## Before you start
- Check existing issues before opening a new one.
- Use GitHub Discussions for questions, ideas, and broader product conversations.
- Use GitHub Issues for confirmed bugs, focused feature requests, and actionable tasks.

## Recommended contribution flow
1. Fork the repository.
2. Create a focused branch from `master`.
3. Keep changes scoped and easy to review.
4. Add or update tests when behavior changes.
5. Update documentation when needed.
6. Open a pull request with a clear summary and validation notes.

## Pull request guidelines
- Use a descriptive title.
- Explain what changed and why.
- Include screenshots or terminal output for UI and DX changes.
- Link related issues when applicable.
- Keep unrelated changes out of the same PR.

## Development notes
- Frontend: `pnpm --filter web-portal dev`
- Gateway: `pnpm --filter gateway dev`
- AI Core: `cd services/brain-core && uvicorn src.main:app --reload --port 8000`
- Tests: `pnpm test` and relevant Python test commands

## Good first contributions
- Documentation improvements
- Bug fixes with clear reproduction steps
- Test coverage improvements
- UX polish and developer experience improvements

## Communication
Please be respectful, constructive, and specific. We value contributors who help improve the product, code quality, and long-term maintainability of the ecosystem.
