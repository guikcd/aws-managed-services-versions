import { test, expect } from '@playwright/test'

// const date: Date = new Date()

test('Check filter with kubernetes', async ({ page }) => {
  await page.goto('https://aws-versions.iroqwa.org/index2.html')

  await expect(page).toHaveTitle(/Amazon Managed Services versions/)

  // await expect(page.getByRole('cell', { name: 'aaa' })).toBeTruthy()
  // await expect(page).toMatch(/Last generation: ${ date }/);
  await page.getByLabel('Search:').fill('kubernetes');

  await expect(page.getByText('Amazon Elastic Kubernetes Service (Amazon EKS)').first(), 'should match EKS').toContainText("EKS");

})
