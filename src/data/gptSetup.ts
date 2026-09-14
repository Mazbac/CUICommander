import { ControlPlaneRequestError, type AccessLevel } from './controlPlane'

export type LocalSetupState = {
  localAdmin: true
  accessLevel: AccessLevel
  accessKey: string
  publicBaseUrl: string
  environmentOverrides: {
    accessLevel: boolean
    accessKey: boolean
  }
  readiness: {
    httpsEndpoint: boolean
    fullControl: boolean
    readyForCustomGPT: boolean
  }
  gpt: {
    name: string
    description: string
    instructions: string
    schemaUrl: string
    authentication: {
      type: string
      placement: string
      scheme: string
      label: string
    }
    steps: string[]
  }
}

export type LocalSetupUpdate = {
  accessLevel?: AccessLevel
  publicBaseUrl?: string
}

async function localJson<T>(
  input: string,
  init?: RequestInit,
): Promise<T | null> {
  const headers = new Headers(init?.headers)
  headers.set('Accept', 'application/json')
  if (init?.body) headers.set('Content-Type', 'application/json')
  const response = await fetch(input, { ...init, headers })
  if (response.status === 403 || response.status === 404) return null
  if (!response.ok) {
    let message = `Local setup request failed (${response.status}).`
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

export async function loadLocalSetup(): Promise<LocalSetupState | null> {
  return localJson<LocalSetupState>('/cuicommander/v1/local/setup')
}

export async function updateLocalSetup(
  update: LocalSetupUpdate,
): Promise<LocalSetupState> {
  const result = await localJson<LocalSetupState>(
    '/cuicommander/v1/local/setup',
    {
      method: 'POST',
      body: JSON.stringify(update),
    },
  )
  if (!result) throw new Error('Local setup is unavailable from this origin.')
  return result
}

export async function rotateLocalAccessKey(): Promise<LocalSetupState> {
  const result = await localJson<LocalSetupState>(
    '/cuicommander/v1/local/credential/rotate',
    {
      method: 'POST',
      body: JSON.stringify({ confirmed: true }),
    },
  )
  if (!result) throw new Error('Local setup is unavailable from this origin.')
  return result
}

export const developmentLocalSetup: LocalSetupState = {
  localAdmin: true,
  accessLevel: 'inspect',
  accessKey: 'development-only-access-key',
  publicBaseUrl: '',
  environmentOverrides: {
    accessLevel: false,
    accessKey: false,
  },
  readiness: {
    httpsEndpoint: false,
    fullControl: false,
    readyForCustomGPT: false,
  },
  gpt: {
    name: 'CUICommander',
    description: 'Universal ComfyUI control plane for ChatGPT Actions.',
    instructions:
      'Discover the live ComfyUI state, use generic CRUD/transfers, execute only discovered native routes, preserve confirmation gates, and verify consequential changes.',
    schemaUrl: 'http://127.0.0.1:8188/cuicommander/v1/openapi',
    authentication: {
      type: 'api_key',
      placement: 'header',
      scheme: 'bearer',
      label: 'Bearer access key',
    },
    steps: [
      'Create a Custom GPT in ChatGPT.',
      'Paste the generated CUICommander instructions.',
      'Create an Action and import the generated OpenAPI schema URL.',
      'Configure Action authentication as an API key using Bearer authentication.',
      'Paste the CUICommander access key and run getCUICommanderManifest as the first test.',
    ],
  },
}
