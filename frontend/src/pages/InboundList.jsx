import React, { useState, useEffect, useCallback } from 'react'
import { Container, Row, Col, Card, Button, Badge, Form } from 'react-bootstrap'
import { FaPlus, FaSearch, FaUndo, FaEye, FaCheck, FaTimes } from 'react-icons/fa'
import { useNavigate } from 'react-router-dom'
import { Table, StatCard, Button as CustomButton } from '@/components'
import { useUIStore } from '@/stores'
import { inboundOrderService } from '@/services/warehouse'
import MainLayout from '@/layouts/MainLayout'
import Footer from '@/components/Footer'
import InboundCarousel from '@/components/InboundCarousel'
import { Modal, message as antMessage } from 'antd'

const InboundList = () => {
  const navigate = useNavigate()
  const { setLoading } = useUIStore()
  
  const [loading, setLoadingLocal] = useState(false)
  const [inboundOrders, setInboundOrders] = useState([])
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0
  })
  const [searchForm, setSearchForm] = useState({
    inbound_type: '',
    status: ''
  })

  const loadInboundOrders = useCallback(async () => {
    try {
      setLoadingLocal(true)
      setLoading(true)
      
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...searchForm
      }
      
      const response = await inboundOrderService.getList(params)
      
      if (response.success) {
        setInboundOrders(response.data.items)
        setPagination(prev => ({
          ...prev,
          total: response.data.total
        }))
      }
    } catch (error) {
      console.error('加载入库数据失败:', error)
      // 不显示弹出框，静默处理错误
    } finally {
      setLoadingLocal(false)
      setLoading(false)
    }
  }, [pagination.page, pagination.per_page, searchForm, setLoading])

  useEffect(() => {
    loadInboundOrders()
  }, [loadInboundOrders])

  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page: 1 }))
    loadInboundOrders()
  }

  const handleReset = () => {
    setSearchForm({ inbound_type: '', status: '' })
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleCreate = () => {
    navigate('/warehouse/inbound/create')
  }

  const handleViewDetail = (row) => {
    navigate(`/warehouse/inbound/${row.id}`)
  }

  const handleComplete = async (row) => {
    Modal.confirm({
      title: '确认完成入库',
      content: '确定要完成该入库单吗？',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await inboundOrderService.complete(row.id)
          if (response.success) {
            antMessage.success('入库完成')
            loadInboundOrders()
          } else {
            antMessage.error(response.error || '操作失败')
          }
        } catch (error) {
          console.error('完成入库失败:', error)
          antMessage.error('操作失败')
        }
      }
    })
  }

  const handleCancel = async (row) => {
    Modal.confirm({
      title: '确认取消',
      content: '确定要取消该入库单吗？',
      okText: '确认取消',
      okType: 'danger',
      cancelText: '返回',
      onOk: async () => {
        try {
          const response = await inboundOrderService.cancel(row.id)
          if (response.success) {
            antMessage.success('已取消')
            loadInboundOrders()
          } else {
            antMessage.error(response.error || '操作失败')
          }
        } catch (error) {
          console.error('取消入库失败:', error)
          antMessage.error('操作失败')
        }
      }
    })
  }

  const getTypeLabel = (type) => {
    const map = {
      purchase: '采购入库',
      return: '退货入库',
      transfer: '调拨入库',
      other: '其他入库'
    }
    return map[type] || type
  }

  const getTypeBadgeVariant = (type) => {
    const map = {
      purchase: 'primary',
      return: 'info',
      transfer: 'success',
      other: 'secondary'
    }
    return map[type] || 'secondary'
  }

  const getStatusLabel = (status) => {
    const map = {
      pending: '待入库',
      partial: '部分入库',
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
      title: '入库单号',
      width: 160
    },
    {
      key: 'inbound_type',
      title: '入库类型',
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
      title: '入库数量',
      width: 100
    },
    {
      key: 'received_quantity',
      title: '实收数量',
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
      <CustomButton.Button
        variant="outline-primary"
        size="sm"
        icon={<FaEye />}
        onClick={() => handleViewDetail(item)}
      >
        详情
      </CustomButton.Button>
      
      {item.status === 'pending' && (
        <CustomButton.Button
          variant="outline-success"
          size="sm"
          icon={<FaCheck />}
          onClick={() => handleComplete(item)}
        >
          完成入库
        </CustomButton.Button>
      )}
      
      {item.status !== 'completed' && item.status !== 'cancelled' && (
        <CustomButton.Button
          variant="outline-danger"
          size="sm"
          icon={<FaTimes />}
          onClick={() => handleCancel(item)}
        >
          取消
        </CustomButton.Button>
      )}
    </>
  )

  return (
    <MainLayout showSidebar={true} showHeader={true}>
      <div className="position-relative" style={{ minHeight: 'calc(100vh - 120px)' }}>
        {/* 轮播图 */}
        <div className="container-fluid px-0 mb-4">
          <InboundCarousel />
        </div>

        {/* 页面头部 */}
        <Row className="mb-4">
          <Col>
            <div className="d-flex justify-content-between align-items-center">
              <h2 className="mb-0">📥 入库管理</h2>
              <Button variant="primary" onClick={handleCreate}>
                <FaPlus className="me-2" />
                新建入库单
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
                    <Form.Label>入库类型</Form.Label>
                    <Form.Select
                      value={searchForm.inbound_type}
                      onChange={(e) => setSearchForm(prev => ({ ...prev, inbound_type: e.target.value }))}
                    >
                      <option value="">全部</option>
                      <option value="purchase">采购入库</option>
                      <option value="return">退货入库</option>
                      <option value="transfer">调拨入库</option>
                      <option value="other">其他入库</option>
                    </Form.Select>
                  </Form.Group>

                  <Form.Group style={{ minWidth: '200px' }}>
                    <Form.Label>状态</Form.Label>
                    <Form.Select
                      value={searchForm.status}
                      onChange={(e) => setSearchForm(prev => ({ ...prev, status: e.target.value }))}
                    >
                      <option value="">全部</option>
                      <option value="pending">待入库</option>
                      <option value="partial">部分入库</option>
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
                  data={inboundOrders}
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

export default InboundList
