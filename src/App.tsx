import { useEffect, useState } from 'react'
import { ActivityPage } from './ActivityPage'
import { AppFrame, type PageId } from './layouts/AppFrame'
import { OverviewPage } from './OverviewPage'
import { ResourcesPage } from './ResourcesPage'
import { RuntimePage } from './RuntimePage'
import { TransfersPage } from './TransfersPage'
import { WorkflowsPage } from './WorkflowsPage'
import { useControlPlane } from './hooks/useControlPlane'

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
      {content}
    </AppFrame>
  )
}

export default App
