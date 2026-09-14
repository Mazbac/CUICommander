import { expect, test } from '@playwright/test'

test('desktop overview remains stable', async ({ page }) => {
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'CUICommander' }),
  ).toBeVisible()
  await expect(page).toHaveScreenshot('overview-desktop.png', {
    fullPage: true,
  })
})

test('mobile overview remains stable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'CUICommander' }),
  ).toBeVisible()
  await expect(page).toHaveScreenshot('overview-mobile.png', { fullPage: true })
})
