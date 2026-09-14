import { useCallback, useEffect, useState } from 'react'
import {
  ControlPlaneRequestError,
  developmentControlPlane,
  loadControlPlane,
  type ControlPlaneSnapshot,
} from '../data/controlPlane'

const TOKEN_KEY = 'cuicommander.sessionToken'

export type ConnectionState =
  'development' | 'needs-auth' | 'connecting' | 'ready' | 'error'

function initialStoredToken(development: boolean) {
  if (development) return null
  return sessionStorage.getItem(TOKEN_KEY)
}
export function useControlPlane() {
  const development = import.meta.env.DEV
  const storedToken = initialStoredToken(development)
  const [snapshot, setSnapshot] = useState<ControlPlaneSnapshot | null>(
    development ? developmentControlPlane : null,
  )
  const [state, setState] = useState<ConnectionState>(
    development ? 'development' : storedToken ? 'connecting' : 'needs-auth',
  )
  const [error, setError] = useState<string | null>(null)

  const handleFailure = useCallback((requestError: unknown) => {
    if (
      requestError instanceof ControlPlaneRequestError &&
      requestError.status === 401
    ) {
      sessionStorage.removeItem(TOKEN_KEY)
    }
    setSnapshot(null)
    setError(
      requestError instanceof Error
        ? requestError.message
        : 'Could not connect to CUICommander.',
    )
    setState('error')
  }, [])

  const connect = useCallback(
    async (token: string) => {
      if (development) return
      const normalized = token.trim()
      if (!normalized) {
        setError('Enter the CUICommander access key.')
        setState('needs-auth')
        return
      }

      setState('connecting')
      setError(null)
      try {
        const next = await loadControlPlane(normalized)
        sessionStorage.setItem(TOKEN_KEY, normalized)
        setSnapshot(next)
        setState('ready')
      } catch (requestError) {
        handleFailure(requestError)
      }
    },
    [development, handleFailure],
  )

  const disconnect = useCallback(() => {
    if (development) return
    sessionStorage.removeItem(TOKEN_KEY)
    setSnapshot(null)
    setError(null)
    setState('needs-auth')
  }, [development])

  useEffect(() => {
    if (development || !storedToken) return
    let active = true
    void loadControlPlane(storedToken)
      .then((next) => {
        if (!active) return
        setSnapshot(next)
        setError(null)
        setState('ready')
      })
      .catch((requestError: unknown) => {
        if (!active) return
        handleFailure(requestError)
      })
    return () => {
      active = false
    }
  }, [development, handleFailure, storedToken])

  return {
    snapshot,
    state,
    error,
    connect,
    disconnect,
    schemaUrl:
      snapshot?.schemaUrl ??
      `${window.location.origin}/cuicommander/v1/openapi`,
  }
}
