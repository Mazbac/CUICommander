import { lazy, Suspense, useEffect, useState } from 'react'
import { Center, Loader } from '@mantine/core'
import { AppFrame, type PageId } from './layouts/AppFrame'
import { OverviewPage } from './OverviewPage'
import { useControlPlane } from './hooks/useControlPlane'

const ResourcesPage = lazy(() =>
  import('./ResourcesPage').then((module) => ({
    default: module.ResourcesPage,
  })),
)
const TransfersPage = lazy(() =>
  import('./TransfersPage').then((module) => ({
    default: module.TransfersPage,
  })),
)
const WorkflowsPage = lazy(() =>
  import('./WorkflowsPage').then((module) => ({
    default: module.WorkflowsPage,
  })),
)
const RuntimePage = lazy(() =>
  import('./RuntimePage').then((module) => ({ default: module.RuntimePage })),
)
const ActivityPage = lazy(() =>
  import('./ActivityPage').then((module) => ({ default: module.ActivityPage })),
)

const validPages = new Set<PageId>([
  'overview',
  'resources',
  'transfers',
  'workflows',
  'runtime',
  'activity',
])

function pageFromHash(): PageId {
  const value = window.location.hash.replace(/^#\/?/, '') || 'overview'
  return validPages.has(value as PageId) ? (value as PageId) : 'overview'
}

function App() {
  const controlPlane = useControlPlane()
  const [page, setPage] = useState<PageId>(pageFromHash)

  useEffect(() => {
    const sync = () => setPage(pageFromHash())
    window.addEventListener('hashchange', sync)
    return () => window.removeEventListener('hashchange', sync)
  }, [])

  const navigate = (next: PageId) => {
    const hash = next === 'overview' ? '#/' : `#/${next}`
    if (window.location.hash !== hash) window.location.hash = hash
    setPage(next)
  }

  const content = (() => {
    if (page === 'resources')
      return <ResourcesPage controlPlane={controlPlane} />
    if (page === 'transfers')
      return <TransfersPage controlPlane={controlPlane} />
    if (page === 'workflows')
      return <WorkflowsPage controlPlane={controlPlane} />
    if (page === 'runtime') return <RuntimePage controlPlane={controlPlane} />
    if (page === 'activity') return <ActivityPage controlPlane={controlPlane} />
    return <OverviewPage controlPlane={controlPlane} />
  })()

  return (
    <AppFrame activePage={page} onNavigate={navigate}>
      <Suspense
        fallback={
          <Center py="xl" aria-label="Loading page">
            <Loader size="sm" />
          </Center>
        }
      >
        {content}
      </Suspense>
    </AppFrame>
  )
}

export default App
