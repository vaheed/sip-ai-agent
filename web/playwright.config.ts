import fs from 'node:fs'
import path from 'node:path'

import { defineConfig } from '@playwright/test'

const junitOutputDir = process.env.PLAYWRIGHT_JUNIT_OUTPUT_DIR ?? 'reports/ui'
fs.mkdirSync(junitOutputDir, { recursive: true })

export default defineConfig({
  testDir: './tests/ui',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI
    ? [
        ['list'],
        ['junit', { outputFile: path.join(junitOutputDir, 'playwright-results.xml') }],
      ]
    : [['list']],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:5173',
    trace: process.env.CI ? 'on-first-retry' : 'off',
    video: 'off',
  },
  outputDir: path.join(junitOutputDir, 'artifacts'),
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5173',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
