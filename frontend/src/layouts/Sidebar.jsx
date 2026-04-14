import React, { useState } from 'react'
import { Nav } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'
import { 
  FaTachometerAlt, 
  FaBox,
  FaWarehouse,
  FaDownload, 
  FaUpload, 
  FaBoxes, 
  FaChartLine,
  FaExchangeAlt,
  FaCogs,
  FaTools,
  FaShoppingCart,
  FaChartBar,
  FaChevronLeft,
  FaChevronRight,
  FaChevronDown,
  FaCog,
  FaClipboardCheck,
  FaExclamationTriangle,
  FaCheckCircle
} from 'react-icons/fa'
import { useUIStore } from '../stores'
import './Sidebar.css'

const Sidebar = () => {
  const navigate = useNavigate()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  
  // 根据当前路径确定激活的菜单
  const currentPath = window.location.pathname
  const [activeMenu, setActiveMenu] = useState(() => {
    if (currentPath.startsWith('/spare-parts') || currentPath.startsWith('/spare_parts')) {
      return 'spare_parts'
    }
    if (currentPath.startsWith('/warehouses/') || currentPath.startsWith('/warehouse/')) {
      return currentPath
    }
    // 交易管理子菜单：去掉 /react 前缀后匹配
    const txPath = currentPath.replace(/^\/react/, '')
    if (txPath.startsWith('/transactions/')) {
      return txPath
    }
    return 'dashboard'
  })

  // 与备件管理系统完全统一的菜单结构
  const menuItems = [
    {
      key: 'dashboard',
      label: '仪表盘',
      icon: <FaTachometerAlt />,
      path: '/warehouse/dashboard'
    },
    {
      key: 'spare_parts',
      label: '备件管理',
      icon: <FaBox />,
      path: '/spare_parts/'
    },
    {
      key: 'warehouse',
      label: '仓库管理',
      icon: <FaWarehouse />,
      path: '#',
      hasSubmenu: true,
      submenu: [
        {
          key: '/warehouses/',
          label: '仓库列表',
          icon: <FaWarehouse />,
          path: '/warehouses/'
        },
        {
          key: '/warehouses/dashboard',
          label: '仓库仪表盘',
          icon: <FaTachometerAlt />,
          path: '/warehouses/dashboard'
        },
        {
          key: '/warehouses/inbound',
          label: '入库管理',
          icon: <FaDownload />,
          path: '/warehouses/inbound'
        },
        {
          key: '/warehouses/outbound',
          label: '出库管理',
          icon: <FaUpload />,
          path: '/warehouses/outbound'
        },
        {
          key: '/warehouses/inventory',
          label: '库存概览',
          icon: <FaBoxes />,
          path: '/warehouses/inventory'
        },
        {
          key: '/inventory-check',
          label: '库存盘点',
          icon: <FaClipboardCheck />,
          path: '/inventory-check'
        },
        {
          key: '/warning-management',
          label: '预警管理',
          icon: <FaExclamationTriangle />,
          path: '/warning-management'
        },
        {
          key: '/quality-check',
          label: '质检管理',
          icon: <FaCheckCircle />,
          path: '/quality-check'
        },
        {
          key: '/warehouses/analysis',
          label: 'AI 分析',
          icon: <FaChartLine />,
          path: '/warehouses/analysis'
        }
      ]
    },
    {
      key: 'transactions',
      label: '交易管理',
      icon: <FaExchangeAlt />,
      path: '#',
      hasSubmenu: true,
      submenu: [
        { key: '/transactions/list', label: '交易列表', icon: <FaExchangeAlt />, path: '/transactions/list' },
        { key: '/transactions/inbound', label: '入库单', icon: <FaDownload />, path: '/transactions/inbound' },
        { key: '/transactions/outbound', label: '出库单', icon: <FaUpload />, path: '/transactions/outbound' },
        { key: '/transactions/transfer', label: '调拨单', icon: <FaExchangeAlt />, path: '/transactions/transfer' },
        { key: '/transactions/inventory', label: '盘点/差异', icon: <FaClipboardCheck />, path: '/transactions/inventory' },
      ]
    },
    {
      key: 'equipment',
      label: '设备管理',
      icon: <FaCogs />,
      path: '/equipment/'
    },
    {
      key: 'maintenance',
      label: '维修管理',
      icon: <FaTools />,
      path: '/maintenance/'
    },
    {
      key: 'purchase',
      label: '采购管理',
      icon: <FaShoppingCart />,
      path: '/purchase/'
    },
    {
      key: 'reports',
      label: '报表统计',
      icon: <FaChartBar />,
      path: '/reports/'
    }
  ]

  const [expandedMenus, setExpandedMenus] = useState(() => {
    // 如果当前路径是仓库管理的子页面，默认展开仓库管理菜单
    if (currentPath.startsWith('/warehouses/') || currentPath.startsWith('/warehouse/')) {
      return ['warehouse']
    }
    // 如果当前路径是交易管理的子页面，默认展开交易管理菜单
    const txPath = currentPath.replace(/^\/react/, '')
    if (txPath.startsWith('/transactions/')) {
      return ['transactions']
    }
    return []
  })

  const toggleMenu = (key) => {
    setExpandedMenus(prev => 
      prev.includes(key) 
        ? prev.filter(k => k !== key)
        : [...prev, key]
    )
  }

  return (
    <>
      {/* 移动端遮罩层 */}
      {!sidebarCollapsed && (
        <div 
          className="d-lg-none fixed-top w-100 h-100"
          style={{ 
            background: 'rgba(0,0,0,0.5)', 
            zIndex: 998 
          }}
          onClick={toggleSidebar}
        />
      )}

      {/* 侧边栏 - 与备件管理系统统一的深色渐变风格 */}
      <div
        className={`
          sidebar-container
          fixed-top h-100 text-white
          ${sidebarCollapsed ? 'collapsed' : ''}
        `}
        style={{
          width: sidebarCollapsed ? '64px' : '240px',
          background: 'linear-gradient(180deg, #2c3e50 0%, #1a252f 100%)',
          color: '#fff',
          overflowY: 'auto',
          zIndex: 1000,
          boxShadow: '4px 0 10px rgba(0, 0, 0, 0.1)'
        }}
      >
        {/* Logo 区域 */}
        <div 
          className="p-3 border-bottom d-flex align-items-center justify-content-between"
          style={{ 
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            background: 'rgba(0, 0, 0, 0.1)'
          }}
        >
          {!sidebarCollapsed && (
            <span className="fw-bold fs-5" style={{ 
              color: '#fff',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              transition: 'opacity 0.3s'
            }}>
              备件管理系统
            </span>
          )}
          <button
            className="btn btn-link text-white-50 d-none d-lg-block p-0"
            onClick={toggleSidebar}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'rgba(255, 255, 255, 0.7)',
              cursor: 'pointer',
              padding: '0.25rem',
              borderRadius: '4px',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
              e.currentTarget.style.color = '#fff'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent'
              e.currentTarget.style.color = 'rgba(255, 255, 255, 0.7)'
            }}
          >
            {sidebarCollapsed ? <FaChevronRight /> : <FaChevronLeft />}
          </button>
        </div>

        {/* 菜单项 */}
        <Nav className="flex-column p-2" style={{ padding: '0.5rem 0', margin: 0 }}>
          {menuItems.map((item) => (
            item.hasSubmenu ? (
              // 带子菜单的菜单项
              <div key={item.key}>
                <Nav.Link
                  active={activeMenu === item.key}
                  onClick={(e) => {
                    e.preventDefault()
                    if (item.path && item.path !== '#') {
                      navigate(item.path)
                    }
                    toggleMenu(item.key)
                    setActiveMenu(item.key)
                  }}
                  className={`
                    sidebar-nav-link
                    d-flex align-items-center
                    ${activeMenu === item.key ? 'active' : ''}
                    ${sidebarCollapsed ? 'justify-content-center' : 'px-3'}
                  `}
                  data-tooltip={item.label}
                >
                  <span className="sidebar-icon">
                    {item.icon}
                  </span>
                  {!sidebarCollapsed && (
                    <>
                      <span className="sidebar-label ms-3">{item.label}</span>
                      <FaChevronDown 
                        className={`ms-auto expand-icon ${expandedMenus.includes(item.key) ? 'rotated' : ''}`}
                      />
                    </>
                  )}
                  {/* 左侧高亮条 */}
                  <span className="highlight-bar" />
                </Nav.Link>
                
                {/* 子菜单 */}
                {!sidebarCollapsed && expandedMenus.includes(item.key) && (
                  <div className="submenu-container">
                    {item.submenu.map((subItem) => (
                      <Nav.Link
                        key={subItem.key}
                        active={activeMenu === subItem.key}
                        onClick={(e) => {
                          e.preventDefault()
                          navigate(subItem.path)
                          setActiveMenu(subItem.key)
                        }}
                        className={`
                          sidebar-submenu-link
                          d-flex align-items-center
                          ${activeMenu === subItem.key ? 'active' : ''}
                          px-3
                        `}
                      >
                        <span className="sidebar-icon" style={{ fontSize: '1rem', minWidth: '20px' }}>
                          {subItem.icon}
                        </span>
                        <span className="sidebar-label ms-2">{subItem.label}</span>
                        {/* 左侧高亮条 */}
                        <span className="highlight-bar" />
                      </Nav.Link>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              // 普通菜单项
              <Nav.Link
                key={item.key}
                active={activeMenu === item.key}
                onClick={(e) => {
                  e.preventDefault()
                  navigate(item.path)
                  setActiveMenu(item.key)
                }}
                className={`
                  sidebar-nav-link
                  d-flex align-items-center
                  ${activeMenu === item.key ? 'active' : ''}
                  ${sidebarCollapsed ? 'justify-content-center' : 'px-3'}
                `}
                data-tooltip={item.label}
              >
                <span className="sidebar-icon">
                  {item.icon}
                </span>
                {!sidebarCollapsed && (
                  <span className="sidebar-label ms-3">{item.label}</span>
                )}
                {/* 左侧高亮条 */}
                <span className="highlight-bar" />
              </Nav.Link>
            )
          ))}
        </Nav>

        {/* 底部菜单 */}
        <div 
          className="position-absolute bottom-0 w-100 border-top p-2"
          style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}
        >
          <Nav.Link 
            className="settings-link text-white-50 d-flex align-items-center px-3"
            onClick={(e) => {
              e.preventDefault()
              navigate('/system/settings')
            }}
          >
            <span className="sidebar-icon">
              <FaCog />
            </span>
            {!sidebarCollapsed && (
              <span className="sidebar-label ms-3">系统设置</span>
            )}
          </Nav.Link>
        </div>
      </div>
    </>
  )
}

export default Sidebar
