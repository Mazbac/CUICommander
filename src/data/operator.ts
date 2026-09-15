export type RootItem = {
  id: string
  label: string
  path: string
  source: 'core' | 'folder_paths'
  exists: boolean
}

export type ResourceEntry = {
  name: string
  type: 'file' | 'directory' | 'symlink' | 'unreadable'
  size?: number | null
  modifiedNs?: number
}

export type ResourceInfo = ResourceEntry & {
  root: string
  path: string
  fingerprint: string
  fingerprintMode: string
  items?: ResourceEntry[]
  itemOffset?: number
  itemLimit?: number
  totalItems?: number
  nextOffset?: number | null
  truncated?: boolean
  mimeType?: string
  preview?: string | null
  previewEncoding?: 'utf-8' | 'base64'
  previewTruncated?: boolean
}

export type ResourceChunk = {
  root: string
  path: string
  size: number
  offset: number
  fingerprint: string
  fingerprintMode: string
  mimeType: string
  encoding: 'utf-8' | 'base64'
  content?: string
  contentBase64?: string
  bytesRead: number
  eof: boolean
  nextOffset: number | null
}

export type DiscoveryPage<T> = {
  items: T[]
  offset: number
  limit: number
  totalItems: number
  nextOffset: number | null
  complete: boolean
}

export type JobItem = {
  id: string
  kind: string
  status: string
  root?: string
  path?: string
  source?: string
  bytesReceived?: number
  totalBytes?: number | null
  createdAt: number
  updatedAt: number
  error?: { type?: string; message?: string }
}

export type NodeItem = {
  name: string
  category: string
  module: string
  returnTypes: string[]
  function: string
  inputTypes?: Record<string, unknown>
  inputTypesError?: string
}

export type RouteItem = {
  method: string
  path: string
  source: string
}

export type NativeResult = {
  method: string
  route: string
  status: number
  contentType: string
  body: unknown
  bodyTruncated: boolean
  responseId?: string | null
  responseSize?: number
  nextOffset?: number | null
}

export type NativeResponseChunk = {
  responseId: string
  size: number
  offset: number
  contentType: string
  encoding: 'utf-8' | 'base64'
  content?: string
  contentBase64?: string
  bytesRead: number
  eof: boolean
  nextOffset: number | null
}

export type ActivityItem = {
  id: string
  at: number
  action: string
  detail: Record<string, unknown>
}

export const developmentRoots: RootItem[] = [
  {
    id: 'comfyui',
    label: 'ComfyUI base directory',
    path: 'C:/ComfyUI',
    source: 'core',
    exists: true,
  },
  {
    id: 'user',
    label: 'User',
    path: 'C:/ComfyUI/user',
    source: 'core',
    exists: true,
  },
]

export const developmentResource: ResourceInfo = {
  name: 'workflows',
  type: 'directory',
  root: 'user',
  path: 'default/workflows',
  fingerprint: '0'.repeat(64),
  fingerprintMode: 'tree-metadata',
  items: [
    { name: 'demo.json', type: 'file', size: 2048 },
    { name: 'archive', type: 'directory', size: null },
  ],
  truncated: false,
}

export const developmentNodes: NodeItem[] = [
  {
    name: 'KSampler',
    category: 'sampling',
    module: 'nodes',
    returnTypes: ['LATENT'],
    function: 'sample',
  },
  {
    name: 'SaveImage',
    category: 'image',
    module: 'nodes',
    returnTypes: [],
    function: 'save_images',
  },
]

export const developmentRoutes: RouteItem[] = [
  { method: 'POST', path: '/prompt', source: 'aiohttp' },
  { method: 'GET', path: '/queue', source: 'aiohttp' },
  { method: 'GET', path: '/history', source: 'aiohttp' },
]

export const developmentJobs: JobItem[] = [
  {
    id: '00000000-0000-4000-8000-000000000001',
    kind: 'download',
    status: 'succeeded',
    root: 'models',
    path: 'checkpoints/example.safetensors',
    bytesReceived: 1024,
    totalBytes: 1024,
    createdAt: Date.now() - 5000,
    updatedAt: Date.now() - 1000,
  },
]

export const developmentActivity: ActivityItem[] = [
  {
    id: 'activity-1',
    at: Date.now() - 1000,
    action: 'resource.update',
    detail: { root: 'user', path: 'default/workflows/demo.json' },
  },
]
