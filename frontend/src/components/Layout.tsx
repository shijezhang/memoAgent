import { useEffect, type ReactNode } from 'react'
import Sidebar from './Sidebar'
import StatusBar from './StatusBar'
import Header from './Header'
import { useStore } from '../store/useStore'

interface LayoutProps {
  activePage: string
  setActivePage: (page: string) => void
  children: ReactNode
}

function Layout({ activePage, setActivePage, children }: LayoutProps) {
  const fetchMemoryStatus = useStore((state) => state.fetchMemoryStatus)

  useEffect(() => {
    fetchMemoryStatus()
    const interval = setInterval(fetchMemoryStatus, 30000)
    return () => clearInterval(interval)
  }, [fetchMemoryStatus])

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-dark-bg">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar activePage={activePage} setActivePage={setActivePage} />
        <main className="flex-1 overflow-auto bg-gray-50 dark:bg-dark-bg-secondary">
          {children}
        </main>
      </div>
      <StatusBar />
    </div>
  )
}

export default Layout
