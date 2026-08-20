import { test, expect } from '@playwright/test';
import { v4 as uuidv4 } from 'uuid';

test.describe('E2E Full Workflow', () => {
  const email = `test-${uuidv4()}@example.com`;
  const password = 'Password123!';

  test('User can register, login, upload, and chat', async ({ page }) => {
    // 1. Register
    await page.goto('/register');
    await page.fill('input[id="email"]', email);
    await page.fill('input[id="password"]', password);
    await page.click('button[type="submit"]');

    // Should redirect to login
    await expect(page).toHaveURL(/.*\/login/);

    // 2. Login
    await page.fill('input[id="email"]', email);
    await page.fill('input[id="password"]', password);
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*\/dashboard\/documents/);

    // 3. Upload Document
    // Playwright needs to intercept file input
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('button:has-text("Upload Document")');
    const fileChooser = await fileChooserPromise;

    // Create a mock text file
    await fileChooser.setFiles({
      name: 'test-policy.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('Enterprise RAG policy states that all data must be encrypted at rest and in transit.'),
    });

    // Wait for "Ready" status
    // The table should eventually show "Ready"
    await expect(page.locator('td', { hasText: 'Ready' }).first()).toBeVisible({ timeout: 60000 });

    // 4. Chat
    await page.goto('/chat');
    
    // Ask a question
    await page.fill('input[placeholder="Ask a question..."]', 'What is the data encryption policy?');
    await page.click('button:has-text("Send")');

    // 5. Wait for Assistant Response & Citation
    await expect(page.locator('text=Sources:')).toBeVisible({ timeout: 30000 });
    const chatContainer = page.locator('.max-w-3xl');
    await expect(chatContainer).toContainText('encrypted at rest');

    // 6. Reload and verify conversation remains
    await page.reload();
    await expect(chatContainer).toContainText('What is the data encryption policy?');
  });
});
