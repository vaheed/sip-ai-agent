#!/bin/bash

# SIP AI Agent - Repository Cleanup Script
# This script removes all committed artifacts and caches

echo "🧹 Starting SIP AI Agent repository cleanup..."

# Remove committed artifacts
echo "Removing committed artifacts..."
git rm -r web/node_modules/ 2>/dev/null || echo "web/node_modules/ not found"
git rm -r web/coverage/ 2>/dev/null || echo "web/coverage/ not found"
git rm -r web/dist/ 2>/dev/null || echo "web/dist/ not found"
git rm -r web/playwright-report/ 2>/dev/null || echo "web/playwright-report/ not found"
git rm -r app/__pycache__/ 2>/dev/null || echo "app/__pycache__/ not found"
git rm -r tests/__pycache__/ 2>/dev/null || echo "tests/__pycache__/ not found"

# Remove disabled workflow files
echo "Removing disabled workflow files..."
git rm .github/workflows/ci.yml.disabled 2>/dev/null || echo "ci.yml.disabled not found"
git rm .github/workflows/docker-deploy.yml.disabled 2>/dev/null || echo "docker-deploy.yml.disabled not found"
git rm .github/workflows/ui-ux-quality.yml.disabled 2>/dev/null || echo "ui-ux-quality.yml.disabled not found"

# Commit the cleanup
if [ -n "$(git status --porcelain)" ]; then
    echo "Committing cleanup changes..."
    git add .
    git commit -m "chore: remove committed artifacts and disabled workflows

- Remove web/node_modules/, web/coverage/, web/dist/, web/playwright-report/
- Remove app/__pycache__/, tests/__pycache__/
- Remove disabled workflow files
- Update .gitignore to prevent future artifact commits
- Improve Playwright config with better debugging
- Strengthen TypeScript configuration
- Create single CI workflow to replace multiple disabled ones"
    
    echo "✅ Cleanup completed and committed!"
    echo "📋 Next steps:"
    echo "   1. Push changes: git push"
    echo "   2. Let CI run to verify everything works"
    echo "   3. Check CI artifacts for any test failures"
else
    echo "ℹ️ No cleanup needed - repository is already clean"
fi

echo "🎉 Repository cleanup complete!"
