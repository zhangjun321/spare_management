import React, { useState, useEffect, useCallback } from 'react'
import { Container, Row, Col, Card, Button, Badge, Form } from 'react-bootstrap'
import { FaSearch, FaUndo, FaEye, FaChartPie, FaSync } from 'react-icons/fa'
import { useNavigate } from 'react-router-dom'
import { Table, StatCard } from '@/components'
import { useUIStore } from '@/stores'
import { inventoryService } from '@/services/warehouse'
import { FaBox, FaExclamationTriangle, FaCheckCircle, FaWarehouse } from 'react-icons/fa'
import MainLayout from '@/layouts/MainLayout'
import Footer from '@/components/Footer'
import InventoryCarousel from '@/components/InventoryCarousel'
import { message as antMessage } from 'antd'

const InventoryList = () => {
  const navigate = useNavigate()
  const { setLoading } = useUIStore()
  
  const [loading, setLoadingLocal] = useState(false)
  const [inventoryItems, setInventoryItems] = useState([])
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0
  })
  const [searchForm, setSearchForm] = useState({
    stock_status: '',
    has_stock: ''
  })
  const [stats, setStats] = useState({
    total: 0,
    lowStock: 0,
    outOfStock: 0,
    normal: 0
  })

  const loadInventory = useCallback(async () => {
    try {
      setLoadingLocal(true)
      setLoading(true)
      
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...searchForm
      }
      
      const response = await inventoryService.getList(params)
      
      if (response.success) {
        setInventoryItems(response.data.items)
        setPagination(prev => ({
          ...prev,
          total: response.data.total
        }))
        setStats(prev => ({
          ...prev,
          total: response.data.total
        }))
      }
    } catch (error) {
      console.error('加载库存数据失败:', error)
      // 不显示弹出框，静默处理错误
    } finally {
      setLoadingLocal(false)
      setLoading(false)
    }
  }, [pagination.page, pagination.per_page, searchForm, setLoading])

  const loadStats = useCallback(async () => {
    try {
      const res = await inventoryService.getStats()
      if (res.success && res.data) {
        setStats(prev => ({
          ...prev,
          lowStock: res.data.low_stock || 0,
          outOfStock: res.data.out_of_stock || 0,
          normal: res.data.normal || 0
        }))
      }
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  }, [])

  useEffect(() => {
    loadInventory()
    loadStats()
  }, [loadInventory, loadStats])

  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page: 1 }))
    loadInventory()
  }

  const handleReset = () => {
    setSearchForm({ stock_status: '', has_stock: '' })
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleRefresh = () => {
    loadInventory()
    loadStats()
    antMessage.success('数据已刷新')
  }

  const handleViewDetail = (row) => {
    navigate(`/warehouse/inventory/${row.id}`)
  }

  const handleViewDistribution = (row) => {
    navigate(`/warehouse/inventory/${row.id}/distribution`)
  }

  const getStatusLabel = (status) => {
    const map = {
      normal: '正常',
      low: '低库存',
      out: '缺货',
      overstocked: '超储',
      locked: '锁定'
    }
    return map[status] || status
  }

  const getStatusBadgeVariant = (status) => {
    const map = {
      normal: 'success',
      low: 'warning',
      out: 'danger',
      overstocked: 'info',
      locked: 'warning'
    }
    return map[status] || 'secondary'
  }

  const columns = [
    {
      key: 'id',
      title: 'ID',
      width: 80
    },
    {
      key: 'spare_part_id',
      title: '备件 ID',
      width: 100
    },
    {
      key: 'warehouse_id',
      title: '仓库 ID',
      width: 100
    },
    {
      key: 'location_id',
      title: '货位 ID',
      width: 100
    },
    {
      key: 'quantity',
      title: '库存数量',
      width: 100
    },
    {
      key: 'available_quantity',
      title: '可用数量',
      width: 100
    },
    {
      key: 'locked_quantity',
      title: '锁定数量',
      width: 100
    },
    {
      key: 'stock_status',
      title: '库存状态',
      width: 100,
      render: (value) => (
        <Badge bg={getStatusBadgeVariant(value)}>{getStatusLabel(value)}</Badge>
      )
    },
    {
      key: 'batch_number',
      title: '批次号',
      width: 150
    },
    {
      key: 'updated_at',
      title: '最后更新时间',
      width: 180
    }
  ]

  const actions = (item) => (
    <>
      <Button
        variant="outline-primary"
        size="sm"
        onClick={() => handleViewDetail(item)}
      >
        <FaEye className="me-1" />
        详情
      </Button>
      
      <Button
        variant="outline-info"
        size="sm"
        onClick={() => handleViewDistribution(item)}
      >
        <FaChartPie className="me-1" />
        分布
      </Button>
    </>
  )

  return (
    <MainLayout showSidebar={true} showHeader={true}>
      <div className="position-relative" style={{ minHeight: 'calc(100vh - 120px)' }}>
        {/* 轮播图 */}
        <div className="container-fluid px-0 mb-4">
          <InventoryCarousel />
        </div>

        {/* 页面头部 */}
        <Row className="mb-4">
          <Col>
            <div className="d-flex justify-content-between align-items-center">
              <h2 className="mb-0">📦 库存管理</h2>
              <Button variant="outline-primary" onClick={handleRefresh}>
                <FaSync className="me-2" />
                刷新
              </Button>
            </div>
          </Col>
        </Row>

        {/* 统计卡片 */}
        <Row className="mb-4">
          <Col md={6} lg={3}>
            <StatCard
              title="总库存品种"
              value={stats.total}
              icon={<FaBox />}
              color="primary"
            />
          </Col>
          <Col md={6} lg={3}>
            <StatCard
              title="低库存"
              value={stats.lowStock}
              icon={<FaExclamationTriangle />}
              color="warning"
            />
          </Col>
          <Col md={6} lg={3}>
            <StatCard
              title="缺货"
              value={stats.outOfStock}
              icon={<FaExclamationTriangle />}
              color="danger"
            />
          </Col>
          <Col md={6} lg={3}>
            <StatCard
              title="正常"
              value={stats.normal}
              icon={<FaCheckCircle />}
              color="success"
            />
          </Col>
        </Row>

        {/* 搜索表单 */}
        <Row className="mb-4">
          <Col>
            <Card className="border-0 shadow-sm">
              <Card.Body>
                <Form className="d-flex flex-wrap gap-3 align-items-end">
                  <Form.Group style={{ minWidth: '200px' }}>
                    <Form.Label>库存状态</Form.Label>
                    <Form.Select
                      value={searchForm.stock_status}
                      onChange={(e) => setSearchForm(prev => ({ ...prev, stock_status: e.target.value }))}
                    >
                      <option value="">全部</option>
                      <option value="normal">正常</option>
                      <option value="low">低库存</option>
                      <option value="out">缺货</option>
                      <option value="overstocked">超储</option>
                    </Form.Select>
                  </Form.Group>

                  <Form.Group style={{ minWidth: '200px' }}>
                    <Form.Label>只显示有库存</Form.Label>
                    <Form.Check
                      type="switch"
                      id="has-stock-switch"
                      checked={searchForm.has_stock === 'true'}
                      onChange={(e) => setSearchForm(prev => ({ 
                        ...prev, 
                        has_stock: e.target.checked ? 'true' : '' 
                      }))}
                      label="开启"
                    />
                  </Form.Group>

                  <div className="d-flex gap-2">
                    <Button variant="primary" onClick={handleSearch}>
                      <FaSearch className="me-1" />
                      查询
                    </Button>
                    <Button variant="outline-secondary" onClick={handleReset}>
                      <FaUndo className="me-1" />
                      重置
                    </Button>
                  </div>
                </Form>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* 数据表格 */}
        <Row>
          <Col>
            <Card className="border-0 shadow-sm">
              <Card.Body>
                <Table
                  columns={columns}
                  data={inventoryItems}
                  pagination={true}
                  searchable={false}
                  sortable={true}
                  pageSize={pagination.per_page}
                  actions={actions}
                  loading={loading}
                />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </div>
      
      {/* Footer */}
      <Footer />
    </MainLayout>
  )
}

export default InventoryList
