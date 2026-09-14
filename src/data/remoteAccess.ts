import { ControlPlaneRequestError } from './controlPlane'

export type RemoteAccessState = {
  provider: 'tailscale'
  installed: boolean
  version: string
  connected: boolean
  dnsName: string
  existingServices: number
  occupiedFunnelPorts: number[]
  recommendedFunnelPort: number | null
  configured: boolean
  active: boolean
  gatewayRunning: boolean
  gatewayPort: number | null
  funnelPort: number | null
  publicBaseUrl: string
  lastError: string
}

async function remoteJson<T>(
  input: string,
  init?: RequestInit,
): Promise<T | null> {
  const headers = new Headers(init?.headers)
  headers.set('Accept', 'application/json')
  if (init?.body) headers.set('Content-Type', 'application/json')
  const response = await fetch(input, { ...init, headers })
  if (response.status === 403 || response.status === 404) return null
  if (!response.ok) {
    let message = `Remote access request failed (${response.status}).`
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

export function loadRemoteAccess(): Promise<RemoteAccessState | null> {
  return remoteJson<RemoteAccessState>('/cuicommander/v1/local/remote')
}

export async function enableTailscaleRemoteAccess(): Promise<RemoteAccessState> {
  const result = await remoteJson<RemoteAccessState>(
    '/cuicommander/v1/local/remote/tailscale/enable',
    { method: 'POST', body: JSON.stringify({ confirmed: true }) },
  )
  if (!result) throw new Error('Remote access can only be managed locally.')
  return result
}

export async function disableTailscaleRemoteAccess(): Promise<RemoteAccessState> {
  const result = await remoteJson<RemoteAccessState>(
    '/cuicommander/v1/local/remote/tailscale/disable',
    { method: 'POST', body: JSON.stringify({ confirmed: true }) },
  )
  if (!result) throw new Error('Remote access can only be managed locally.')
  return result
}

export const developmentRemoteAccess: RemoteAccessState = {
  provider: 'tailscale',
  installed: true,
  version: '1.102.2',
  connected: true,
  dnsName: 'example-device.example.ts.net',
  existingServices: 2,
  occupiedFunnelPorts: [443, 8443],
  recommendedFunnelPort: 10000,
  configured: false,
  active: false,
  gatewayRunning: false,
  gatewayPort: null,
  funnelPort: null,
  publicBaseUrl: '',
  lastError: '',
}
