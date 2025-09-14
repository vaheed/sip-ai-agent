#!/usr/bin/env node

/**
 * Production-only security audit script
 * Only checks production dependencies for vulnerabilities
 */

const { execSync } = require('child_process');
const fs = require('fs');

function runAudit() {
  try {
    // eslint-disable-next-line no-console
    console.log('🔍 Running production dependencies audit...');
    
    // Get production dependencies only
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    const prodDeps = Object.keys(packageJson.dependencies || {});
    
    if (prodDeps.length === 0) {
      // eslint-disable-next-line no-console
      console.log('✅ No production dependencies to audit');
      return;
    }
    
    // eslint-disable-next-line no-console
    console.log(`📦 Checking ${prodDeps.length} production dependencies...`);
    
    // Run audit only on production dependencies
    const auditCommand = 'npm audit --audit-level=high --production';
    
    try {
      execSync(auditCommand, { stdio: 'inherit' });
      // eslint-disable-next-line no-console
      console.log('✅ Production dependencies audit passed');
    } catch (error) {
      // eslint-disable-next-line no-console
      console.log('⚠️  Some vulnerabilities found in production dependencies');
      // eslint-disable-next-line no-console
      console.log('This requires attention before deployment');
      process.exit(1);
    }
    
  } catch (error) {
    // eslint-disable-next-line no-console
    console.log('❌ Audit failed:', error.message);
    process.exit(1);
  }
}

runAudit();
