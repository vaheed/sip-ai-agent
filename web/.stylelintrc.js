module.exports = {
  extends: [
    'stylelint-config-standard',
    'stylelint-config-prettier',
    'stylelint-config-tailwindcss',
  ],
  rules: {
    // BEM/utility policies
    'selector-class-pattern': [
      '^[a-z]([a-z0-9-]+)?(__([a-z0-9]+-?)+)?(--([a-z0-9]+-?)+){0,2}$',
      {
        message: 'Expected class selector to be BEM format (block__element--modifier)',
      },
    ],
    
    // Disallow !important
    'declaration-no-important': true,
    
    // Design token validation
    'color-no-hex': [
      true,
      {
        message: 'Use design tokens instead of hardcoded hex colors',
      },
    ],
    
    // Spacing consistency
    'length-zero-no-unit': true,
    'shorthand-property-no-redundant-values': true,
    
    // Tailwind CSS specific
    'at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: [
          'tailwind',
          'apply',
          'variants',
          'responsive',
          'screen',
          'layer',
        ],
      },
    ],
    'function-no-unknown': [
      true,
      {
        ignoreFunctions: ['theme', 'screen'],
      },
    ],
    
    // Accessibility
    'color-no-invalid-hex': true,
    'color-hex-case': 'lower',
    'color-hex-length': 'short',
    
    // Performance
    'max-nesting-depth': 4,
    'selector-max-compound-selectors': 4,
    'selector-max-specificity': '0,4,0',
    
    // Maintainability
    'declaration-block-no-duplicate-properties': true,
    'declaration-block-no-redundant-longhand-properties': true,
    'property-no-unknown': [
      true,
      {
        ignoreProperties: ['composes'],
      },
    ],
    
    // Formatting
    'indentation': 2,
    'string-quotes': 'single',
    'no-duplicate-selectors': true,
    'no-empty-source': null,
  },
  ignoreFiles: [
    'node_modules/**/*',
    'dist/**/*',
    'build/**/*',
    'coverage/**/*',
    '**/*.min.css',
  ],
};