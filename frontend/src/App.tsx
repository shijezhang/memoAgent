import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import KnowledgePage from './pages/KnowledgePage'
import MemoryPage from './pages/MemoryPage'
import ReflectionPage from './pages/ReflectionPage'
import { useTheme } from './hooks/useTheme'

function App() {
  const [activePage, setActivePage] = useState('chat')

  // Initialize theme on mount
  useTheme()

  const renderPage = () => {
    switch (activePage) {
      case 'chat':
        return <ChatPage />
      case 'knowledge':
        return <KnowledgePage />
      case 'memory':
        return <MemoryPage />
      case 'reflection':
        return <ReflectionPage />
      default:
        return <ChatPage />
    }
  }

  return (
    <Layout activePage={activePage} setActivePage={setActivePage}>
      {renderPage()}
    </Layout>
  )
}

export default App
