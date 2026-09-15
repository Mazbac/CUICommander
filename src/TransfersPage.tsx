import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Group,
  Paper,
  Progress,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
} from '@mantine/core'
import { EmptyState } from './components/ui/EmptyState'
import { PageHeader } from './components/ui/PageHeader'
import { Section } from './components/ui/Section'
import {
  developmentJobs,
  developmentRoots,
  type JobItem,
  type RootItem,
} from './data/operator'
import { useControlPlane } from './hooks/useControlPlane'

type Props = { controlPlane: ReturnType<typeof useControlPlane> }

function jobStatusColor(status: string) {
  if (status === 'succeeded') return 'green'
  if (status === 'failed') return 'red'
  if (status === 'interrupted') return 'yellow'
  if (status === 'cancelled') return 'gray'
  return 'brand'
}

export function TransfersPage({ controlPlane }: Props) {
  const { development, state, request, snapshot } = controlPlane
  const [roots, setRoots] = useState<RootItem[]>(
    development ? developmentRoots : [],
  )
  const [jobs, setJobs] = useState<JobItem[]>(
    development ? developmentJobs : [],
  )
  const [root, setRoot] = useState(development ? 'comfyui' : '')
  const [path, setPath] = useState('models/example.bin')
  const [url, setUrl] = useState('')
  const [sha256, setSha256] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canEdit = snapshot?.accessLevel !== 'inspect'

  const refresh = useCallback(async () => {
    if (development || state !== 'ready') return
    try {
      const [rootResult, jobResult] = await Promise.all([
        request<{ items: RootItem[] }>('/cuicommander/v1/discover', {
          method: 'POST',
          body: JSON.stringify({ kind: 'roots', limit: 500 }),
        }),
        request<{ items: JobItem[] }>('/cuicommander/v1/jobs?limit=100'),
      ])
      setRoots(rootResult.items)
      setJobs(jobResult.items)
      if (!root && rootResult.items[0]) setRoot(rootResult.items[0].id)
      setError(null)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not load transfers.',
      )
    }
  }, [development, request, root, state])

  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0)
    if (development) return () => window.clearTimeout(initial)
    const active = jobs.some(
      (job) =>
        !['succeeded', 'failed', 'cancelled', 'interrupted'].includes(
          job.status,
        ),
    )
    if (!active) return
    const timer = window.setInterval(() => void refresh(), 2000)
    return () => {
      window.clearTimeout(initial)
      window.clearInterval(timer)
    }
  }, [development, jobs, refresh])

  const rootOptions = useMemo(
    () =>
      roots.map((item) => ({
        value: item.id,
        label: `${item.label} (${item.id})`,
      })),
    [roots],
  )

  const start = async () => {
    if (!root || !path.trim() || !url.trim()) return
    setBusy(true)
    setError(null)
    try {
      await request('/cuicommander/v1/downloads', {
        method: 'POST',
        body: JSON.stringify({
          root,
          path: path.trim(),
          url: url.trim(),
          ...(sha256.trim() ? { expectedSha256: sha256.trim() } : {}),
        }),
      })
      setUrl('')
      setSha256('')
      await refresh()
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Download could not start.',
      )
    } finally {
      setBusy(false)
    }
  }

  const cancel = async (job: JobItem) => {
    if (!window.confirm(`Cancel ${job.path ?? job.id}?`)) return
    try {
      await request(`/cuicommander/v1/jobs/${job.id}/cancel`, {
        method: 'POST',
        body: JSON.stringify({ confirmed: true }),
      })
      await refresh()
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : 'Cancel failed.',
      )
    }
  }

  return (
    <Stack gap="xl">
      <PageHeader
        title="Transfers & jobs"
        description="Stream public HTTP(S) assets into discovered ComfyUI roots and inspect durable job state."
        actions={
          <Button variant="light" onClick={() => void refresh()}>
            Refresh
          </Button>
        }
      />
      {error && <Alert color="red">{error}</Alert>}
      <Section
        title="New download"
        description="Downloads are bounded, resumeless, checksum-aware, and finalized atomically."
      >
        <Paper withBorder p="lg" className="cc-surface">
          <Stack gap="md">
            <Select
              label="Destination root"
              data={rootOptions}
              value={root}
              searchable
              onChange={(value) => setRoot(value ?? '')}
            />
            <TextInput
              label="Destination path"
              value={path}
              onChange={(event) => setPath(event.currentTarget.value)}
            />
            <TextInput
              label="Public HTTP(S) URL"
              placeholder="https://…"
              value={url}
              onChange={(event) => setUrl(event.currentTarget.value)}
            />
            <TextInput
              label="Expected SHA-256 (optional)"
              value={sha256}
              onChange={(event) => setSha256(event.currentTarget.value)}
            />
            <Group justify="flex-end">
              <Button
                loading={busy}
                disabled={!canEdit || !root || !path.trim() || !url.trim()}
                onClick={() => void start()}
              >
                Start download
              </Button>
            </Group>
            {!canEdit && (
              <Text size="sm" c="dimmed">
                Edit or Full access is required to start downloads.
              </Text>
            )}
          </Stack>
        </Paper>
      </Section>
      <Section
        title="Recent jobs"
        description="Running work is polled; incomplete work survives restart as interrupted state."
      >
        <Paper withBorder className="cc-surface">
          {jobs.length === 0 ? (
            <EmptyState
              title="No jobs yet"
              description="Downloads and other durable CUICommander work will appear here."
            />
          ) : (
            <Table.ScrollContainer minWidth={760}>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Kind</Table.Th>
                    <Table.Th>Target</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Progress</Table.Th>
                    <Table.Th>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {jobs.map((job) => {
                    const ratio =
                      job.totalBytes && job.totalBytes > 0
                        ? Math.min(
                            100,
                            (100 * (job.bytesReceived ?? 0)) / job.totalBytes,
                          )
                        : null
                    const active = ![
                      'succeeded',
                      'failed',
                      'cancelled',
                      'interrupted',
                    ].includes(job.status)
                    return (
                      <Table.Tr key={job.id}>
                        <Table.Td>{job.kind}</Table.Td>
                        <Table.Td>
                          <Text size="sm">
                            {job.path ?? job.source ?? job.id}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          <Badge
                            color={jobStatusColor(job.status)}
                            variant="light"
                          >
                            {job.status}
                          </Badge>
                        </Table.Td>
                        <Table.Td>
                          {ratio === null ? (
                            '—'
                          ) : (
                            <Progress
                              value={ratio}
                              w={140}
                              aria-label={`${Math.round(ratio)}% download progress`}
                            />
                          )}
                        </Table.Td>
                        <Table.Td>
                          <Button
                            size="xs"
                            variant="subtle"
                            color="red"
                            disabled={!active || !canEdit}
                            onClick={() => void cancel(job)}
                          >
                            Cancel
                          </Button>
                        </Table.Td>
                      </Table.Tr>
                    )
                  })}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          )}
        </Paper>
      </Section>
    </Stack>
  )
}
