# Contributing to SIP AI Agent

Thank you for considering a contribution to this project! We welcome bug reports, feature requests, and pull requests. The following guidelines help ensure a smooth collaboration and maintain high code quality.

## 🐛 How to Report Bugs

If you encounter unexpected behavior or a defect:

1. **Check existing issues** to see if your problem has already been reported or fixed
2. **Open a new issue** with a clear and descriptive title
3. **Include detailed information**:
   - What happened vs. what you expected
   - Steps to reproduce the issue
   - Environment details (OS, Docker version, Python version)
   - Relevant logs and error messages
   - Screenshots if applicable
4. **Label appropriately** (bug, enhancement, documentation, etc.)

## ✨ How to Request Features

1. **Describe the feature** you would like to see implemented
2. **Explain the use case** and why it would benefit other users
3. **Provide examples** or reference implementations if possible
4. **Consider implementation complexity** and suggest a basic approach

## 🚀 Development Workflow

### 1. Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/your-username/sip-ai-agent.git
cd sip-ai-agent

# Setup development environment
make setup-dev

# Install pre-commit hooks
pre-commit install
```

### 2. Create a Feature Branch

   ```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 3. Development Standards

#### Python Code Standards
- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code style
- Use Black for code formatting (automated via pre-commit)
- Use isort for import sorting (automated via pre-commit)
- Document all functions, classes, and modules with docstrings
- Add type hints for all function parameters and return values
- Write comprehensive tests with pytest
- Handle all exceptions gracefully with proper logging

#### Frontend Code Standards
- Follow React and TypeScript best practices
- Use ESLint and Stylelint rules (configured in project)
- Follow BEM naming conventions for CSS
- Use design tokens instead of hardcoded values
- Write unit tests with Vitest
- Write E2E tests with Playwright
- Ensure accessibility compliance (WCAG 2.1 AA)

#### Code Quality Requirements
- All code must pass linting and type checking
- Test coverage should be maintained above 80%
- Security scanning must pass (bandit, safety)
- UI/UX quality gates must pass (ESLint, Stylelint, accessibility tests)

### 4. Testing

```bash
# Run all tests
make test

# Run specific test suites
make test-python        # Python unit tests
make test-web           # Frontend tests
make test-e2e          # End-to-end tests

# Run quality checks
make check-all         # All quality gates
make ui-quality        # UI/UX quality checks
make security          # Security scanning
```

### 5. Commit Changes

Use conventional commit messages:

   ```bash
git commit -m "feat: add new SIP configuration option"
git commit -m "fix: resolve WebSocket connection timeout issue"
git commit -m "docs: update deployment guide with new features"
git commit -m "test: add unit tests for call history module"
```

### 6. Pull Request Process

1. **Push your branch** to GitHub
2. **Open a pull request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots for UI changes
   - Testing instructions
3. **Ensure CI passes** - all GitHub Actions workflows must pass
4. **Address review feedback** promptly and professionally

## 🧪 Testing Guidelines

### Python Testing
- Write unit tests for all new functions and classes
- Use pytest fixtures for common test objects
- Mock external dependencies (SIP, OpenAI, WebSocket)
- Test error conditions and edge cases
- Maintain test coverage above 80%

### Frontend Testing
- Write unit tests for React components
- Use Testing Library for component testing
- Write E2E tests for critical user flows
- Test accessibility with axe-core
- Ensure responsive design works on all devices

### Integration Testing
- Test SIP registration and call handling
- Test OpenAI API integration
- Test WebSocket real-time updates
- Test configuration management
- Test call history and analytics

## 📝 Documentation Requirements

### Code Documentation
- Document all public functions and classes
- Use clear, descriptive docstrings
- Include examples for complex functions
- Document configuration options and environment variables

### User Documentation
- Update README.md for new features
- Add troubleshooting steps for common issues
- Update API documentation for new endpoints
- Include screenshots for UI changes

## 🔒 Security Guidelines

### Security Best Practices
- Never commit sensitive information (API keys, passwords)
- Use environment variables for configuration
- Validate all input parameters
- Follow secure coding practices
- Run security scans before submitting PRs

### Security Testing
- All code must pass bandit security scanning
- Docker images must pass Trivy vulnerability scanning
- Dependencies must pass safety checks
- Authentication and authorization must be properly implemented

## 🎨 UI/UX Guidelines

### Design Standards
- Follow the established design system
- Use design tokens for colors, spacing, and typography
- Ensure consistent component behavior
- Maintain responsive design principles

### Accessibility
- Follow WCAG 2.1 AA guidelines
- Test with screen readers
- Ensure keyboard navigation works
- Maintain proper color contrast ratios
- Use semantic HTML elements

### Performance
- Optimize for Core Web Vitals
- Minimize bundle size
- Use lazy loading where appropriate
- Ensure Lighthouse scores meet minimum thresholds

## 🚀 Release Process

### Version Management
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Update CHANGELOG.md for all releases
- Tag releases with proper version numbers
- Create GitHub releases with release notes

### Release Checklist
- [ ] All tests pass
- [ ] Code quality gates pass
- [ ] Security scans pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped
- [ ] Git tag created
- [ ] GitHub release created

## 🤝 Code Review Process

### For Contributors
- Be responsive to review feedback
- Make requested changes promptly
- Ask questions if feedback is unclear
- Be open to suggestions and improvements

### For Reviewers
- Provide constructive feedback
- Focus on code quality and maintainability
- Test the changes thoroughly
- Be respectful and professional

## 📋 Issue Templates

When opening issues, use the provided templates:
- Bug Report
- Feature Request
- Documentation Update
- Security Vulnerability

## 🔧 Development Tools

### Required Tools
- Python 3.9+
- Node.js 18+
- Docker and Docker Compose
- Git
- Make

### Recommended Tools
- VS Code with Python and TypeScript extensions
- Pre-commit hooks
- Browser developer tools
- Postman for API testing

## 📞 Getting Help

### Community Support
- Check existing issues and discussions
- Join our community Discord/Slack (if available)
- Ask questions in GitHub Discussions

### Direct Support
- For security issues, email security@your-domain.com
- For urgent bugs, use the "urgent" label
- For feature requests, use the "enhancement" label

## 📄 Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Please:

- Be respectful and kind
- Use welcoming and inclusive language
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

Harassment or abusive behavior will not be tolerated. We follow the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct.

## 🎉 Recognition

Contributors will be:
- Listed in the project's CONTRIBUTORS.md file
- Mentioned in release notes for significant contributions
- Invited to maintainer status for consistent high-quality contributions

---

Thank you for helping improve the SIP AI Agent project! Your contributions make this project better for everyone. 🚀