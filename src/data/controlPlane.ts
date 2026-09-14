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
  roots: RootSummary[]
  capabilities: Array<{
    title: string
    description: string
    access: 'read' | 'write' | 'full'
  }>
}

export const developmentControlPlane: ControlPlaneSnapshot = {
  version: '0.1.0-dev',
  comfyVersion: 'live runtime required',
  status: 'needs-runtime',
  accessLevel: 'inspect',
  schemaUrl: 'http://127.0.0.1:8188/cuicommander/v1/openapi',
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
  capabilities: [
    {
      title: 'Discover and inspect',
      description:
        'Read live nodes, routes, roots, files, and directories without vendor adapters.',
      access: 'read',
    },
    {
      title: 'Generic CRUD',
      description:
        'Create, replace, move, and delete ComfyUI-scoped files and directories with stale-state protection.',
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
  ],
}
