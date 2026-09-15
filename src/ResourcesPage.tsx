import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Code,
  Group,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core'
import { PageHeader } from './components/ui/PageHeader'
import { Section } from './components/ui/Section'
import {
  developmentResource,
  developmentRoots,
  type ResourceInfo,
  type RootItem,
} from './data/operator'
import { useControlPlane } from './hooks/useControlPlane'

type Props = { controlPlane: ReturnType<typeof useControlPlane> }

function joinPath(base: string, name: string) {
  return [base.replace(/\/$/, ''), name].filter(Boolean).join('/')
}

export function ResourcesPage({ controlPlane }: Props) {
  const { development, state, request, snapshot } = controlPlane
  const [roots, setRoots] = useState<RootItem[]>(
    development ? developmentRoots : [],
  )
  const [root, setRoot] = useState(development ? 'user' : '')
  const [path, setPath] = useState(
    controlPlane.development ? 'default/workflows' : '',
  )
  const [resource, setResource] = useState<ResourceInfo | null>(
    development ? developmentResource : null,
  )
  const [editor, setEditor] = useState('')
  const [newPath, setNewPath] = useState('')
  const [newType, setNewType] = useState<'file' | 'directory'>('file')
  const [movePath, setMovePath] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canEdit = snapshot?.accessLevel !== 'inspect'

  const inspect = useCallback(
    async (nextRoot = root, nextPath = path) => {
      if (development) return
      if (!nextRoot) return
      setBusy(true)
      setError(null)
      try {
        const result = await request<ResourceInfo>(
          '/cuicommander/v1/resources/inspect',
          {
            method: 'POST',
            body: JSON.stringify({ root: nextRoot, path: nextPath }),
          },
        )
        setResource(result)
        setRoot(nextRoot)
        setPath(nextPath)
        setEditor(
          result.previewEncoding === 'utf-8' &&
            typeof result.preview === 'string'
            ? result.preview
            : '',
        )
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : 'Inspect failed.',
        )
      } finally {
        setBusy(false)
      }
    },
    [development, path, request, root],
  )

  useEffect(() => {
    if (development || state !== 'ready') return
    const timer = window.setTimeout(
      () =>
        void (async () => {
          try {
            const discovered = await request<{ items: RootItem[] }>(
              '/cuicommander/v1/discover',
              {
                method: 'POST',
                body: JSON.stringify({ kind: 'roots', limit: 500 }),
              },
            )
            setRoots(discovered.items)
            const preferred =
              discovered.items.find((item) => item.id === 'user') ??
              discovered.items[0]
            if (preferred) await inspect(preferred.id, '')
          } catch (requestError) {
            setError(
              requestError instanceof Error
                ? requestError.message
                : 'Could not load roots.',
            )
          }
        })(),
      0,
    )
    return () => window.clearTimeout(timer)
  }, [development, inspect, request, state])

  const rootOptions = useMemo(
    () =>
      roots.map((item) => ({
        value: item.id,
        label: `${item.label} (${item.id})`,
      })),
    [roots],
  )

  const create = async () => {
    if (!newPath.trim()) return
    setBusy(true)
    setError(null)
    try {
      const result = await request<ResourceInfo>(
        '/cuicommander/v1/resources/create',
        {
          method: 'POST',
          body: JSON.stringify({
            root,
            path: newPath.trim(),
            type: newType,
            parents: true,
            ...(newType === 'file' ? { content: '' } : {}),
          }),
        },
      )
      setNewPath('')
      await inspect(root, resource?.type === 'directory' ? path : '')
      if (result.type === 'file') setResource(result)
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : 'Create failed.',
      )
    } finally {
      setBusy(false)
    }
  }

  const save = async () => {
    if (!resource || resource.type !== 'file') return
    setBusy(true)
    setError(null)
    try {
      const result = await request<ResourceInfo>(
        '/cuicommander/v1/resources/update',
        {
          method: 'POST',
          body: JSON.stringify({
            root: resource.root,
            path: resource.path,
            expectedFingerprint: resource.fingerprint,
            content: editor,
          }),
        },
      )
      setResource(result)
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : 'Save failed.',
      )
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    if (!resource || !resource.path) return
    if (!window.confirm(`Delete ${resource.path}?`)) return
    setBusy(true)
    try {
      await request('/cuicommander/v1/resources/delete', {
        method: 'POST',
        body: JSON.stringify({
          root: resource.root,
          path: resource.path,
          expectedFingerprint: resource.fingerprint,
          recursive: resource.type === 'directory',
          confirmed: true,
        }),
      })
      const parent = resource.path.split('/').slice(0, -1).join('/')
      await inspect(root, parent)
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : 'Delete failed.',
      )
    } finally {
      setBusy(false)
    }
  }

  const move = async () => {
    if (!resource || !resource.path || !movePath.trim()) return
    setBusy(true)
    try {
      const result = await request<ResourceInfo>(
        '/cuicommander/v1/resources/move',
        {
          method: 'POST',
          body: JSON.stringify({
            root: resource.root,
            path: resource.path,
            targetRoot: resource.root,
            targetPath: movePath.trim(),
            expectedFingerprint: resource.fingerprint,
          }),
        },
      )
      setMovePath('')
      setPath(result.path)
      setResource(result)
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : 'Move failed.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <Stack gap="xl">
      <PageHeader
        title="Resources"
        description="Browse and manage every ComfyUI-owned or registered filesystem root."
        actions={
          <Badge variant="outline">
            {canEdit ? 'Edit enabled' : 'Inspect only'}
          </Badge>
        }
      />
      {error && <Alert color="red">{error}</Alert>}
      <Section
        title="Browse"
        description="Inspect first; mutations use the returned fingerprint."
      >
        <Paper withBorder p="lg">
          <Stack gap="md">
            <SimpleGrid cols={{ base: 1, md: 2 }}>
              <Select
                label="Root"
                data={rootOptions}
                value={root}
                searchable
                onChange={(value) => value && void inspect(value, '')}
              />
              <TextInput
                label="Relative path"
                value={path}
                onChange={(event) => setPath(event.currentTarget.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') void inspect()
                }}
              />
            </SimpleGrid>
            <Group justify="flex-end">
              <Button
                variant="default"
                loading={busy}
                onClick={() => void inspect()}
              >
                Inspect
              </Button>
            </Group>
          </Stack>
        </Paper>
        {resource && (
          <Paper withBorder p="lg">
            <Stack gap="md">
              <Group justify="space-between" align="flex-start" wrap="wrap">
                <Stack gap={4}>
                  <Text fw={600}>{resource.name || resource.root}</Text>
                  <Code>{resource.path || '/'}</Code>
                </Stack>
                <Group gap="xs">
                  <Badge variant="light">{resource.type}</Badge>
                  <Badge variant="outline">{resource.fingerprintMode}</Badge>
                </Group>
              </Group>
              {resource.type === 'directory' && (
                <Table.ScrollContainer minWidth={620}>
                  <Table striped highlightOnHover>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Name</Table.Th>
                        <Table.Th>Type</Table.Th>
                        <Table.Th>Size</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {(resource.items ?? []).map((item) => (
                        <Table.Tr
                          key={item.name}
                          onClick={() =>
                            void inspect(root, joinPath(path, item.name))
                          }
                        >
                          <Table.Td>{item.name}</Table.Td>
                          <Table.Td>{item.type}</Table.Td>
                          <Table.Td>{item.size ?? '—'}</Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </Table.ScrollContainer>
              )}
              {resource.type === 'file' &&
                resource.previewEncoding === 'utf-8' && (
                  <Textarea
                    label="UTF-8 content"
                    value={editor}
                    onChange={(event) => setEditor(event.currentTarget.value)}
                    autosize
                    minRows={8}
                    maxRows={24}
                    readOnly={!canEdit}
                  />
                )}
              {resource.type === 'file' &&
                resource.previewEncoding === 'base64' && (
                  <Alert>
                    Binary preview is available through the API but is not
                    edited as text here.
                  </Alert>
                )}
              {resource.previewTruncated && (
                <Alert color="yellow">
                  This file is larger than the bounded preview limit.
                </Alert>
              )}
              {canEdit &&
                resource.type === 'file' &&
                resource.previewEncoding === 'utf-8' && (
                  <Group justify="flex-end">
                    <Button loading={busy} onClick={() => void save()}>
                      Save with fresh fingerprint
                    </Button>
                  </Group>
                )}
            </Stack>
          </Paper>
        )}
      </Section>

      {canEdit && (
        <Section
          title="Mutations"
          description="Create, move, or delete within the selected discovered root."
        >
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            <Paper withBorder p="lg">
              <Stack gap="sm">
                <Text fw={600}>Create</Text>
                <TextInput
                  label="Target path"
                  value={newPath}
                  onChange={(e) => setNewPath(e.currentTarget.value)}
                />
                <Select
                  label="Type"
                  value={newType}
                  data={[
                    { value: 'file', label: 'File' },
                    { value: 'directory', label: 'Directory' },
                  ]}
                  onChange={(value) =>
                    setNewType(value === 'directory' ? 'directory' : 'file')
                  }
                />
                <Button
                  loading={busy}
                  disabled={!newPath.trim()}
                  onClick={() => void create()}
                >
                  Create
                </Button>
              </Stack>
            </Paper>
            <Paper withBorder p="lg">
              <Stack gap="sm">
                <Text fw={600}>Selected resource</Text>
                <Text size="sm" c="dimmed">
                  Move or delete the currently inspected non-root resource.
                </Text>
                <TextInput
                  label="Move to path"
                  value={movePath}
                  onChange={(event) => setMovePath(event.currentTarget.value)}
                  disabled={!resource?.path}
                />
                <Group justify="space-between">
                  <Button
                    variant="default"
                    loading={busy}
                    disabled={!resource?.path || !movePath.trim()}
                    onClick={() => void move()}
                  >
                    Move
                  </Button>
                  <Button
                    color="red"
                    variant="outline"
                    loading={busy}
                    disabled={!resource?.path}
                    onClick={() => void remove()}
                  >
                    Delete
                  </Button>
                </Group>
              </Stack>
            </Paper>
          </SimpleGrid>
        </Section>
      )}
    </Stack>
  )
}
