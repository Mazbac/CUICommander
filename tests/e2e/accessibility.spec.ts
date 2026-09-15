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
  await expect(page.getByText('Custom GPT setup')).toBeVisible()
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
