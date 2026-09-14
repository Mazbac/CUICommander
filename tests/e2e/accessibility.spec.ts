import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

test('overview is usable and has no detectable accessibility violations', async ({
  page,
}) => {
  await page.goto('/')

  await expect(
    page.getByRole('heading', { name: 'CUICommander' }),
  ).toBeVisible()
  await expect(
    page.getByRole('button', { name: 'Copy schema URL' }),
  ).toBeEnabled()
  await expect(
    page.getByRole('table').getByText('ComfyUI base directory'),
  ).toBeVisible()

  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
})
