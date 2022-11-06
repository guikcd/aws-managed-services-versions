import { test, expect } from '@playwright/test'

const date: string = new Date().toISOString().replace(/T.*/, '')

test('Check generic', async ({ page }) => {
  await page.goto('https://aws-versions.iroqwa.org/index2.html')

  await expect(page).toHaveTitle(/Amazon Managed Services versions/)

  // verify that page has been generated today
  await expect(page.getByText(/Last generation:/)).toContainText(`${date}`)
})
