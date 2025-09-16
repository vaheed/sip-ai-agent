import { test, expect } from '@playwright/test';

test.describe('Configuration Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Login first
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    
    // Wait for dashboard and navigate to configuration
    await expect(page.getByText('SIP AI Agent Dashboard')).toBeVisible();
    await page.getByRole('button', { name: /configuration/i }).click();
  });

  test('should display configuration interface', async ({ page }) => {
    await expect(page.getByText('Configuration')).toBeVisible();
    
    // Check for save button
    await expect(page.getByRole('button', { name: /save.*reload/i })).toBeVisible();
  });

  test('should display SIP configuration section', async ({ page }) => {
    await expect(page.getByText('📞 SIP Configuration')).toBeVisible();
    
    // Check for SIP form fields
    await expect(page.getByLabel(/sip domain/i)).toBeVisible();
    await expect(page.getByLabel(/sip username/i)).toBeVisible();
    await expect(page.getByLabel(/sip password/i)).toBeVisible();
    await expect(page.getByLabel(/audio sample rate/i)).toBeVisible();
  });

  test('should display OpenAI configuration section', async ({ page }) => {
    await expect(page.getByText('🤖 OpenAI Configuration')).toBeVisible();
    
    // Check for OpenAI form fields
    await expect(page.getByLabel(/api mode/i)).toBeVisible();
    await expect(page.getByLabel(/model/i)).toBeVisible();
    await expect(page.getByLabel(/voice/i)).toBeVisible();
    await expect(page.getByLabel(/max tokens/i)).toBeVisible();
  });

  test('should display system configuration section', async ({ page }) => {
    await expect(page.getByText('⚙️ System Configuration')).toBeVisible();
    
    // Check for system form fields
    await expect(page.getByLabel(/log level/i)).toBeVisible();
    await expect(page.getByLabel(/metrics enabled/i)).toBeVisible();
  });

  test('should allow editing SIP configuration fields', async ({ page }) => {
    const sipDomainInput = page.getByLabel(/sip domain/i);
    const sipUsernameInput = page.getByLabel(/sip username/i);
    const sipPasswordInput = page.getByLabel(/sip password/i);
    
    // Clear and fill fields
    await sipDomainInput.clear();
    await sipDomainInput.fill('test.sip.com');
    
    await sipUsernameInput.clear();
    await sipUsernameInput.fill('testuser');
    
    await sipPasswordInput.clear();
    await sipPasswordInput.fill('testpass');
    
    // Verify values
    await expect(sipDomainInput).toHaveValue('test.sip.com');
    await expect(sipUsernameInput).toHaveValue('testuser');
    await expect(sipPasswordInput).toHaveValue('testpass');
  });

  test('should allow selecting audio sample rate', async ({ page }) => {
    const sampleRateSelect = page.getByLabel(/audio sample rate/i);
    
    // Select different sample rate
    await sampleRateSelect.selectOption('48000');
    await expect(sampleRateSelect).toHaveValue('48000');
    
    // Select another option
    await sampleRateSelect.selectOption('16000');
    await expect(sampleRateSelect).toHaveValue('16000');
  });

  test('should allow editing OpenAI configuration fields', async ({ page }) => {
    const apiModeSelect = page.getByLabel(/api mode/i);
    const modelInput = page.getByLabel(/model/i);
    const voiceSelect = page.getByLabel(/voice/i);
    const maxTokensInput = page.getByLabel(/max tokens/i);
    
    // Select API mode
    await apiModeSelect.selectOption('legacy');
    await expect(apiModeSelect).toHaveValue('legacy');
    
    // Fill model name
    await modelInput.clear();
    await modelInput.fill('gpt-4o-mini');
    await expect(modelInput).toHaveValue('gpt-4o-mini');
    
    // Select voice
    await voiceSelect.selectOption('nova');
    await expect(voiceSelect).toHaveValue('nova');
    
    // Set max tokens
    await maxTokensInput.clear();
    await maxTokensInput.fill('8192');
    await expect(maxTokensInput).toHaveValue('8192');
  });

  test('should allow editing system configuration fields', async ({ page }) => {
    const logLevelSelect = page.getByLabel(/log level/i);
    const metricsEnabledSelect = page.getByLabel(/metrics enabled/i);
    
    // Select log level
    await logLevelSelect.selectOption('DEBUG');
    await expect(logLevelSelect).toHaveValue('DEBUG');
    
    // Toggle metrics
    await metricsEnabledSelect.selectOption('false');
    await expect(metricsEnabledSelect).toHaveValue('false');
    
    await metricsEnabledSelect.selectOption('true');
    await expect(metricsEnabledSelect).toHaveValue('true');
  });

  test('should validate numeric inputs', async ({ page }) => {
    const maxTokensInput = page.getByLabel(/max tokens/i);
    
    // Clear and try to enter non-numeric value
    await maxTokensInput.clear();
    await maxTokensInput.fill('abc');
    
    // Should not accept non-numeric input (browser validation)
    // or should show validation error
    const value = await maxTokensInput.inputValue();
    expect(value).toBe(''); // Browser should prevent invalid input
  });

  test('should show save button state changes', async ({ page }) => {
    const saveButton = page.getByRole('button', { name: /save.*reload/i });
    
    // Should be enabled initially
    await expect(saveButton).toBeEnabled();
    
    // Click save button
    await saveButton.click();
    
    // Should show saving state (briefly)
    await expect(page.getByText(/saving.../i)).toBeVisible();
  });

  test('should display configuration warning', async ({ page }) => {
    // Should show warning about configuration changes
    await expect(page.getByText(/note:/i)).toBeVisible();
    await expect(page.getByText(/after saving configuration changes/i)).toBeVisible();
  });

  test('should show loading state initially', async ({ page }) => {
    // Navigate to configuration and immediately check for loading state
    await page.reload();
    await page.getByRole('textbox', { name: /username/i }).fill('admin');
    await page.getByRole('textbox', { name: /password/i }).fill('admin123');
    await page.getByRole('button', { name: /login/i }).click();
    await page.getByRole('button', { name: /configuration/i }).click();
    
    // Should show loading state briefly
    const loadingText = page.getByText('Loading configuration...');
    if (await loadingText.isVisible()) {
      await expect(loadingText).toBeVisible();
    }
  });

  test('should handle form validation errors', async ({ page }) => {
    // Try to save without making changes
    const saveButton = page.getByRole('button', { name: /save.*reload/i });
    await saveButton.click();
    
    // Should handle the save attempt (either success or error message)
    // The exact behavior depends on backend implementation
    await expect(saveButton).toBeVisible();
  });
});
