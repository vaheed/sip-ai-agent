import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 4, // Use more workers locally for faster execution
  globalSetup: require.resolve('./tests/e2e/global-setup'),
  // Run only quick tests by default for faster feedback
  testMatch: process.env.FULL_TESTS ? '**/*.spec.ts' : '**/quick-*.spec.ts',
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:8080',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Optimized timeouts for better performance
    actionTimeout: 10000,
    navigationTimeout: 30000,
    // Add performance optimizations
    ignoreHTTPSErrors: true,
    // Allow localStorage access in tests
    storageState: undefined,
    // Disable images and CSS for faster loading in tests
    // (uncomment if needed for specific tests)
    // launchOptions: {
    //   args: ['--disable-images', '--disable-css']
    // }
  },
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Optimize Chrome for faster testing
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-extensions',
            '--no-sandbox',
            '--disable-setuid-sandbox'
          ]
        }
      },
    },
    // Firefox disabled due to performance issues (25-42s per test)
    // {
    //   name: 'firefox',
    //   use: { 
    //     ...devices['Desktop Firefox'],
    //     // Optimize Firefox for faster testing
    //     launchOptions: {
    //       firefoxUserPrefs: {
    //         'dom.webnotifications.enabled': false,
    //         'dom.push.enabled': false,
    //         'media.navigator.permission.disabled': true,
    //         'media.navigator.streams.fake': true,
    //         'media.peerconnection.enabled': false,
    //         'media.navigator.mediadevices.enabled': false
    //       }
    //     }
    //   },
    // },
    // WebKit disabled due to protocol errors with FixedBackgroundsPaintRelativeToDocument
    // {
    //   name: 'webkit',
    //   use: { 
    //     ...devices['Desktop Safari'],
    //     // Use basic WebKit configuration without problematic settings
    //   },
    // },
    {
      name: 'accessibility',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/*.accessibility.spec.ts',
    },
  ],
  webServer: {
    command: 'cd .. && python3 -m app.web_backend',
    url: 'http://localhost:8080',
    reuseExistingServer: true, // Always reuse existing server to avoid conflicts
    timeout: 120 * 1000, // 2 minutes
  },
  // Global setup removed to fix CI issues
});