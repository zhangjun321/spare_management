import React from 'react'
import { Navbar, Nav, Container, Dropdown, Badge } from 'react-bootstrap'
import { FaBell, FaUser, FaBars, FaSignOutAlt } from 'react-icons/fa'
import { useUIStore } from '../stores'

const Header = () => {
  const { sidebarCollapsed, toggleSidebar } = useUIStore()

  return (
    <Navbar bg="white" expand="lg" className="border-bottom shadow-sm px-3">
      <div className="d-flex align-items-center w-100">
        {/* 侧边栏切换按钮 */}
        <button
          className="btn btn-link d-lg-none me-2"
          onClick={toggleSidebar}
        >
          <FaBars size={20} />
        </button>

        {/* Logo */}
        <Navbar.Brand href="/" className="fw-bold text-primary">
          <i className="fas fa-warehouse me-2"></i>
          智能仓库管理系统
        </Navbar.Brand>

        {/* 右侧导航 */}
        <Nav className="ms-auto align-items-center">
          {/* 通知 */}
          <Nav.Link href="#" className="position-relative">
            <FaBell size={18} />
            <Badge 
              bg="danger" 
              pill 
              className="position-absolute top-0 start-100 translate-middle"
              style={{ fontSize: '0.6rem' }}
            >
              3
            </Badge>
          </Nav.Link>

          {/* 用户菜单 */}
          <Dropdown align="end">
            <Dropdown.Toggle variant="link" className="nav-link text-dark text-decoration-none">
              <FaUser className="me-1" />
              <span className="d-none d-md-inline">管理员</span>
            </Dropdown.Toggle>

            <Dropdown.Menu>
              <Dropdown.Header>个人信息</Dropdown.Header>
              <Dropdown.Item href="/profile">
                <FaUser className="me-2" />
                个人资料
              </Dropdown.Item>
              <Dropdown.Item href="/settings">
                <i className="fas fa-cog me-2"></i>
                系统设置
              </Dropdown.Item>
              <Dropdown.Divider />
              <Dropdown.Item href="/logout" className="text-danger">
                <FaSignOutAlt className="me-2" />
                退出登录
              </Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
        </Nav>
      </div>
    </Navbar>
  )
}

export default Header
