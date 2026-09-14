export type AccessLevel = 'inspect' | 'edit' | 'full'

export type RootSummary = {
  id: string
  label: string
  source: 'core' | 'folder_paths'
  detail: string
}

export type ControlPlaneSnapshot = {
  version: string
  comfyVersion: string
  status: 'ready' | 'needs-runtime'
  accessLevel: AccessLevel
  schemaUrl: string
  rootCount: number
  roots: RootSummary[]
  capabilities: Array<{
    title: string
    description: string
    access: 'read' | 'write' | 'full'
  }>
}

export class ControlPlaneRequestError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}
const capabilities: ControlPlaneSnapshot['capabilities'] = [
  {
    title: 'Discover and inspect',
    description:
      'Read live nodes, routes, roots, files, and directories without vendor adapters.',
    access: 'read',
  },
  {
    title: 'CRUD + transfers',
    description:
      'Create, replace, move, delete, and background-download ComfyUI-scoped resources with stale-state and transfer safeguards.',
    access: 'write',
  },
  {
    title: 'Native execution',
    description:
      'Use ComfyUI workflow, queue, job, and discovered route primitives instead of one action per node.',
    access: 'full',
  },
  {
    title: 'Full-control fallback',
    description:
      'Reach ComfyUI-owned runtime/source details when narrower primitives cannot express the operation.',
    access: 'full',
  },
]

export const developmentControlPlane: ControlPlaneSnapshot = {
  version: '0.4.0-dev',
  comfyVersion: 'live runtime required',
  status: 'needs-runtime',
  accessLevel: 'inspect',
  schemaUrl: 'http://127.0.0.1:8188/cuicommander/v1/openapi',
  rootCount: 3,
  roots: [
    {
      id: 'comfyui',
      label: 'ComfyUI base directory',
      source: 'core',
      detail: 'Complete ComfyUI installation tree from folder_paths.base_path.',
    },
    {
      id: 'models',
      label: 'Models',
      source: 'core',
      detail:
        'Base models directory plus every registered external model path.',
    },
    {
      id: 'registered.*',
      label: 'Dynamic registered roots',
      source: 'folder_paths',
      detail:
        'Checkpoints, LoRAs, VAEs, custom nodes, and future path categories are discovered live.',
    },
  ],
  capabilities,
}

type ManifestResponse = {
  version: string
  comfyVersion: string
  accessLevel: AccessLevel
  schemaUrl: string
  rootCount: number
}
type RootResponse = {
  id: string
  label: string
  path: string
  source: 'core' | 'folder_paths'
  exists: boolean
}

async function apiJson<T>(
  input: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers)
  headers.set('Authorization', `Bearer ${token}`)
  if (init?.body) headers.set('Content-Type', 'application/json')

  const response = await fetch(input, { ...init, headers })
  if (!response.ok) {
    let message = `CUICommander request failed (${response.status}).`
    try {
      const body = (await response.json()) as { message?: string }
      if (body.message) message = body.message
    } catch {
      // Keep the status-based fallback for non-JSON failures.
    }
    throw new ControlPlaneRequestError(message, response.status)
  }
  return (await response.json()) as T
}

export async function loadControlPlane(
  token: string,
): Promise<ControlPlaneSnapshot> {
  const manifest = await apiJson<ManifestResponse>(
    '/cuicommander/v1/manifest',
    token,
  )
  const discovered = await apiJson<{ items: RootResponse[] }>(
    '/cuicommander/v1/discover',
    token,
    {
      method: 'POST',
      body: JSON.stringify({ kind: 'roots', limit: 500 }),
    },
  )

  const roots = discovered.items.slice(0, 12).map((root) => ({
    id: root.id,
    label: root.label,
    source: root.source,
    detail: root.exists ? root.path : `${root.path} (missing)`,
  }))

  return {
    version: manifest.version,
    comfyVersion: manifest.comfyVersion,
    status: 'ready',
    accessLevel: manifest.accessLevel,
    schemaUrl: manifest.schemaUrl,
    rootCount: manifest.rootCount,
    roots,
    capabilities,
  }
}
