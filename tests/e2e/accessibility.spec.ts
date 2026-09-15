import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

async function expectAccessible(page: Page) {
  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
}

test('primary product pages are usable and accessible', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Home' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Home' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'ChatGPT' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Activity' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Advanced' })).toBeVisible()
  await expectAccessible(page)

  for (const [link, heading] of [
    ['ChatGPT', 'ChatGPT'],
    ['Activity', 'Activity'],
    ['Advanced', 'Advanced'],
  ] as const) {
    await page.getByRole('link', { name: link }).click()
    await expect(
      page.getByRole('heading', { name: heading, exact: true }),
    ).toBeVisible()
    await expectAccessible(page)
  }
})

test('advanced operator tools remain directly reachable and accessible', async ({
  page,
}) => {
  for (const [hash, heading] of [
    ['resources', 'Resources'],
    ['transfers', 'Transfers & jobs'],
    ['workflows', 'Workflows'],
    ['runtime', 'Runtime'],
  ] as const) {
    await page.goto(`/#/${hash}`)
    await expect(
      page.getByRole('heading', { name: heading, exact: true }),
    ).toBeVisible()
    await expectAccessible(page)
  }
})

test('narrow home reflows without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Home' })).toBeVisible()
  const widths = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }))
  expect(widths.scroll).toBe(widths.client)
  await expectAccessible(page)
})

test('dark appearance persists and remains accessible', async ({ page }) => {
  await page.goto('/')
  await page
    .getByRole('button', { name: /Appearance:/ })
    .first()
    .click()
  await page.getByRole('menuitem', { name: /Dark/ }).click()
  await expect(page.locator('html')).toHaveAttribute(
    'data-mantine-color-scheme',
    'dark',
  )
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute(
    'data-mantine-color-scheme',
    'dark',
  )
  await expect(
    page.getByRole('button', { name: 'Appearance: Dark' }).first(),
  ).toBeVisible()
  await expectAccessible(page)
})
