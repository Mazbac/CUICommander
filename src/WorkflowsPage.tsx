import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Code,
  Group,
  Paper,
  Select,
  Stack,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core'
import { PageHeader } from './components/ui/PageHeader'
import { Section } from './components/ui/Section'
import {
  developmentRoots,
  type NativeResult,
  type ResourceChunk,
  type ResourceInfo,
  type RootItem,
} from './data/operator'
import { useControlPlane } from './hooks/useControlPlane'

type Props = { controlPlane: ReturnType<typeof useControlPlane> }

const starterPrompt = JSON.stringify(
  {
    '1': {
      class_type: 'EmptyLatentImage',
      inputs: { width: 512, height: 512, batch_size: 1 },
    },
  },
  null,
  2,
)
export function WorkflowsPage({ controlPlane }: Props) {
  const { development, state, request, snapshot } = controlPlane
  const [roots, setRoots] = useState<RootItem[]>(
    development ? developmentRoots : [],
  )
  const [root, setRoot] = useState(development ? 'user' : '')
  const [path, setPath] = useState('default/workflows/cuicommander-prompt.json')
  const [editor, setEditor] = useState(starterPrompt)
  const [loaded, setLoaded] = useState<ResourceInfo | null>(null)
  const [queueResult, setQueueResult] = useState<NativeResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canEdit = snapshot?.accessLevel !== 'inspect'
  const full = snapshot?.accessLevel === 'full'

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
            const preferred = discovered.items.find(
              (item) => item.id === 'user',
            )
            if (preferred) setRoot(preferred.id)
          } catch (requestError) {
            setError(
              requestError instanceof Error
                ? requestError.message
                : 'Could not discover roots.',
            )
          }
        })(),
      0,
    )
    return () => window.clearTimeout(timer)
  }, [development, request, state])

  const rootOptions = useMemo(
    () =>
      roots.map((item) => ({
        value: item.id,
        label: `${item.label} (${item.id})`,
      })),
    [roots],
  )
  const parsedPrompt = () => {
    const value = JSON.parse(editor) as unknown
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      throw new Error('Prompt JSON must be an object keyed by node id.')
    }
    return value as Record<string, unknown>
  }

  const load = async () => {
    if (!root || !path.trim()) return
    setBusy(true)
    setError(null)
    try {
      const result = await request<ResourceInfo>(
        '/cuicommander/v1/resources/inspect',
        {
          method: 'POST',
          body: JSON.stringify({ root, path: path.trim() }),
        },
      )
      if (result.type !== 'file') {
        throw new Error('Workflow path must be a UTF-8 JSON file.')
      }

      let content = ''
      if (!result.previewTruncated && result.previewEncoding === 'utf-8') {
        content = String(result.preview ?? '')
      } else {
        let offset = 0
        const chunks: string[] = []
        while (true) {
          const chunk = await request<ResourceChunk>(
            '/cuicommander/v1/resources/read',
            {
              method: 'POST',
              body: JSON.stringify({
                root,
                path: path.trim(),
                offset,
                maxBytes: 131072,
                encoding: 'utf-8',
                expectedFingerprint: result.fingerprint,
              }),
            },
          )
          if (chunk.fingerprint !== result.fingerprint) {
            throw new Error(
              'Workflow changed while it was being read. Load it again.',
            )
          }
          chunks.push(chunk.content ?? '')
          if (chunk.eof) break
          if (chunk.nextOffset === null || chunk.nextOffset <= offset) {
            throw new Error('Workflow read did not make forward progress.')
          }
          offset = chunk.nextOffset
        }
        content = chunks.join('')
      }

      setLoaded(result)
      setEditor(content)
    } catch (requestError) {
      setLoaded(null)
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Workflow load failed.',
      )
    } finally {
      setBusy(false)
    }
  }

  const save = async () => {
    if (!root || !path.trim()) return
    setBusy(true)
    setError(null)
    try {
      parsedPrompt()
      let result: ResourceInfo
      if (loaded && loaded.root === root && loaded.path === path.trim()) {
        result = await request<ResourceInfo>(
          '/cuicommander/v1/resources/update',
          {
            method: 'POST',
            body: JSON.stringify({
              root,
              path: path.trim(),
              expectedFingerprint: loaded.fingerprint,
              content: editor,
            }),
          },
        )
      } else {
        result = await request<ResourceInfo>(
          '/cuicommander/v1/resources/create',
          {
            method: 'POST',
            body: JSON.stringify({
              root,
              path: path.trim(),
              type: 'file',
              parents: true,
              content: editor,
            }),
          },
        )
      }
      setLoaded(result)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Workflow save failed.',
      )
    } finally {
      setBusy(false)
    }
  }
  const queue = async () => {
    setBusy(true)
    setError(null)
    try {
      const prompt = parsedPrompt()
      const result = await request<NativeResult>('/cuicommander/v1/execute', {
        method: 'POST',
        body: JSON.stringify({
          method: 'POST',
          route: '/prompt',
          body: { prompt },
          confirmed: true,
        }),
      })
      setQueueResult(result)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Workflow queue failed.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <Stack gap="xl">
      <PageHeader
        title="Workflows"
        description="Author, save, and queue ComfyUI API prompt graphs without model- or node-pack-specific adapters."
        actions={
          <Group gap="xs">
            <Badge variant="outline">
              {canEdit ? 'Save enabled' : 'Read only'}
            </Badge>
            <Badge variant="outline">
              {full ? 'Queue enabled' : 'Full control required to queue'}
            </Badge>
          </Group>
        }
      />
      {error && <Alert color="red">{error}</Alert>}
      <Section
        title="Prompt graph"
        description="This editor uses ComfyUI's API-format prompt object: node ids mapped to class_type and inputs. Discover node INPUT_TYPES in Runtime when composing unknown nodes."
      >
        <Paper withBorder p="lg" className="cc-surface">
          <Stack gap="md">
            <Group align="end" wrap="wrap">
              <Select
                label="Storage root"
                data={rootOptions}
                value={root}
                searchable
                onChange={(value) => {
                  setRoot(value ?? '')
                  setLoaded(null)
                }}
                miw={260}
              />
              <TextInput
                label="Workflow JSON path"
                value={path}
                onChange={(event) => {
                  setPath(event.currentTarget.value)
                  setLoaded(null)
                }}
                flex={1}
              />
              <Button
                variant="light"
                loading={busy}
                onClick={() => void load()}
              >
                Load
              </Button>
            </Group>{' '}
            <Textarea
              label="API prompt JSON"
              minRows={18}
              autosize
              maxRows={36}
              value={editor}
              onChange={(event) => setEditor(event.currentTarget.value)}
              classNames={{ input: 'cc-mono' }}
            />
            <Group justify="space-between" wrap="wrap">
              <Text size="xs" c="dimmed">
                {loaded
                  ? `Loaded with ${loaded.fingerprintMode} fingerprint protection.`
                  : 'Not loaded from disk; Save creates a new file.'}
              </Text>
              <Group gap="xs">
                <Button
                  variant="default"
                  loading={busy}
                  disabled={!canEdit || !root || !path.trim()}
                  onClick={() => void save()}
                >
                  Save JSON
                </Button>
                <Button
                  loading={busy}
                  disabled={!full}
                  onClick={() => void queue()}
                >
                  Queue in ComfyUI
                </Button>
              </Group>
            </Group>
          </Stack>
        </Paper>
      </Section>

      {queueResult && (
        <Section title="Last queue response">
          <Paper withBorder p="lg" className="cc-surface">
            <Stack gap="xs">
              <Text fw={600}>HTTP {queueResult.status}</Text>
              <Code block>{JSON.stringify(queueResult.body, null, 2)}</Code>
            </Stack>
          </Paper>
        </Section>
      )}
    </Stack>
  )
}
