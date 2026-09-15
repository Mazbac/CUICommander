import { useRef, useState } from 'react'
import {
  Accordion,
  Alert,
  Badge,
  Button,
  Code,
  CopyButton,
  Divider,
  Group,
  List,
  Paper,
  PasswordInput,
  Select,
  Stack,
  Text,
  TextInput,
  Textarea,
} from '@mantine/core'
import { Section } from './ui/Section'
import type { AccessLevel } from '../data/controlPlane'
import type { LocalSetupState, LocalSetupUpdate } from '../data/gptSetup'
import type { RemoteAccessState } from '../data/remoteAccess'

type CustomGptSetupProps = {
  setup: LocalSetupState | null
  busy: boolean
  error: string | null
  remote: RemoteAccessState | null
  remoteBusy: boolean
  remoteError: string | null
  onUpdate: (update: LocalSetupUpdate) => Promise<void>
  onRotateAccessKey: () => Promise<void>
  onRefreshRemoteAccess: () => Promise<void>
  onPrepareRemoteAccess: () => Promise<void>
  onEnableRemoteAccess: () => Promise<void>
  onDisableRemoteAccess: () => Promise<void>
}

const accessOptions = [
  { value: 'inspect', label: 'Inspect only' },
  { value: 'edit', label: 'Edit ComfyUI files' },
  { value: 'full', label: 'Full ComfyUI control' },
]

function StepLabel({
  number,
  title,
  description,
  complete,
}: {
  number: string
  title: string
  description: string
  complete: boolean
}) {
  return (
    <Group
      justify="space-between"
      gap="sm"
      wrap="nowrap"
      pr="xs"
      align="flex-start"
    >
      <Group gap="sm" wrap="nowrap" flex={1} miw={0}>
        <Badge variant="light" color={complete ? 'green' : 'brand'}>
          {number}
        </Badge>
        <Stack gap={0} miw={0}>
          <Text fw={650}>{title}</Text>
          <Text size="xs" c="dimmed">
            {description}
          </Text>
        </Stack>
      </Group>
      <Badge
        color={complete ? 'green' : 'gray'}
        variant="light"
        visibleFrom="sm"
      >
        {complete ? 'Ready' : 'To do'}
      </Badge>
    </Group>
  )
}

