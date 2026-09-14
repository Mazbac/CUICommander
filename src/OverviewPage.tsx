import {
  Badge,
  Button,
  Code,
  CopyButton,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
} from '@mantine/core'
import { PageHeader } from './components/ui/PageHeader'
import { Section } from './components/ui/Section'
import { developmentControlPlane } from './data/controlPlane'

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
  const snapshot = developmentControlPlane

  return (
    <Stack gap="xl">
      <PageHeader
        title="CUICommander"
        description="Universal ChatGPT control plane for this ComfyUI instance."
        actions={
          <Group gap="xs">
            <Badge variant="outline">
              {accessLabels[snapshot.accessLevel]}
            </Badge>
            <Badge color={snapshot.status === 'ready' ? 'green' : 'yellow'}>
              {snapshot.status === 'ready' ? 'Ready' : 'Runtime needed'}
            </Badge>
          </Group>
        }
      />

      <Section
        title="Connection"
        description="One compact Action contract sits above the live ComfyUI runtime instead of one Action per node or model type."
      >
        <Paper withBorder p="lg">
          <Stack gap="md">
            <Group justify="space-between" align="flex-start" wrap="wrap">
              <Stack gap={4} maw={720}>
                <Text fw={600}>Custom GPT Action endpoint</Text>
                <Text c="dimmed" size="sm">
                  Install CUICommander under ComfyUI custom_nodes, restart
                  ComfyUI, then expose the authenticated endpoint through your
                  chosen HTTPS edge for Custom GPT Actions.
                </Text>
              </Stack>
              <CopyButton value={snapshot.schemaUrl}>
                {({ copied, copy }) => (
                  <Button variant="default" onClick={copy}>
                    {copied ? 'Copied' : 'Copy schema URL'}
                  </Button>
                )}
              </CopyButton>
            </Group>
            <Code block>{snapshot.schemaUrl}</Code>
            <Text c="dimmed" size="xs">
              CUICommander {snapshot.version} | ComfyUI {snapshot.comfyVersion}
            </Text>
          </Stack>
        </Paper>
      </Section>

      <Section
        title="Universal control model"
        description="The stable machine vocabulary stays the same even when ComfyUI, models, or custom nodes change."
      >
        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
          {snapshot.capabilities.map((capability) => (
            <Paper withBorder p="lg" key={capability.title}>
              <Stack gap="xs">
                <Group justify="space-between" align="flex-start" wrap="nowrap">
                  <Text fw={600}>{capability.title}</Text>
                  <Badge color={accessTone[capability.access]} variant="light">
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
        description="The complete ComfyUI tree is a first-class root, and extra registered paths are discovered from the running process."
      >
        <Paper withBorder visibleFrom="sm">
          <Table verticalSpacing="sm" horizontalSpacing="md">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Root</Table.Th>
                <Table.Th>Source</Table.Th>
                <Table.Th>What it means</Table.Th>
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
                <Group justify="space-between" align="flex-start" wrap="nowrap">
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
              Full control still prefers the narrowest generic primitive first:
              inspect current state, use CRUD or native ComfyUI execution, then
              fall back only when those cannot express the requested result.
            </Text>
            <Text c="dimmed" size="sm">
              No checkpoint adapter. No LoRA adapter. No custom-node-suite
              adapter. New ComfyUI capabilities are discovered from the running
              source/runtime and compile down to the same control primitives.
            </Text>
          </Stack>
        </Paper>
      </Section>
    </Stack>
  )
}
