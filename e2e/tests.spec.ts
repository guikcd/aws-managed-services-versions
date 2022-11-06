import { test, expect } from '@playwright/test'

const date: Date = new Date()

test('test', async ({ page }) => {
  await page.goto('https://aws-versions.iroqwa.org/index2.html')

  await expect(page).toHaveTitle(/Amazon Managed Services versions/)

  await expect(page.getByLabel('Search:').fill('nonexistent')).toBeTruthy()

  await page.getByRole('cell', { name: 'Amazon MQ for RabbitMQdzadza' })

  // await expect(page).toMatch(/Last generation: ${ date }/);
})
