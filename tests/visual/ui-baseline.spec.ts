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

test('narrow overview remains stable', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'CUICommander' }),
  ).toBeVisible()
  await expect(page).toHaveScreenshot('overview-narrow.png', { fullPage: true })
})

test('dark desktop overview remains stable', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /Appearance:/ }).click()
  await page.getByRole('menuitem', { name: /Dark/ }).click()
  await expect(page).toHaveScreenshot('overview-dark-desktop.png', {
    fullPage: true,
  })
})

test('dark mobile overview remains stable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: /Appearance:/ }).click()
  await page.getByRole('menuitem', { name: /Dark/ }).click()
  await expect(page).toHaveScreenshot('overview-dark-mobile.png', {
    fullPage: true,
  })
})
