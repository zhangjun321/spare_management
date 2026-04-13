import React from 'react'
import { Container } from 'react-bootstrap'
import Sidebar from './Sidebar'
import Header from './Header'
import { useUIStore } from '../stores'

const MainLayout = ({ children, showSidebar = true }) => {
  const { sidebarCollapsed } = useUIStore()

  // 全屏模式（无侧边栏）
  if (!showSidebar) {
    return (
      <div className="d-flex" style={{ minHeight: '100vh', background: '#f5f7fa' }}>
        <main className="flex-grow-1 w-100 p-4">
          <Container fluid className="px-0 h-100">
            {children}
          </Container>
        </main>
      </div>
    )
  }

  // 正常模式（有侧边栏和 Header - React 完整布局）
  return (
    <div className="d-flex" style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <Sidebar />
      
      <div 
        className="flex-grow-1 d-flex flex-column"
        style={{
          marginLeft: sidebarCollapsed ? '64px' : '240px',
          transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          minWidth: 0,
          flex: '1 1 auto'
        }}
      >
        <Header />
        
        <main className="flex-grow-1 p-4" style={{ width: '100%', overflowX: 'auto' }}>
          <Container fluid className="px-4" style={{ maxWidth: '100%', width: '100%' }}>
            {children}
          </Container>
        </main>
      </div>
    </div>
  )
}

export default MainLayout
