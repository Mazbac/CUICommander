import { lazy, Suspense, useEffect, useState } from 'react'
import { AdvancedPage } from './AdvancedPage'
import { ConnectionPage } from './ConnectionPage'
import { HomePage } from './HomePage'
import { AppFrame, type PageId } from './layouts/AppFrame'
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
  'home',
  'chatgpt',
  'activity',
  'advanced',
  'resources',
  'transfers',
  'workflows',
  'runtime',
])

function pageFromHash(): PageId {
  const value = window.location.hash.replace(/^#\/?/, '') || 'home'
  if (value === 'overview') return 'home'
  return validPages.has(value as PageId) ? (value as PageId) : 'home'
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
    const hash = next === 'home' ? '#/' : `#/${next}`
    if (window.location.hash !== hash) window.location.hash = hash
    setPage(next)
  }

  const content = (() => {
    if (page === 'chatgpt')
      return <ConnectionPage controlPlane={controlPlane} />
    if (page === 'activity') return <ActivityPage controlPlane={controlPlane} />
    if (page === 'advanced') return <AdvancedPage onNavigate={navigate} />
    if (page === 'resources')
      return <ResourcesPage controlPlane={controlPlane} />
    if (page === 'transfers')
      return <TransfersPage controlPlane={controlPlane} />
    if (page === 'workflows')
      return <WorkflowsPage controlPlane={controlPlane} />
    if (page === 'runtime') return <RuntimePage controlPlane={controlPlane} />
    return <HomePage controlPlane={controlPlane} onNavigate={navigate} />
  })()

  return (
    <AppFrame activePage={page} onNavigate={navigate}>
      <Suspense fallback={null}>{content}</Suspense>
    </AppFrame>
  )
}

export default App