export function CustomGptSetup({
  setup,
  busy,
  error,
  remote,
  remoteBusy,
  remoteError,
  onUpdate,
  onRotateAccessKey,
  onRefreshRemoteAccess,
  onPrepareRemoteAccess,
  onEnableRemoteAccess,
  onDisableRemoteAccess,
}: CustomGptSetupProps) {
  const endpointRef = useRef<HTMLInputElement>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showSchema, setShowSchema] = useState(false)
  const fullControl = setup?.accessLevel === 'full'
  const remoteReady = Boolean(setup?.readiness.customGptOrigin)
  const [openedStep, setOpenedStep] = useState<string | null>(
    !fullControl ? 'access' : !remoteReady ? 'remote' : 'chatgpt',
  )

  if (!setup) {
    return (
      <Section
        title="Connect ChatGPT"
        description="Complete setup locally before exposing the authenticated Action API."
      >
        <Alert title="Setup is only available on this ComfyUI machine">
          Open CUICommander through localhost to manage access, remote
          connectivity, and the Action credential.
        </Alert>
      </Section>
    )
  }

  const saveEndpoint = async () => {
    const normalized = (endpointRef.current?.value ?? '')
      .trim()
      .replace(/\/$/, '')
    await onUpdate({ publicBaseUrl: normalized })
  }

  const updateAccess = (value: string | null) => {
    if (!value) return
    void (async () => {
      await onUpdate({ accessLevel: value as AccessLevel })
      if (value === 'full') {
        setOpenedStep(remoteReady ? 'chatgpt' : 'remote')
      }
    })()
  }

  const enableRemoteAccess = () => {
    void (async () => {
      await onEnableRemoteAccess()
      setOpenedStep('chatgpt')
    })()
  }

  return (
    <Section
      title="Connect ChatGPT"
      description="Three guided steps take this ComfyUI instance from local-only to a working Custom GPT connection."
    >
      <Stack gap="md">
        <Paper withBorder p={{ base: 'md', sm: 'lg' }} className="cc-surface">
          <Group justify="space-between" align="center" wrap="wrap" gap="md">
            <Stack gap={2}>
              <Text fw={700}>Connection readiness</Text>
              <Text size="sm" c="dimmed">
                {setup.readiness.readyForCustomGPT
                  ? 'The local prerequisites are complete. Copy the connection details into ChatGPT.'
                  : 'Finish the highlighted setup steps below.'}
              </Text>
            </Stack>
            <Group gap="xs" wrap="wrap">
              <Badge color={fullControl ? 'green' : 'gray'} variant="light">
                {fullControl ? 'Full control ready' : 'Choose access'}
              </Badge>
              <Badge color={remoteReady ? 'green' : 'gray'} variant="light">
                {remoteReady ? 'HTTPS 443 ready' : 'Remote access needed'}
              </Badge>
              <Badge
                color={setup.readiness.readyForCustomGPT ? 'green' : 'yellow'}
              >
                {setup.readiness.readyForCustomGPT
                  ? 'Ready for Custom GPT'
                  : 'Setup incomplete'}
              </Badge>
            </Group>
          </Group>
        </Paper>

        {error && (
          <Alert color="red" title="Setup change failed">
            {error}
          </Alert>
        )}

        <Accordion
          value={openedStep}
          onChange={setOpenedStep}
          variant="separated"
          radius="md"
          transitionDuration={0}
        >
          <Accordion.Item
            value="access"
            className="cc-step-card"
            data-complete={fullControl}
          >
            <Accordion.Control>
              <StepLabel
                number="1"
                title="Choose control access"
                description="Decide what the Custom GPT may do."
                complete={fullControl}
              />
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="md">
                <Select
                  label="Custom GPT access level"
                  description="Full control enables discovered native ComfyUI routes as well as file operations."
                  data={accessOptions}
                  value={setup.accessLevel}
                  onChange={updateAccess}
                  disabled={busy || setup.environmentOverrides.accessLevel}
                />
                {setup.environmentOverrides.accessLevel ? (
                  <Text size="xs" c="dimmed">
                    Controlled by the CUICOMMANDER_ACCESS environment variable.
                  </Text>
                ) : fullControl ? (
                  <Alert color="green" title="Full control enabled">
                    Discovery, managed files, downloads, workflows, and native
                    route execution are available with their existing
                    safeguards.
                  </Alert>
                ) : (
                  <Alert color="brand" title="Limited access selected">
                    Inspect and Edit are valid restricted modes. Choose Full
                    ComfyUI control when the GPT should also run workflows and
                    discovered native routes.
                  </Alert>
                )}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>

          <Accordion.Item
            value="remote"
            className="cc-step-card"
            data-complete={remoteReady}
          >
            <Accordion.Control>
              <StepLabel
                number="2"
                title="Create a secure remote endpoint"
                description="Use standard HTTPS 443 without exposing raw ComfyUI."
                complete={remoteReady}
              />
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="md">
                {remoteError && (
                  <Alert color="red" title="Remote access check failed">
                    {remoteError}
                  </Alert>
                )}

                {!remote ? (
                  <Alert title="Remote access unavailable">
                    Remote access can only be managed from the local ComfyUI
                    machine.
                  </Alert>
                ) : !remote.installed ? (
                  <Alert
                    className="cc-warning-alert"
                    color="yellow"
                    title="Install Tailscale once"
                  >
                    <Stack gap="sm">
                      <Text size="sm">
                        Install the free Tailscale client and sign in. Then
                        return here and refresh detection.
                      </Text>
                      <Group gap="xs">
                        <Button
                          component="a"
                          href="https://tailscale.com/download"
                          target="_blank"
                          rel="noreferrer"
                          variant="default"
                        >
                          Open Tailscale download
                        </Button>
                        <Button
                          variant="light"
                          onClick={() => void onRefreshRemoteAccess()}
                          loading={remoteBusy}
                        >
                          Refresh detection
                        </Button>
                      </Group>
                    </Stack>
                  </Alert>
                ) : !remote.connected ? (
                  <Alert
                    className="cc-warning-alert"
                    color="yellow"
                    title="Sign in to Tailscale"
                  >
                    <Stack gap="sm">
                      <Text size="sm">
                        Tailscale {remote.version || 'is installed'}, but this
                        PC is not connected to a tailnet yet.
                      </Text>
                      <Button
                        variant="light"
                        w="fit-content"
                        onClick={() => void onRefreshRemoteAccess()}
                        loading={remoteBusy}
                      >
                        Refresh detection
                      </Button>
                    </Stack>
                  </Alert>
                ) : remote.active ? (
                  <>
                    <Alert
                      className={
                        remote.customGptCompatible
                          ? undefined
                          : 'cc-warning-alert'
                      }
                      color={remote.customGptCompatible ? 'green' : 'yellow'}
                      title={
                        remote.customGptCompatible
                          ? 'Secure endpoint active'
                          : 'Legacy remote endpoint active'
                      }
                    >
                      {remote.customGptCompatible
                        ? 'The endpoint uses standard HTTPS 443 and reaches only the authenticated CUICommander Action API.'
                        : 'This endpoint is reachable, but Custom GPT Actions require standard HTTPS 443.'}
                    </Alert>
                    <Paper withBorder p="md" className="cc-surface">
                      <Group
                        justify="space-between"
                        align="center"
                        wrap="wrap"
                        gap="sm"
                      >
                        <Stack gap={3}>
                          <Text size="xs" c="dimmed">
                            Public Action endpoint
                          </Text>
                          <Code>{remote.publicBaseUrl}</Code>
                        </Stack>
                        <Group gap="xs">
                          {remote.mode === 'action-node' && (
                            <Badge variant="light" color="brand">
                              Isolated node
                            </Badge>
                          )}
                          <Badge color="green" variant="light">
                            HTTPS {remote.funnelPort}
                          </Badge>
                        </Group>
                      </Group>
                    </Paper>
                    <Group justify="space-between" wrap="wrap">
                      <Text size="xs" c="dimmed">
                        Existing Tailscale services remain unchanged.
                      </Text>
                      <Button
                        variant="subtle"
                        color="red"
                        loading={remoteBusy}
                        onClick={() => {
                          if (
                            window.confirm(
                              'Disable CUICommander remote access? Your Custom GPT will stop connecting until it is enabled again.',
                            )
                          ) {
                            void onDisableRemoteAccess()
                          }
                        }}
                      >
                        Disable remote access
                      </Button>
                    </Group>
                  </>
                ) : remote.systemPort443Available ? (
                  <Alert color="brand" title="Ready to create the endpoint">
                    <Stack gap="sm">
                      <Text size="sm">
                        CUICommander will use your current Tailscale device on
                        HTTPS 443 and publish only the isolated Action gateway.
                      </Text>
                      <Button
                        w="fit-content"
                        onClick={enableRemoteAccess}
                        loading={remoteBusy}
                      >
                        Enable Custom GPT access
                      </Button>
                    </Stack>
                  </Alert>
                ) : remote.actionNodeConnected ? (
                  <Alert color="brand" title="Isolated endpoint ready">
                    <Stack gap="sm">
                      <Text size="sm">
                        HTTPS 443 is already in use on your main Tailscale
                        device, so CUICommander will use{' '}
                        {remote.actionNodeDnsName} instead. Your existing
                        service stays untouched.
                      </Text>
                      <Button
                        w="fit-content"
                        onClick={enableRemoteAccess}
                        loading={remoteBusy}
                      >
                        Enable isolated Custom GPT access
                      </Button>
                    </Stack>
                  </Alert>
                ) : remote.actionNodeSupported ? (
                  <Alert color="brand" title="Create an isolated endpoint">
                    <Stack gap="sm">
                      <Text size="sm">
                        Your main Tailscale HTTPS 443 is already occupied.
                        CUICommander can create its own Tailscale Action node so
                        nothing existing is moved or exposed. Windows asks once
                        for administrator approval.
                      </Text>
                      <Group gap="xs" wrap="wrap">
                        <Button
                          onClick={() => void onPrepareRemoteAccess()}
                          loading={remoteBusy}
                        >
                          Set up isolated endpoint
                        </Button>
                        {remote.actionNodeLoginUrl && (
                          <Button
                            component="a"
                            href={remote.actionNodeLoginUrl}
                            target="_blank"
                            rel="noreferrer"
                            variant="default"
                          >
                            Sign in to Tailscale
                          </Button>
                        )}
                        <Button
                          variant="light"
                          onClick={() => void onRefreshRemoteAccess()}
                          loading={remoteBusy}
                        >
                          Refresh
                        </Button>
                      </Group>
                      {remote.actionNodeRunning &&
                        !remote.actionNodeConnected && (
                          <Text size="xs" c="dimmed">
                            The isolated node is running. Complete the Tailscale
                            sign-in if prompted, then refresh this step.
                          </Text>
                        )}
                    </Stack>
                  </Alert>
                ) : (
                  <Alert
                    className="cc-warning-alert"
                    color="yellow"
                    title="HTTPS 443 needs another edge"
                  >
                    This platform cannot create an isolated Action node while
                    HTTPS 443 is occupied. Configure an advanced HTTPS 443
                    origin that terminates at the CUICommander Action API.
                  </Alert>
                )}

                <Divider />
                <Group justify="space-between" align="center" wrap="wrap">
                  <Stack gap={2}>
                    <Text size="sm" fw={600}>
                      Advanced endpoint settings
                    </Text>
                    <Text size="xs" c="dimmed">
                      Only needed when you manage your own HTTPS edge.
                    </Text>
                  </Stack>
                  <Button
                    variant="subtle"
                    size="compact-sm"
                    onClick={() => setShowAdvanced((value) => !value)}
                  >
                    {showAdvanced ? 'Hide advanced' : 'Show advanced'}
                  </Button>
                </Group>

                {showAdvanced && (
                  <Paper withBorder p="md" className="cc-surface">
                    <Stack gap="sm">
                      <TextInput
                        key={setup.publicBaseUrl}
                        label="Manual public origin"
                        description="Must be an HTTPS 443 origin terminating at the CUICommander Action API, never raw ComfyUI port 8188."
                        placeholder="https://comfy.example.com"
                        defaultValue={setup.publicBaseUrl}
                        ref={endpointRef}
                        disabled={busy || remoteBusy || remote?.active}
                      />
                      {setup.readiness.httpsEndpoint &&
                        !setup.readiness.customGptOrigin && (
                          <Alert
                            className="cc-warning-alert"
                            color="yellow"
                            title="Standard HTTPS 443 required"
                          >
                            Custom GPT Actions reject non-standard Action server
                            origins such as :8443 or :10000.
                          </Alert>
                        )}
                      <Group justify="flex-end">
                        <Button
                          variant="default"
                          onClick={saveEndpoint}
                          loading={busy}
                          disabled={remote?.active}
                        >
                          Save manual endpoint
                        </Button>
                      </Group>
                    </Stack>
                  </Paper>
                )}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>

          <Accordion.Item
            value="chatgpt"
            className="cc-step-card"
            data-complete={setup.readiness.readyForCustomGPT}
          >
            <Accordion.Control>
              <StepLabel
                number="3"
                title="Copy the connection into ChatGPT"
                description="Instructions, schema, and Bearer key."
                complete={setup.readiness.readyForCustomGPT}
              />
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="lg">
                {!setup.readiness.readyForCustomGPT && (
                  <Alert
                    className="cc-warning-alert"
                    color="yellow"
                    title="Finish steps 1 and 2 first"
                  >
                    The generated connection details are available, but the
                    Custom GPT will not have a complete full-control HTTPS 443
                    connection until the prerequisites above are ready.
                  </Alert>
                )}

                <Stack gap="md">
                  <Group
                    justify="space-between"
                    align="center"
                    wrap="wrap"
                    gap="md"
                  >
                    <Stack gap={2}>
                      <Text fw={600}>Custom GPT instructions</Text>
                      <Text size="sm" c="dimmed">
                        Paste these into the GPT Instructions field.
                      </Text>
                    </Stack>
                    <CopyButton value={setup.gpt.instructions}>
                      {({ copied, copy }) => (
                        <Button variant="light" onClick={copy}>
                          {copied ? 'Copied' : 'Copy instructions'}
                        </Button>
                      )}
                    </CopyButton>
                  </Group>

                  <Divider />

                  <Group
                    justify="space-between"
                    align="center"
                    wrap="wrap"
                    gap="md"
                  >
                    <Stack gap={2}>
                      <Text fw={600}>Action schema</Text>
                      <Text size="sm" c="dimmed">
                        Paste the JSON directly into the Action Schema editor.
                        Do not use Import from URL.
                      </Text>
                    </Stack>
                    <Group gap="xs">
                      <Button
                        variant="subtle"
                        onClick={() => setShowSchema((value) => !value)}
                      >
                        {showSchema ? 'Hide preview' : 'Preview'}
                      </Button>
                      <CopyButton value={setup.gpt.schema}>
                        {({ copied, copy }) => (
                          <Button variant="light" onClick={copy}>
                            {copied ? 'Copied' : 'Copy Action schema'}
                          </Button>
                        )}
                      </CopyButton>
                    </Group>
                  </Group>
                  {showSchema && (
                    <Textarea
                      className="cc-code-preview"
                      label="OpenAPI Action schema"
                      value={setup.gpt.schema}
                      readOnly
                      rows={10}
                    />
                  )}

                  <Divider />

                  <Stack gap="sm">
                    <Group
                      justify="space-between"
                      align="center"
                      wrap="wrap"
                      gap="md"
                    >
                      <Stack gap={2}>
                        <Text fw={600}>Bearer access key</Text>
                        <Text size="sm" c="dimmed">
                          In the Action editor choose API Key authentication and
                          Bearer, then paste this key.
                        </Text>
                      </Stack>
                      <CopyButton value={setup.accessKey}>
                        {({ copied, copy }) => (
                          <Button variant="light" onClick={copy}>
                            {copied ? 'Copied' : 'Copy access key'}
                          </Button>
                        )}
                      </CopyButton>
                    </Group>
                    <PasswordInput
                      label="Action access key"
                      value={setup.accessKey}
                      readOnly
                      autoComplete="off"
                    />
                    <Group justify="flex-end">
                      <Button
                        variant="subtle"
                        color="red"
                        disabled={busy || setup.environmentOverrides.accessKey}
                        onClick={() => {
                          if (
                            window.confirm(
                              'Rotate the CUICommander access key? Existing Custom GPT connections will stop working until updated.',
                            )
                          ) {
                            void onRotateAccessKey()
                          }
                        }}
                      >
                        Rotate key
                      </Button>
                    </Group>
                    {setup.environmentOverrides.accessKey && (
                      <Text size="xs" c="dimmed">
                        The access key is controlled by CUICOMMANDER_API_TOKEN
                        and cannot be rotated here.
                      </Text>
                    )}
                  </Stack>
                </Stack>

                <Paper withBorder p="md" className="cc-surface">
                  <Stack gap="sm">
                    <Text fw={650}>Finish in ChatGPT</Text>
                    <List spacing="xs" size="sm">
                      <List.Item>Create or edit your Custom GPT.</List.Item>
                      <List.Item>
                        Paste the copied CUICommander instructions.
                      </List.Item>
                      <List.Item>
                        Create an Action and paste the copied OpenAPI JSON
                        directly into the Schema editor.
                      </List.Item>
                      <List.Item>
                        Set Authentication to API Key + Bearer and paste the
                        CUICommander access key.
                      </List.Item>
                      <List.Item>
                        Test getCUICommanderManifest before running a real
                        workflow.
                      </List.Item>
                    </List>
                  </Stack>
                </Paper>

                {showAdvanced && (
                  <Text size="xs" c="dimmed">
                    Advanced schema endpoint: {setup.gpt.schemaUrl}
                  </Text>
                )}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </Stack>
    </Section>
  )
}
