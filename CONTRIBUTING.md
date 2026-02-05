# Contributing to Instagram Follower Manager

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help make this project better for everyone

## How to Contribute

### Reporting Bugs

If you find a bug:

1. Check if it's already reported in Issues
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, Node version)
   - Screenshots if applicable

### Suggesting Features

Feature requests are welcome! Please:

1. Check if it's already suggested
2. Describe the feature clearly
3. Explain why it would be useful
4. Consider implementation complexity

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Development Setup

```powershell
# Clone your fork
git clone https://github.com/YOUR_USERNAME/instagram-tool.git
cd instagram-tool

# Run setup
.\setup.ps1

# Create a branch
git checkout -b feature/my-feature
```

### Code Style

**Python (Backend)**
- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions focused and small

**TypeScript (Frontend)**
- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- Keep components small and focused

### Testing

Before submitting a PR:

1. Test the backend:
```powershell
cd backend
pytest
```

2. Test the frontend:
```powershell
cd frontend
npm run lint
npm run build
```

3. Manual testing:
   - Test login flow
   - Test follower analysis
   - Test unfollow functionality
   - Check error handling

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add batch selection for users
fix: Resolve login timeout issue
docs: Update installation instructions
refactor: Simplify user list component
```

Prefixes:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## Areas for Contribution

### High Priority

- [ ] Unit tests for backend
- [ ] Unit tests for frontend
- [ ] Error handling improvements
- [ ] Performance optimization
- [ ] Better logging

### Medium Priority

- [ ] Dark mode support
- [ ] Export/import follower lists
- [ ] More filter options
- [ ] Better mobile responsiveness
- [ ] Internationalization (i18n)

### Low Priority

- [ ] Advanced analytics
- [ ] Custom unfollowing schedules
- [ ] Browser notification support
- [ ] CSV export of logs

## Security

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email the maintainers privately
3. Allow time for a fix before disclosure

## Questions?

Feel free to:
- Open an issue for discussion
- Ask in Pull Request comments
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
