# SIP AI Agent - Web UI

Modern React-based web interface for the SIP AI Agent with comprehensive UI/UX quality checks.

## 🚀 Quick Start

```bash
# Install dependencies and setup Playwright
npm run setup

# Start development server
npm run dev

# Build for production
npm run build

# Run all quality checks
npm run quality
```

### Playwright E2E Testing Setup

```bash
# Setup Playwright environment (installs dependencies and browsers)
npm run setup

# Run quick E2E tests
npm run test:e2e:quick

# Run full E2E test suite
npm run test:e2e:full

# Run E2E tests with UI
npm run test:e2e:ui

# Debug E2E tests
npm run test:e2e:debug
```

## 🎨 Design System

### Design Tokens

All design decisions are centralized in `design-tokens.json`:

- **Colors**: Primary, secondary, success, warning, error palettes
- **Spacing**: Consistent spacing scale (xs, sm, md, lg, xl, 2xl, 3xl)
- **Typography**: Font families, sizes, weights, line heights
- **Border Radius**: Consistent corner rounding
- **Shadows**: Elevation system
- **Breakpoints**: Responsive design breakpoints

### Component Library

Built with Storybook for component development and documentation:

```bash
# Start Storybook
npm run storybook

# Build Storybook
npm run build-storybook
```

## 🔍 Quality Checks

### Code Style & Design Rules

#### ESLint (JS/TS)
- **Naming conventions**: camelCase for variables, PascalCase for components
- **Component patterns**: Arrow functions, consistent file extensions
- **Import organization**: Automatic import sorting and grouping
- **Accessibility**: JSX-a11y rules for ARIA, keyboard navigation
- **TypeScript**: Strict type checking and best practices

#### Stylelint (CSS)
- **BEM methodology**: Block__Element--Modifier naming
- **No !important**: Prevents specificity issues
- **Design tokens**: Validates use of design tokens over hardcoded values
- **Tailwind CSS**: Proper utility class usage
- **Performance**: Limits nesting depth and selector complexity

#### Design Token Validation
```bash
# Validate design tokens
npm run design-tokens

# Check for hardcoded values
npm run lint
```

### Accessibility (a11y)

#### Automated Scans
- **pa11y-ci**: WCAG 2.1 AA compliance testing
- **axe-core**: Comprehensive accessibility testing
- **Playwright**: E2E accessibility validation

#### Key Checks
- Color contrast ratios (4.5:1 minimum)
- Keyboard navigation support
- Screen reader compatibility
- Focus management
- ARIA labels and roles
- Semantic HTML structure

```bash
# Run accessibility tests
npm run a11y

# Run E2E accessibility tests
npm run test:e2e
```

### Visual Consistency

#### Visual Regression Testing
- **Percy**: Automated visual diff detection
- **Playwright**: Screenshot comparison
- **Multi-device testing**: Desktop, tablet, mobile views
- **Theme testing**: Light/dark mode consistency

#### Test Coverage
- Homepage, dashboard, call history, config pages
- Form states (empty, filled, error, loading)
- Component states (hover, focus, active, disabled)
- Responsive breakpoints

```bash
# Run visual regression tests
npm run visual-regression
```

### UX Quality / Best Practices

#### Lighthouse CI
- **Performance**: Core Web Vitals (LCP, FID, CLS)
- **Accessibility**: WCAG compliance scoring
- **Best Practices**: Security, modern web standards
- **SEO**: Search engine optimization
- **PWA**: Progressive Web App features

#### Minimum Score Gates
- Performance: ≥90
- Accessibility: ≥90
- Best Practices: ≥90
- SEO: ≥90
- PWA: ≥80

```bash
# Run Lighthouse tests
npm run lighthouse
```

### Component Contracts

#### Storybook Requirements
- **Required stories**: Button, Input, Modal, Table, Form
- **Documentation**: Auto-generated component docs
- **Controls**: Interactive property testing
- **Accessibility**: Built-in a11y addon

#### Testing Requirements
- **Unit tests**: Jest + Testing Library
- **Interaction tests**: User event simulation
- **Accessibility tests**: axe-core integration
- **Focus order**: Keyboard navigation validation
- **ARIA compliance**: Screen reader support

```bash
# Run unit tests
npm run test

# Run tests with coverage
npm run test:coverage
```

## 🛠️ Development Workflow

