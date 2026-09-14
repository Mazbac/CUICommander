import { useCallback, useEffect, useState } from 'react'
import {
  ControlPlaneRequestError,
  developmentControlPlane,
  loadControlPlane,
  type ControlPlaneSnapshot,
} from '../data/controlPlane'
import {
  developmentLocalSetup,
  loadLocalSetup,
  rotateLocalAccessKey,
  updateLocalSetup,
  type LocalSetupState,
  type LocalSetupUpdate,
} from '../data/gptSetup'

const TOKEN_KEY = 'cuicommander.sessionToken'

export type ConnectionState =
  | 'development'
  | 'initializing'
  | 'needs-auth'
  | 'connecting'
  | 'ready'
  | 'error'

export function useControlPlane() {
  const development = import.meta.env.DEV
  const [snapshot, setSnapshot] = useState<ControlPlaneSnapshot | null>(
    development ? developmentControlPlane : null,
  )
  const [localSetup, setLocalSetup] = useState<LocalSetupState | null>(
    development ? developmentLocalSetup : null,
  )
  const [state, setState] = useState<ConnectionState>(
    development ? 'development' : 'initializing',
  )
  const [error, setError] = useState<string | null>(null)
  const [setupError, setSetupError] = useState<string | null>(null)
  const [setupBusy, setSetupBusy] = useState(false)

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

  const applyLocalSetup = useCallback(
    async (update: LocalSetupUpdate) => {
      if (development) return
      setSetupBusy(true)
      setSetupError(null)
      try {
        const nextSetup = await updateLocalSetup(update)
        const nextSnapshot = await loadControlPlane(nextSetup.accessKey)
        sessionStorage.setItem(TOKEN_KEY, nextSetup.accessKey)
        setLocalSetup(nextSetup)
        setSnapshot(nextSnapshot)
        setError(null)
        setState('ready')
      } catch (requestError) {
        setSetupError(
          requestError instanceof Error
            ? requestError.message
            : 'Could not update local setup.',
        )
      } finally {
        setSetupBusy(false)
      }
    },
    [development],
  )

  const rotateAccessKey = useCallback(async () => {
    if (development) return
    setSetupBusy(true)
    setSetupError(null)
    try {
      const nextSetup = await rotateLocalAccessKey()
      const nextSnapshot = await loadControlPlane(nextSetup.accessKey)
      sessionStorage.setItem(TOKEN_KEY, nextSetup.accessKey)
      setLocalSetup(nextSetup)
      setSnapshot(nextSnapshot)
      setError(null)
      setState('ready')
    } catch (requestError) {
      setSetupError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not rotate the local access key.',
      )
    } finally {
      setSetupBusy(false)
    }
  }, [development])

  const disconnect = useCallback(() => {
    if (development) return
    sessionStorage.removeItem(TOKEN_KEY)
    setSnapshot(null)
    setLocalSetup(null)
    setError(null)
    setSetupError(null)
    setState('needs-auth')
  }, [development])

  useEffect(() => {
    if (development) return
    let active = true

    const initialize = async () => {
      try {
        const local = await loadLocalSetup()
        if (!active) return
        if (local) {
          const next = await loadControlPlane(local.accessKey)
          if (!active) return
          sessionStorage.setItem(TOKEN_KEY, local.accessKey)
          setLocalSetup(local)
          setSnapshot(next)
          setError(null)
          setState('ready')
          return
        }

        const stored = sessionStorage.getItem(TOKEN_KEY)
        if (!stored) {
          setState('needs-auth')
          return
        }
        const next = await loadControlPlane(stored)
        if (!active) return
        setSnapshot(next)
        setError(null)
        setState('ready')
      } catch (requestError) {
        if (!active) return
        handleFailure(requestError)
      }
    }

    void initialize()
    return () => {
      active = false
    }
  }, [development, handleFailure])

  return {
    snapshot,
    localSetup,
    state,
    error,
    setupError,
    setupBusy,
    connect,
    disconnect,
    applyLocalSetup,
    rotateAccessKey,
    schemaUrl:
      localSetup?.gpt.schemaUrl ??
      snapshot?.schemaUrl ??
      `${window.location.origin}/cuicommander/v1/openapi`,
  }
}
