import React, { useState, useEffect, useCallback } from 'react'
import { Container, Row, Col, Card, Button, Badge, Form } from 'react-bootstrap'
import { FaPlus, FaSearch, FaUndo, FaEye, FaCheck, FaTimes } from 'react-icons/fa'
import { useNavigate } from 'react-router-dom'
import { Table } from '@/components'
import { useUIStore } from '@/stores'
import { outboundOrderService } from '@/services/warehouse'
import MainLayout from '@/layouts/MainLayout'
import Footer from '@/components/Footer'
import OutboundCarousel from '@/components/OutboundCarousel'
import { Modal, message as antMessage } from 'antd'

const OutboundList = () => {
  const navigate = useNavigate()
  const { setLoading } = useUIStore()
  
  const [loading, setLoadingLocal] = useState(false)
  const [outboundOrders, setOutboundOrders] = useState([])
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0
  })
  const [searchForm, setSearchForm] = useState({
    outbound_type: '',
    status: ''
  })

  const loadOutboundOrders = useCallback(async () => {
    try {
      setLoadingLocal(true)
      setLoading(true)
      
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...searchForm
      }
      
      const response = await outboundOrderService.getList(params)
      
      if (response.success) {
        setOutboundOrders(response.data.items)
        setPagination(prev => ({
          ...prev,
          total: response.data.total
        }))
      }
    } catch (error) {
      console.error('加载出库数据失败:', error)
      // 不显示弹出框，静默处理错误
    } finally {
      setLoadingLocal(false)
      setLoading(false)
    }
  }, [pagination.page, pagination.per_page, searchForm, setLoading])

  useEffect(() => {
    loadOutboundOrders()
  }, [loadOutboundOrders])

  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page: 1 }))
    loadOutboundOrders()
  }

  const handleReset = () => {
    setSearchForm({ outbound_type: '', status: '' })
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleCreate = () => {
    navigate('/warehouse/outbound/create')
  }

  const handleViewDetail = (row) => {
    navigate(`/warehouse/outbound/${row.id}`)
  }

  const handleComplete = async (row) => {
    Modal.confirm({
      title: '确认完成出库',
      content: '确定要完成该出库单吗？',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await outboundOrderService.complete(row.id)
          if (response.success) {
            antMessage.success('出库完成')
            loadOutboundOrders()
          } else {
            antMessage.error(response.error || '操作失败')
          }
        } catch (error) {
          console.error('完成出库失败:', error)
          antMessage.error('操作失败')
        }
      }
    })
  }

  const handleCancel = async (row) => {
    Modal.confirm({
      title: '确认取消',
      content: '确定要取消该出库单吗？',
      okText: '确认取消',
      okType: 'danger',
      cancelText: '返回',
      onOk: async () => {
        try {
          const response = await outboundOrderService.cancel(row.id)
          if (response.success) {
            antMessage.success('已取消')
            loadOutboundOrders()
          } else {
            antMessage.error(response.error || '操作失败')
          }
        } catch (error) {
          console.error('取消出库失败:', error)
          antMessage.error('操作失败')
        }
      }
    })
  }

  const getTypeLabel = (type) => {
    const map = {
      requisition: '领用出库',
      sale: '销售出库',
      return: '退货出库',
      transfer: '调拨出库',
      other: '其他出库'
    }
    return map[type] || type
  }

  const getTypeBadgeVariant = (type) => {
    const map = {
      requisition: 'primary',
      sale: 'success',
      return: 'info',
      transfer: 'warning',
      other: 'secondary'
    }
    return map[type] || 'secondary'
  }

  const getStatusLabel = (status) => {
    const map = {
      pending: '待出库',
      partial: '部分出库',
      completed: '已完成',
      cancelled: '已取消'
    }
    return map[status] || status
  }

  const getStatusBadgeVariant = (status) => {
    const map = {
      pending: 'warning',
      partial: 'info',
      completed: 'success',
      cancelled: 'danger'
    }
    return map[status] || 'secondary'
  }

  const columns = [
    {
      key: 'order_no',
      title: '出库单号',
      width: 160
    },
    {
      key: 'outbound_type',
      title: '出库类型',
      width: 120,
      render: (value) => (
        <Badge bg={getTypeBadgeVariant(value)}>{getTypeLabel(value)}</Badge>
      )
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
      key: 'quantity',
      title: '出库数量',
      width: 100
    },
    {
      key: 'shipped_quantity',
      title: '实发数量',
      width: 100
    },
    {
      key: 'status',
      title: '状态',
      width: 100,
      render: (value) => (
        <Badge bg={getStatusBadgeVariant(value)}>{getStatusLabel(value)}</Badge>
      )
    },
    {
      key: 'created_at',
      title: '创建时间',
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
      
      {item.status === 'pending' && (
        <Button
          variant="outline-success"
          size="sm"
          onClick={() => handleComplete(item)}
        >
          <FaCheck className="me-1" />
          完成出库
        </Button>
      )}
      
      {item.status !== 'completed' && item.status !== 'cancelled' && (
        <Button
          variant="outline-danger"
          size="sm"
          onClick={() => handleCancel(item)}
        >
          <FaTimes className="me-1" />
          取消
        </Button>
      )}
    </>
  )

  return (
    <MainLayout showSidebar={true} showHeader={true}>
      <div className="position-relative" style={{ minHeight: 'calc(100vh - 120px)' }}>
        {/* 轮播图 */}
        <div className="container-fluid px-0 mb-4">
          <OutboundCarousel />
        </div>

        {/* 页面头部 */}
        <Row className="mb-4">
          <Col>
            <div className="d-flex justify-content-between align-items-center">
              <h2 className="mb-0">📤 出库管理</h2>
              <Button variant="primary" onClick={handleCreate}>
                <FaPlus className="me-2" />
                新建出库单
              </Button>
            </div>
          </Col>
        </Row>

        {/* 搜索表单 */}
        <Row className="mb-4">
          <Col>
            <Card className="border-0 shadow-sm">
              <Card.Body>
                <Form className="d-flex flex-wrap gap-3 align-items-end">
                  <Form.Group style={{ minWidth: '200px' }}>
                    <Form.Label>出库类型</Form.Label>
                    <Form.Select
                      value={searchForm.outbound_type}
                      onChange={(e) => setSearchForm(prev => ({ ...prev, outbound_type: e.target.value }))}
                    >
                      <option value="">全部</option>
                      <option value="requisition">领用出库</option>
                      <option value="sale">销售出库</option>
                      <option value="return">退货出库</option>
                      <option value="transfer">调拨出库</option>
                      <option value="other">其他出库</option>
                    </Form.Select>
                  </Form.Group>

                  <Form.Group style={{ minWidth: '200px' }}>
                    <Form.Label>状态</Form.Label>
                    <Form.Select
                      value={searchForm.status}
                      onChange={(e) => setSearchForm(prev => ({ ...prev, status: e.target.value }))}
                    >
                      <option value="">全部</option>
                      <option value="pending">待出库</option>
                      <option value="partial">部分出库</option>
                      <option value="completed">已完成</option>
                      <option value="cancelled">已取消</option>
                    </Form.Select>
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
                  data={outboundOrders}
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

export default OutboundList