### Pre-commit Hooks
```bash
# Install pre-commit hooks
npm install

# Hooks automatically run:
# - ESLint (fix auto-fixable issues)
# - Stylelint (fix auto-fixable issues)
# - Prettier (format code)
# - TypeScript (type checking)
# - Tests (affected files only)
```

### Code Quality Pipeline
1. **Local Development**: Pre-commit hooks
2. **Pull Request**: Full quality gate
3. **Merge to Main**: Production build + quality checks
4. **Release**: Version tagging + deployment

### Quality Gate Requirements
All checks must pass before merging:
- ✅ Code style (ESLint + Stylelint)
- ✅ Accessibility (pa11y + axe-core)
- ✅ Visual regression (Percy + Playwright)
- ✅ Performance (Lighthouse CI)
- ✅ Component tests (Jest + Storybook)
- ✅ Integration tests (Playwright E2E)

## 📊 Monitoring & Reporting

### GitHub Actions Integration
- **Automated testing**: On every PR and push
- **Quality gates**: Block merges on failures
- **Artifact uploads**: Test results and reports
- **Security scanning**: Vulnerability detection

### Reports Generated
- **Coverage reports**: Code coverage metrics
- **Lighthouse reports**: Performance and UX scores
- **Accessibility reports**: WCAG compliance results
- **Visual regression**: Screenshot comparisons
- **Storybook build**: Component documentation

## 🎯 Best Practices

### Component Development
1. **Start with Storybook**: Create stories first
2. **Write tests**: Unit + accessibility tests
3. **Use design tokens**: No hardcoded values
4. **Follow BEM**: Consistent CSS naming
5. **Document props**: TypeScript interfaces

### Accessibility First
1. **Semantic HTML**: Use proper elements
2. **ARIA labels**: Provide context
3. **Keyboard navigation**: Full keyboard support
4. **Color contrast**: WCAG AA compliance
5. **Screen readers**: Test with actual tools

### Performance Optimization
1. **Code splitting**: Lazy load components
2. **Image optimization**: WebP format, lazy loading
3. **Bundle analysis**: Monitor bundle size
4. **Core Web Vitals**: Optimize LCP, FID, CLS
5. **Caching**: Proper cache headers

## 🔧 Configuration

### ESLint Configuration
```javascript
// .eslintrc.js
module.exports = {
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:jsx-a11y/recommended',
    'plugin:import/recommended',
    'prettier',
  ],
  rules: {
    // Custom rules for naming, patterns, accessibility
  },
};
```

### Stylelint Configuration
```javascript
// .stylelintrc.js
module.exports = {
  extends: [
    'stylelint-config-standard',
    'stylelint-config-tailwindcss',
    'stylelint-config-prettier',
  ],
  rules: {
    // BEM naming, no !important, design tokens
  },
};
```

### Playwright Configuration
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:8080',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
```

## 📚 Resources

- [Storybook Documentation](https://storybook.js.org/docs)
- [Playwright Testing](https://playwright.dev/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [pa11y Accessibility Testing](https://pa11y.org/)
- [axe-core Accessibility Engine](https://github.com/dequelabs/axe-core)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## 🆘 Troubleshooting

### Common Issues

#### ESLint Errors
```bash
# Fix auto-fixable issues
npm run lint:fix

# Check specific file
npx eslint src/components/Button.tsx
```

#### Stylelint Errors
```bash
# Fix auto-fixable issues
npm run stylelint:fix

# Check specific file
npx stylelint src/index.css
```

#### Accessibility Failures
```bash
# Run specific accessibility test
npx pa11y http://localhost:8080

# Check specific component
npx axe http://localhost:8080/dashboard
```

#### Visual Regression Issues
```bash
# Update baseline images
npm run visual-regression -- --update-snapshots

# Check specific page
npx playwright test tests/e2e/visual-regression.spec.ts
```

#### Performance Issues
```bash
# Run Lighthouse locally
npx lighthouse http://localhost:8080

# Check bundle size
npm run build && npx bundle-analyzer dist/
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow quality standards**: All checks must pass
4. **Write tests**: Unit, accessibility, and E2E tests
5. **Update documentation**: Storybook stories and README
6. **Submit a pull request**: Quality gates will run automatically

### Quality Checklist
- [ ] Code follows ESLint and Stylelint rules
- [ ] Components have Storybook stories
- [ ] Unit tests written and passing
- [ ] Accessibility tests passing
- [ ] Visual regression tests passing
- [ ] Lighthouse scores meet minimums
- [ ] Documentation updated
- [ ] No hardcoded values (use design tokens)
