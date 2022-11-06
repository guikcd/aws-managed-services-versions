import { test, expect } from '@playwright/test'

test('Check filter with kubernetes', async ({ page }) => {
  await page.goto('https://aws-versions.iroqwa.org/index2.html')

  await page.getByLabel('Search:').fill('kubernetes');

  await expect(page.getByText('Amazon Elastic Kubernetes Service (Amazon EKS)').first(), 'should match EKS').toContainText("EKS");

})