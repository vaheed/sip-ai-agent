import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  // Pre-warm the browser and load the page to cache resources
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Navigate to the page and wait for it to load
    await page.goto('http://localhost:8080');
    
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Wait for React to be ready
    await page.waitForFunction(() => {
      const root = document.getElementById('root');
      return root && root.children.length > 0;
    }, { timeout: 30000 });
    
    console.log('Global setup: Page pre-warmed successfully');
  } catch (error) {
    console.warn('Global setup: Failed to pre-warm page:', error);
  } finally {
    await browser.close();
  }
}

export default globalSetup;
