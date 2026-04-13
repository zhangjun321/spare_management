import React from 'react'
import { Container, Row, Col, Button } from 'react-bootstrap'
import { FaGithub, FaWeixin, FaQq, FaBell, FaPhone, FaEnvelope, FaClock, FaMapMarkerAlt, FaChevronUp } from 'react-icons/fa'

const Footer = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const currentYear = new Date().getFullYear()

  return (
    <footer style={{ 
      background: '#fff',
      borderTop: '1px solid #e9ecef',
      padding: '40px 0 20px',
      marginTop: '60px'
    }}>
      <Container>
        {/* Footer 主要内容 */}
        <Row className="mb-4">
          {/* 品牌信息 */}
          <Col lg={3} md={6} className="mb-4">
            <h5 className="fw-bold mb-3" style={{ color: '#2c3e50' }}>
              <i className="fas fa-warehouse me-2"></i>智能仓储管理系统
            </h5>
            <p className="text-muted small">
              实时库存监控，精准库存预警，让备件管理更高效
            </p>
            <div className="d-flex gap-3 mt-3">
              <Button variant="outline-primary" className="rounded-circle p-2" style={{ width: '40px', height: '40px' }}>
                <FaGithub />
              </Button>
              <Button variant="outline-info" className="rounded-circle p-2" style={{ width: '40px', height: '40px' }}>
                <FaWeixin />
              </Button>
              <Button variant="outline-success" className="rounded-circle p-2" style={{ width: '40px', height: '40px' }}>
                <FaQq />
              </Button>
              <Button variant="outline-warning" className="rounded-circle p-2" style={{ width: '40px', height: '40px' }}>
                <FaBell />
              </Button>
            </div>
          </Col>

          {/* 快速链接 */}
          <Col lg={2} md={6} className="mb-4">
            <h6 className="fw-bold mb-3" style={{ color: '#2c3e50' }}>快速链接</h6>
            <ul className="list-unstyled">
              <li className="mb-2">
                <a href="/warehouse/dashboard" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>仪表盘
                </a>
              </li>
              <li className="mb-2">
                <a href="/warehouse/inbound" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>入库管理
                </a>
              </li>
              <li className="mb-2">
                <a href="/warehouse/outbound" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>出库管理
                </a>
              </li>
              <li className="mb-2">
                <a href="/warehouse/inventory" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>库存管理
                </a>
              </li>
            </ul>
          </Col>

          {/* 功能导航 */}
          <Col lg={2} md={6} className="mb-4">
            <h6 className="fw-bold mb-3" style={{ color: '#2c3e50' }}>功能导航</h6>
            <ul className="list-unstyled">
              <li className="mb-2">
                <a href="/warehouse/inbound" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>交易管理
                </a>
              </li>
              <li className="mb-2">
                <a href="/warehouse/inventory" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>维修管理
                </a>
              </li>
              <li className="mb-2">
                <a href="/warehouse/inbound" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>采购管理
                </a>
              </li>
              <li className="mb-2">
                <a href="/reports" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>报表统计
                </a>
              </li>
            </ul>
          </Col>

          {/* 技术支持 */}
          <Col lg={2} md={6} className="mb-4">
            <h6 className="fw-bold mb-3" style={{ color: '#2c3e50' }}>技术支持</h6>
            <ul className="list-unstyled">
              <li className="mb-2">
                <a href="/help" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>帮助文档
                </a>
              </li>
              <li className="mb-2">
                <a href="/system/status" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>系统状态
                </a>
              </li>
              <li className="mb-2">
                <a href="/changelog" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>更新日志
                </a>
              </li>
              <li className="mb-2">
                <a href="/feedback" className="text-decoration-none text-muted small">
                  <i className="fas fa-chevron-right me-1 small"></i>反馈意见
                </a>
              </li>
            </ul>
          </Col>

          {/* 联系我们 */}
          <Col lg={3} md={6} className="mb-4">
            <h6 className="fw-bold mb-3" style={{ color: '#2c3e50' }}>联系我们</h6>
            <ul className="list-unstyled">
              <li className="mb-3">
                <div className="d-flex align-items-center">
                  <FaPhone className="text-primary me-2" />
                  <span className="text-muted small">400-888-8888</span>
                </div>
              </li>
              <li className="mb-3">
                <div className="d-flex align-items-center">
                  <FaEnvelope className="text-primary me-2" />
                  <span className="text-muted small">support@example.com</span>
                </div>
              </li>
              <li className="mb-3">
                <div className="d-flex align-items-start">
                  <FaClock className="text-primary me-2 mt-1" />
                  <span className="text-muted small">周一至周五 9:00-18:00</span>
                </div>
              </li>
              <li className="mb-3">
                <div className="d-flex align-items-start">
                  <FaMapMarkerAlt className="text-primary me-2 mt-1" />
                  <span className="text-muted small">中国 上海</span>
                </div>
              </li>
            </ul>
          </Col>
        </Row>

        {/* 底部分隔线 */}
        <hr className="my-4" />

        {/* 版权信息 */}
        <Row className="align-items-center">
          <Col md={6} className="text-center text-md-start mb-2 mb-md-0">
            <p className="text-muted small mb-0">
              &copy; {currentYear} 智能仓储管理系统。All rights reserved.
            </p>
          </Col>
          <Col md={6} className="text-center text-md-end">
            <a href="/privacy" className="text-muted small text-decoration-none me-3">
              隐私政策
            </a>
            <a href="/terms" className="text-muted small text-decoration-none me-3">
              使用条款
            </a>
            <Button 
              variant="primary" 
              className="rounded-circle p-2"
              style={{ width: '40px', height: '40px' }}
              onClick={scrollToTop}
            >
              <FaChevronUp />
            </Button>
          </Col>
        </Row>
      </Container>
    </footer>
  )
}

export default Footer
