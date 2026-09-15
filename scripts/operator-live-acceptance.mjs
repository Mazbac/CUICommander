import process from 'node:process'

const base = (
  process.env.CUICOMMANDER_BASE_URL ?? 'http://127.0.0.1:8188'
).replace(/\/$/, '')
if (process.env.CUICOMMANDER_ACCEPT_MUTATIONS !== '1') {
  throw new Error(
    'Set CUICOMMANDER_ACCEPT_MUTATIONS=1 for operator live acceptance.',
  )
}

async function json(url, init = {}) {
  const response = await fetch(`${base}${url}`, init)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(
      `${url} failed with HTTP ${response.status}: ${body.message ?? body.error ?? 'unknown error'}`,
    )
  }
  return body
}

const setup = await json('/cuicommander/v1/local/setup')
const previousAccess = setup.accessLevel
let token = setup.accessKey
let workflowFingerprint = null
let outputPath = null
const workflowPath = `cuicommander-acceptance/workflow-${Date.now()}.json`
const filenamePrefix = `CUICommander/acceptance-${Date.now()}`
function auth(body) {
  return {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  }
}

async function inspect(root, path) {
  return json('/cuicommander/v1/resources/inspect', auth({ root, path }))
}

try {
  const elevated = await json('/cuicommander/v1/local/setup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ accessLevel: 'full' }),
  })
  token = elevated.accessKey

  const prompt = {
    1: {
      class_type: 'EmptyLatentImage',
      inputs: { width: 64, height: 64, batch_size: 1 },
    },
    2: {
      class_type: 'SaveLatent',
      inputs: { samples: ['1', 0], filename_prefix: filenamePrefix },
    },
  }

  const created = await json(
    '/cuicommander/v1/resources/create',
    auth({
      root: 'user',
      path: workflowPath,
      type: 'file',
      parents: true,
      content: JSON.stringify(prompt, null, 2),
    }),
  )
  workflowFingerprint = created.fingerprint

  const queued = await json(
    '/cuicommander/v1/execute',
    auth({
      method: 'POST',
      route: '/prompt',
      body: { prompt },
      confirmed: true,
    }),
  )
  if (queued.status !== 200 || !queued.body?.prompt_id) {
    throw new Error('Native /prompt execution did not return a prompt id.')
  }
  const promptId = queued.body.prompt_id
  let history = null
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const result = await json(
      '/cuicommander/v1/execute',
      auth({ method: 'GET', route: `/history/${promptId}` }),
    )
    const record = result.body?.[promptId]
    if (record?.status?.completed) {
      history = record
      break
    }
    await new Promise((resolve) => setTimeout(resolve, 500))
  }
  if (!history)
    throw new Error('Workflow did not reach completed history state.')

  const outputs = Object.values(history.outputs ?? {})
  const latent = outputs.flatMap((value) => value?.latents ?? [])[0]
  if (!latent?.filename)
    throw new Error('SaveLatent output was not present in history.')
  outputPath = [latent.subfolder, latent.filename].filter(Boolean).join('/')

  const activity = await json('/cuicommander/v1/activity?limit=20', {
    headers: { Authorization: `Bearer ${token}` },
  })
  const actions = new Set((activity.items ?? []).map((item) => item.action))
  if (!actions.has('resource.create') || !actions.has('runtime.execute')) {
    throw new Error('Activity feed did not contain expected mutation records.')
  }
  console.log('Operator workflow/activity live acceptance passed.')
} finally {
  try {
    if (outputPath) {
      const output = await inspect('output', outputPath)
      await json(
        '/cuicommander/v1/resources/delete',
        auth({
          root: 'output',
          path: outputPath,
          expectedFingerprint: output.fingerprint,
          confirmed: true,
        }),
      )
    }
  } catch {
    // Best-effort cleanup; the unique acceptance prefix makes leftovers obvious.
  }
  try {
    if (workflowFingerprint) {
      const workflow = await inspect('user', workflowPath)
      await json(
        '/cuicommander/v1/resources/delete',
        auth({
          root: 'user',
          path: workflowPath,
          expectedFingerprint: workflow.fingerprint,
          confirmed: true,
        }),
      )
    }
  } catch {
    // Best-effort cleanup.
  }
  try {
    await json('/cuicommander/v1/local/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accessLevel: previousAccess }),
    })
  } catch {
    // The acceptance target may have stopped before restoration.
  }
}
