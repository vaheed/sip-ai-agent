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
    
    // Wait for the page to have some content (either static HTML or React-rendered)
    await page.waitForFunction(() => {
      const body = document.body;
      return body && body.textContent && body.textContent.length > 100;
    }, { timeout: 30000 });
    
    console.log('Global setup: Page pre-warmed successfully');
  } catch (error) {
    console.warn('Global setup: Failed to pre-warm page:', error);
  } finally {
    await browser.close();
  }
}

export default globalSetup;
