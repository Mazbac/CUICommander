import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

async function expectAccessible(page: Page) {
  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
}

test('operator console pages are usable and accessible', async ({ page }) => {
  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: 'CUICommander' }),
  ).toBeVisible()
  await expect(page.getByText('Connect ChatGPT', { exact: true })).toBeVisible()
  await page
    .getByRole('button', { name: /3 Copy the connection into ChatGPT/ })
    .click()
  await expect(
    page.getByRole('button', { name: 'Copy instructions' }),
  ).toBeEnabled()
  await expectAccessible(page)

  const pages = [
    ['Resources', 'Resources'],
    ['Transfers & jobs', 'Transfers & jobs'],
    ['Workflows', 'Workflows'],
    ['Runtime', 'Runtime'],
    ['Activity', 'Activity'],
  ] as const

  for (const [link, heading] of pages) {
    await page.getByRole('link', { name: link }).click()
    await expect(
      page.getByRole('heading', { name: heading, exact: true }),
    ).toBeVisible()
    await expectAccessible(page)
  }
})

test('narrow overview reflows without horizontal overflow', async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'CUICommander' }),
  ).toBeVisible()
  const widths = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }))
  expect(widths.scroll).toBe(widths.client)
  await expectAccessible(page)
})

test('dark appearance persists and remains accessible', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Appearance: System' }).click()
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
    page.getByRole('button', { name: 'Appearance: Dark' }),
  ).toBeVisible()
  await expectAccessible(page)
})
