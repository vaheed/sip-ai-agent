import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use;
  
  // Start browser and navigate to the app to ensure it's ready
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    await page.goto(baseURL!, { waitUntil: 'networkidle' });
    console.log('✅ Global setup: App is ready for testing');
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
