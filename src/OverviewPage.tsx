import { useState, type FormEvent } from 'react'
import {
  Alert,
  Badge,
  Button,
  Code,
  CopyButton,
  Group,
  Paper,
  PasswordInput,
  SimpleGrid,
  Stack,
  Table,
  Text,
} from '@mantine/core'
import { PageHeader } from './components/ui/PageHeader'
import { CustomGptSetup } from './components/CustomGptSetup'
import { Section } from './components/ui/Section'
import { useControlPlane } from './hooks/useControlPlane'

const accessLabels = {
  inspect: 'Inspect only',
  edit: 'Edit ComfyUI',
  full: 'Full control',
} as const

const accessTone = {
  read: 'gray',
  write: 'blue',
  full: 'dark',
} as const

export function OverviewPage() {
  const controlPlane = useControlPlane()
  const [credential, setCredential] = useState('')
  const snapshot = controlPlane.snapshot
  const submitConnection = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void controlPlane.connect(credential)
  }

  const statusLabel = snapshot
    ? snapshot.status === 'ready'
      ? 'Ready'
      : 'Runtime needed'
    : controlPlane.state === 'initializing'
      ? 'Initializing'
      : controlPlane.state === 'connecting'
        ? 'Connecting'
        : 'Authentication required'

  return (
    <Stack gap="xl">
      <PageHeader
        title="CUICommander"
        description="Universal ChatGPT control plane for this ComfyUI instance."
        actions={
          <Group gap="xs">
            {snapshot && (
              <Badge variant="outline">
                {accessLabels[snapshot.accessLevel]}
              </Badge>
            )}
            <Badge
              color={
                snapshot?.status === 'ready'
                  ? 'green'
                  : controlPlane.state === 'error'
                    ? 'red'
                    : 'yellow'
              }
            >
              {statusLabel}
            </Badge>
          </Group>
        }
      />

      <Section
        title="Connection"
        description="One compact Action contract sits above the live ComfyUI runtime instead of one Action per node or model type."
      >
        <Paper withBorder p="lg">
          {!snapshot &&
          !import.meta.env.DEV &&
          controlPlane.state === 'initializing' ? (
            <Stack gap="xs">
              <Text fw={600}>Checking local setup</Text>
              <Text c="dimmed" size="sm">
                Detecting the local CUICommander configuration and restoring a
                browser-session connection when available.
              </Text>
            </Stack>
          ) : !snapshot && !import.meta.env.DEV ? (
            <form onSubmit={submitConnection}>
              <Stack gap="md">
                <Stack gap={4} maw={720}>
                  <Text fw={600}>Connect this browser session</Text>
                  <Text c="dimmed" size="sm">
                    Enter the configured CUICommander access key. It stays in
                    this browser session and is not written into the project or
                    bundled UI.
                  </Text>
                </Stack>
                {controlPlane.error && (
                  <Alert color="red" title="Connection failed">
                    {controlPlane.error}
                  </Alert>
                )}
                <PasswordInput
                  label="Access key"
                  value={credential}
                  onChange={(event) => setCredential(event.currentTarget.value)}
                  autoComplete="off"
                  maw={560}
                />
                <Group justify="space-between" align="flex-end" wrap="wrap">
                  <Stack gap={4}>
                    <Text size="xs" c="dimmed">
                      OpenAPI schema
                    </Text>
                    <Code>{controlPlane.schemaUrl}</Code>
                  </Stack>
                  <Button
                    type="submit"
                    loading={controlPlane.state === 'connecting'}
                  >
                    Connect
                  </Button>
                </Group>
              </Stack>
            </form>
          ) : (
            <Stack gap="md">
              <Group justify="space-between" align="flex-start" wrap="wrap">
                <Stack gap={4} maw={720}>
                  <Text fw={600}>Custom GPT Action endpoint</Text>
                  <Text c="dimmed" size="sm">
                    Expose this authenticated ComfyUI endpoint through your
                    chosen HTTPS edge, then use the schema URL in Custom GPT
                    Actions.
                  </Text>
                </Stack>
                <Group gap="xs">
                  <CopyButton value={controlPlane.schemaUrl}>
                    {({ copied, copy }) => (
                      <Button variant="default" onClick={copy}>
                        {copied ? 'Copied' : 'Copy schema URL'}
                      </Button>
                    )}
                  </CopyButton>
                  {controlPlane.state === 'ready' && (
                    <Button variant="subtle" onClick={controlPlane.disconnect}>
                      Disconnect
                    </Button>
                  )}
                </Group>
              </Group>
              <Code block>{controlPlane.schemaUrl}</Code>
              {snapshot && (
                <Text c="dimmed" size="xs">
                  CUICommander {snapshot.version} | ComfyUI{' '}
                  {snapshot.comfyVersion}
                </Text>
              )}
            </Stack>
          )}
        </Paper>
      </Section>

      {snapshot && (
        <>
          <CustomGptSetup
            setup={controlPlane.localSetup}
            busy={controlPlane.setupBusy}
            error={controlPlane.setupError}
            remote={controlPlane.remoteAccess}
            remoteBusy={controlPlane.remoteBusy}
            remoteError={controlPlane.remoteError}
            onUpdate={controlPlane.applyLocalSetup}
            onRotateAccessKey={controlPlane.rotateAccessKey}
            onRefreshRemoteAccess={controlPlane.refreshRemoteAccess}
            onEnableRemoteAccess={controlPlane.enableRemoteAccess}
            onDisableRemoteAccess={controlPlane.disableRemoteAccess}
          />
          <Section
            title="Universal control model"
            description="The stable machine vocabulary stays the same even when ComfyUI, models, or custom nodes change."
          >
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
              {snapshot.capabilities.map((capability) => (
                <Paper withBorder p="lg" key={capability.title}>
                  <Stack gap="xs">
                    <Group
                      justify="space-between"
                      align="flex-start"
                      wrap="nowrap"
                    >
                      <Text fw={600}>{capability.title}</Text>
                      <Badge
                        color={accessTone[capability.access]}
                        variant="light"
                      >
                        {capability.access}
                      </Badge>
                    </Group>
                    <Text c="dimmed" size="sm">
                      {capability.description}
                    </Text>
                  </Stack>
                </Paper>
              ))}
            </SimpleGrid>
          </Section>

          <Section
            title="Filesystem reach"
            description={`The live runtime reports ${snapshot.rootCount} managed roots. Showing ${snapshot.roots.length} representative roots from ComfyUI and folder_paths.`}
          >
            <Paper withBorder visibleFrom="sm">
              <Table verticalSpacing="sm" horizontalSpacing="md">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Root</Table.Th>
                    <Table.Th>Source</Table.Th>
                    <Table.Th>Path</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {snapshot.roots.map((root) => (
                    <Table.Tr key={root.id}>
                      <Table.Td>
                        <Stack gap={2}>
                          <Text fw={600} size="sm">
                            {root.label}
                          </Text>
                          <Code>{root.id}</Code>
                        </Stack>
                      </Table.Td>
                      <Table.Td>
                        <Badge variant="outline">{root.source}</Badge>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" c="dimmed">
                          {root.detail}
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Paper>
            <Stack hiddenFrom="sm" gap="sm">
              {snapshot.roots.map((root) => (
                <Paper withBorder p="md" key={root.id}>
                  <Stack gap="xs">
                    <Group
                      justify="space-between"
                      align="flex-start"
                      wrap="nowrap"
                    >
                      <Stack gap={2}>
                        <Text fw={600} size="sm">
                          {root.label}
                        </Text>
                        <Code>{root.id}</Code>
                      </Stack>
                      <Badge variant="outline">{root.source}</Badge>
                    </Group>
                    <Text size="sm" c="dimmed">
                      {root.detail}
                    </Text>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </Section>
          <Section
            title="Access model"
            description="Risk changes the execution path and safeguards, not whether ComfyUI remains reachable."
          >
            <Paper withBorder p="lg">
              <Stack gap="md">
                <Group gap="xs" wrap="wrap">
                  <Badge variant="outline">Inspect only</Badge>
                  <Badge variant="outline">Edit ComfyUI</Badge>
                  <Badge variant="light" color="dark">
                    Full control
                  </Badge>
                </Group>
                <Text size="sm">
                  Full control still prefers the narrowest generic primitive
                  first: inspect current state, use CRUD or native ComfyUI
                  execution, then fall back only when those cannot express the
                  requested result.
                </Text>
                <Text c="dimmed" size="sm">
                  No checkpoint adapter. No LoRA adapter. No custom-node-suite
                  adapter. New ComfyUI capabilities are discovered from the
                  running source/runtime and compile down to the same control
                  primitives.
                </Text>
              </Stack>
            </Paper>
          </Section>
        </>
      )}
    </Stack>
  )
}
