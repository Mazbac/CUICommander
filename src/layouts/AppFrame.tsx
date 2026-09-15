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
  | 'home'
  | 'chatgpt'
  | 'activity'
  | 'advanced'
  | 'resources'
  | 'transfers'
  | 'workflows'
  | 'runtime'

type AppFrameProps = {
  children: ReactNode
  activePage: PageId
  onNavigate: (page: PageId) => void
}

const primaryPages: Array<{ id: PageId; label: string }> = [
  { id: 'home', label: 'Home' },
  { id: 'chatgpt', label: 'ChatGPT' },
  { id: 'activity', label: 'Activity' },
  { id: 'advanced', label: 'Advanced' },
]

const advancedPages = new Set<PageId>([
  'advanced',
  'resources',
  'transfers',
  'workflows',
  'runtime',
])

function primaryActive(page: PageId, candidate: PageId) {
  if (candidate === 'advanced') return advancedPages.has(page)
  return page === candidate
}

export function AppFrame({ children, activePage, onNavigate }: AppFrameProps) {
  const [opened, { toggle, close }] = useDisclosure(false)

  return (
    <AppShell
      header={{ height: { base: 56, sm: 0 } }}
      navbar={{
        width: layoutTokens.navbarWidth,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding={{ base: 'md', sm: 'xl' }}
    >
      <AppShell.Header className="cc-mobile-header" hiddenFrom="sm">
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <Burger
              opened={opened}
              onClick={toggle}
              size="sm"
              aria-label="Toggle navigation"
            />
            <Text fw={700}>CUICommander</Text>
          </Group>
          <AppearanceMenu />
        </Group>
      </AppShell.Header>

      <AppShell.Navbar className="cc-app-navbar" p="lg">
        <Stack h="100%" gap="xl">
          <Stack gap={2}>
            <Group gap="sm" wrap="nowrap">
              <Box className="cc-brand-mark" aria-hidden="true">
                C
              </Box>
              <Text fw={750} size="lg">
                CUICommander
              </Text>
            </Group>
            <Text c="dimmed" size="xs" pl={44}>
              ChatGPT control for ComfyUI
            </Text>
          </Stack>

          <Stack gap={4}>
            {primaryPages.map((page) => (
              <NavLink
                className="cc-nav-link"
                key={page.id}
                label={page.label}
                active={primaryActive(activePage, page.id)}
                color="brand"
                variant="light"
                href={page.id === 'home' ? '#/' : `#/${page.id}`}
                onClick={(event) => {
                  event.preventDefault()
                  onNavigate(page.id)
                  close()
                }}
              />
            ))}
          </Stack>

          <Stack gap="sm" mt="auto">
            <Divider />
            <Group justify="space-between" align="center" wrap="nowrap">
              <Stack gap={0} miw={0}>
                <Text size="xs" fw={600}>
                  Local administration
                </Text>
                <Text size="xs" c="dimmed">
                  Private by default
                </Text>
              </Stack>
              <AppearanceMenu />
            </Group>
          </Stack>
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
