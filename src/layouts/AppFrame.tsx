import type { ReactNode } from 'react'
import {
  AppShell,
  Box,
  Burger,
  Divider,
  Group,
  NavLink,
  Stack,
  Text,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { AppearanceMenu } from '../components/ui/AppearanceMenu'
import { layoutTokens } from '../theme/theme'

export type PageId =
  'overview' | 'resources' | 'transfers' | 'workflows' | 'runtime' | 'activity'

type AppFrameProps = {
  children: ReactNode
  activePage: PageId
  onNavigate: (page: PageId) => void
}

const pages: Array<{ id: PageId; label: string }> = [
  { id: 'overview', label: 'Setup & status' },
  { id: 'resources', label: 'Resources' },
  { id: 'transfers', label: 'Transfers & jobs' },
  { id: 'workflows', label: 'Workflows' },
  { id: 'runtime', label: 'Runtime' },
  { id: 'activity', label: 'Activity' },
]

export function AppFrame({ children, activePage, onNavigate }: AppFrameProps) {
  const [opened, { toggle, close }] = useDisclosure(false)

  return (
    <AppShell
      header={{ height: layoutTokens.headerHeight }}
      navbar={{
        width: layoutTokens.navbarWidth,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding={{ base: 'md', sm: 'xl' }}
    >
      <AppShell.Header className="cc-app-header">
        <Group
          h="100%"
          px={{ base: 'md', sm: 'lg' }}
          justify="space-between"
          wrap="nowrap"
        >
          <Group gap="sm" wrap="nowrap" miw={0}>
            <Burger
              opened={opened}
              onClick={toggle}
              hiddenFrom="sm"
              size="sm"
              aria-label="Toggle navigation"
            />
            <Box className="cc-brand-mark" aria-hidden="true">
              C
            </Box>
            <Stack gap={0} miw={0}>
              <Text fw={750} lh={1.2}>
                CUICommander
              </Text>
              <Text c="dimmed" size="xs" visibleFrom="xs">
                ComfyUI control plane
              </Text>
            </Stack>
          </Group>
          <AppearanceMenu />
        </Group>
      </AppShell.Header>

      <AppShell.Navbar className="cc-app-navbar" p="md">
        <Stack gap="md" h="100%">
          <Stack gap={4}>
            <Text size="xs" fw={700} c="dimmed" tt="uppercase">
              Workspace
            </Text>
            {pages.map((page) => (
              <NavLink
                className="cc-nav-link"
                key={page.id}
                label={page.label}
                active={activePage === page.id}
                color="brand"
                variant="light"
                href={page.id === 'overview' ? '#/' : `#/${page.id}`}
                onClick={(event) => {
                  event.preventDefault()
                  onNavigate(page.id)
                  close()
                }}
              />
            ))}
          </Stack>
          <Divider mt="auto" />
          <Text size="xs" c="dimmed">
            Local administration stays private. Public access uses only the
            authenticated Action API.
          </Text>
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>
        <Box className="cc-main" maw={layoutTokens.contentMaxWidth} mx="auto">
          {children}
        </Box>
      </AppShell.Main>
    </AppShell>
  )
}
