import { readFileSync } from 'node:fs'
import process from 'node:process'
import { chromium } from '@playwright/test'

const baseUrl = process.env.CUICOMMANDER_BASE_URL ?? 'http://127.0.0.1:8188'
const tokenFile = process.env.CUICOMMANDER_TOKEN_FILE
const configuredToken = process.env.CUICOMMANDER_API_TOKEN?.trim()

function readAccessKey() {
  if (configuredToken) return configuredToken
  if (!tokenFile) {
    throw new Error(
      'Set CUICOMMANDER_API_TOKEN or CUICOMMANDER_TOKEN_FILE for a non-local acceptance target.',
    )
  }
  const value = JSON.parse(
    readFileSync(tokenFile, 'utf8').replace(/^\uFEFF/, ''),
  )
  const token = String(value.token ?? '').trim()
  if (!token) throw new Error('Configured CUICommander access key is empty.')
  return token
}
async function connectIfNeeded(page) {
  const ready = page.getByText('Ready', { exact: true })
  const accessInput = page.getByLabel('Access key', { exact: true })
  await Promise.any([
    ready.waitFor({ timeout: 10_000 }),
    accessInput.waitFor({ timeout: 10_000 }),
  ])

  if (await accessInput.isVisible().catch(() => false)) {
    await accessInput.fill(readAccessKey())
    await page.getByRole('button', { name: 'Connect' }).click()
  }
  await ready.waitFor({ timeout: 10_000 })
}

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
try {
  const root = baseUrl.replace(/\/$/, '')
  await page.goto(`${root}/cuicommander/`, { waitUntil: 'networkidle' })
  await page.getByRole('heading', { name: 'CUICommander' }).waitFor()
  await connectIfNeeded(page)
  await page.getByText(/CUICommander .* \| ComfyUI /).waitFor()
  await page
    .getByRole('table')
    .getByText('ComfyUI base directory', { exact: true })
    .waitFor()

  const openapiResponse = await page.request.get(
    `${root}/cuicommander/v1/openapi`,
  )
  if (!openapiResponse.ok())
    throw new Error('OpenAPI endpoint was not reachable.')
  const schema = await openapiResponse.json()
  const leakedLocalPath = Object.keys(schema.paths ?? {}).find((path) =>
    path.startsWith('/cuicommander/v1/local/'),
  )
  if (leakedLocalPath) {
    throw new Error(
      `Local admin route leaked into Action schema: ${leakedLocalPath}`,
    )
  }

  const publicOrigin = page.getByLabel('Public origin')
  if (await publicOrigin.isVisible().catch(() => false)) {
    await page.getByText('Custom GPT setup', { exact: true }).waitFor()
    await page.getByRole('button', { name: 'Copy instructions' }).waitFor()
    await page.getByRole('button', { name: 'Copy Action schema URL' }).waitFor()
    const localKey = await page.getByLabel('Action access key').inputValue()
    if (!localKey)
      throw new Error('Local setup did not provide an Action access key.')
  }
  await page.reload({ waitUntil: 'networkidle' })
  await connectIfNeeded(page)

  await page.getByRole('button', { name: 'Disconnect' }).click()
  await page.getByText('Authentication required', { exact: true }).waitFor()
  await page.getByLabel('Access key', { exact: true }).waitFor()

  console.log('Live embedded UI and Custom GPT setup acceptance passed.')
} finally {
  await browser.close()
}
