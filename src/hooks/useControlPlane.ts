import { useCallback, useEffect, useState } from 'react'
import {
  ControlPlaneRequestError,
  apiJson,
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
import {
  developmentRemoteAccess,
  disableTailscaleRemoteAccess,
  enableTailscaleRemoteAccess,
  loadRemoteAccess,
  type RemoteAccessState,
} from '../data/remoteAccess'

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
  const [remoteAccess, setRemoteAccess] = useState<RemoteAccessState | null>(
    development ? developmentRemoteAccess : null,
  )
  const [state, setState] = useState<ConnectionState>(
    development ? 'development' : 'initializing',
  )
  const [error, setError] = useState<string | null>(null)
  const [setupError, setSetupError] = useState<string | null>(null)
  const [setupBusy, setSetupBusy] = useState(false)
  const [remoteBusy, setRemoteBusy] = useState(false)
  const [remoteError, setRemoteError] = useState<string | null>(null)

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

  const applyRemoteResult = useCallback(
    async (nextRemote: RemoteAccessState) => {
      const nextSetup = await loadLocalSetup()
      if (!nextSetup) {
        throw new Error(
          'Local setup became unavailable after remote access changed.',
        )
      }
      const nextSnapshot = await loadControlPlane(nextSetup.accessKey)
      sessionStorage.setItem(TOKEN_KEY, nextSetup.accessKey)
      setRemoteAccess(nextRemote)
      setLocalSetup(nextSetup)
      setSnapshot(nextSnapshot)
      setError(null)
      setState('ready')
    },
    [],
  )

  const refreshRemoteAccess = useCallback(async () => {
    if (development) return
    setRemoteBusy(true)
    setRemoteError(null)
    try {
      const remote = await loadRemoteAccess()
      setRemoteAccess(remote)
      setRemoteError(remote?.lastError || null)
    } catch (requestError) {
      setRemoteError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not inspect remote access.',
      )
    } finally {
      setRemoteBusy(false)
    }
  }, [development])

  const enableRemoteAccess = useCallback(async () => {
    if (development) return
    setRemoteBusy(true)
    setRemoteError(null)
    try {
      await applyRemoteResult(await enableTailscaleRemoteAccess())
    } catch (requestError) {
      setRemoteError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not enable remote access.',
      )
    } finally {
      setRemoteBusy(false)
    }
  }, [applyRemoteResult, development])

  const disableRemoteAccess = useCallback(async () => {
    if (development) return
    setRemoteBusy(true)
    setRemoteError(null)
    try {
      await applyRemoteResult(await disableTailscaleRemoteAccess())
    } catch (requestError) {
      setRemoteError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not disable remote access.',
      )
    } finally {
      setRemoteBusy(false)
    }
  }, [applyRemoteResult, development])

  const disconnect = useCallback(() => {
    if (development) return
    sessionStorage.removeItem(TOKEN_KEY)
    setSnapshot(null)
    setLocalSetup(null)
    setRemoteAccess(null)
    setError(null)
    setSetupError(null)
    setRemoteError(null)
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
          const [next, remote] = await Promise.all([
            loadControlPlane(local.accessKey),
            loadRemoteAccess(),
          ])
          if (!active) return
          sessionStorage.setItem(TOKEN_KEY, local.accessKey)
          setLocalSetup(local)
          setRemoteAccess(remote)
          setSnapshot(next)
          setError(null)
          setRemoteError(remote?.lastError || null)
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

  const request = useCallback(
    async <T>(input: string, init?: RequestInit): Promise<T> => {
      const credential =
        localSetup?.accessKey ?? sessionStorage.getItem(TOKEN_KEY) ?? ''
      if (!credential) throw new Error('CUICommander is not authenticated.')
      return apiJson<T>(input, credential, init)
    },
    [localSetup],
  )

  return {
    snapshot,
    localSetup,
    remoteAccess,
    state,
    error,
    setupError,
    setupBusy,
    remoteError,
    remoteBusy,
    connect,
    disconnect,
    applyLocalSetup,
    rotateAccessKey,
    refreshRemoteAccess,
    enableRemoteAccess,
    disableRemoteAccess,
    request,
    development,
    schemaUrl:
      localSetup?.gpt.schemaUrl ??
      snapshot?.schemaUrl ??
      `${window.location.origin}/cuicommander/v1/openapi`,
  }
}
