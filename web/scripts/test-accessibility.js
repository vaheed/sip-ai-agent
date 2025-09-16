#!/usr/bin/env node

/**
 * Test script to verify accessibility testing setup
 * This script runs both pa11y-ci and Playwright accessibility tests
 */

const { execSync } = require('child_process');
const path = require('path');

console.log('🧪 Testing accessibility setup...\n');

try {
  // Test 1: Run pa11y-ci
  console.log('1️⃣ Running pa11y-ci...');
  execSync('npx pa11y-ci', { 
    stdio: 'inherit',
    cwd: path.join(__dirname, '..')
  });
  console.log('✅ pa11y-ci completed successfully\n');

  // Test 2: Run Playwright accessibility tests
  console.log('2️⃣ Running Playwright accessibility tests...');
  execSync('npx playwright test --project=accessibility', { 
    stdio: 'inherit',
    cwd: path.join(__dirname, '..')
  });
  console.log('✅ Playwright accessibility tests completed successfully\n');

  console.log('🎉 All accessibility tests passed!');

} catch (error) {
  console.error('❌ Accessibility test failed:', error.message);
  process.exit(1);
}
