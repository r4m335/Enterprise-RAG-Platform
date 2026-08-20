import { test, expect } from '@playwright/test';
import { v4 as uuidv4 } from 'uuid';

test.describe('Multi-tenant Security Isolation', () => {
  const userA = { email: `a-${uuidv4()}@example.com`, password: 'Password123!' };
  const userB = { email: `b-${uuidv4()}@example.com`, password: 'Password123!' };

  test('User A cannot access User B documents or chats', async ({ browser }) => {
    // Context A
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();
    
    // Register A
    await pageA.goto('/register');
    await pageA.fill('input[id="email"]', userA.email);
    await pageA.fill('input[id="password"]', userA.password);
    await pageA.click('button[type="submit"]');
    
    await pageA.waitForURL(/.*\/login/);
    await pageA.fill('input[id="email"]', userA.email);
    await pageA.fill('input[id="password"]', userA.password);
    await pageA.click('button[type="submit"]');
    await pageA.waitForURL(/.*\/dashboard\/documents/);
    
    // Upload document as User A
    const fileChooserPromise = pageA.waitForEvent('filechooser');
    await pageA.click('button:has-text("Upload Document")');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'top-secret-a.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('This is a secret for User A.'),
    });

    await expect(pageA.locator('td', { hasText: 'Ready' }).first()).toBeVisible({ timeout: 60000 });

    // Context B
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();
    
    // Register B
    await pageB.goto('/register');
    await pageB.fill('input[id="email"]', userB.email);
    await pageB.fill('input[id="password"]', userB.password);
    await pageB.click('button[type="submit"]');
    
    await pageB.waitForURL(/.*\/login/);
    await pageB.fill('input[id="email"]', userB.email);
    await pageB.fill('input[id="password"]', userB.password);
    await pageB.click('button[type="submit"]');
    await pageB.waitForURL(/.*\/dashboard\/documents/);
    
    // Verify B does not see A's document
    await expect(pageB.locator('text=top-secret-a.txt')).not.toBeVisible();
    
    // Verify B cannot query A's document in chat
    await pageB.goto('/chat');
    await pageB.fill('input[placeholder="Ask a question..."]', 'What is the secret?');
    await pageB.click('button:has-text("Send")');
    
    await pageB.waitForTimeout(5000); // Wait a bit for response
    // Should not contain the exact secret text from A
    const chatContainer = pageB.locator('.max-w-3xl');
    await expect(chatContainer).not.toContainText('This is a secret for User A.');
  });
});
