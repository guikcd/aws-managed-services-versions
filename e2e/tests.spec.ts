import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {

  await page.goto('https://aws-versions.iroqwa.org/index2.html');

  await expect(page).toHaveTitle(/Amazon Managed Services versions/);

  await page.getByLabel('Search:').fill('nonexistent');

  await page.getByRole('cell', { name: 'Amazon MQ for RabbitMQ' });

});
