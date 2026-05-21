import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Card, Button, Tag, Space, Input, Select, Modal, message, Tooltip } from 'antd'
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, SendOutlined, CheckOutlined, CloseOutlined, CarOutlined, InboxOutlined } from '@ant-design/icons'
import { TransferOrderService } from '../services/transferOrder'
import axios from 'axios'

const { Search } = Input

const STATUS_MAP = {
  draft: { label: '草稿', color: 'default' },
  submitted: { label: '已提交', color: 'blue' },
  approved: { label: '已审批', color: 'cyan' },
  in_transit: { label: '在途', color: 'orange' },
  received: { label: '已收货', color: 'green' },
  completed: { label: '已完成', color: 'green' },
  rejected: { label: '已驳回', color: 'red' },
}

export default function TransferOrderList() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0 })
  const [filters, setFilters] = useState({ keyword: '', status: '', warehouse_id: '' })
  const [warehouses, setWarehouses] = useState([])

  const loadOrders = async () => {
    setLoading(true)
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    if (filters.warehouse_id) params.warehouse_id = filters.warehouse_id

    const result = await TransferOrderService.list(params)
    if (result.success) {
      setOrders(result.data || [])
      setPagination((prev) => ({ ...prev, total: result.pagination?.total || 0 }))
    } else {
      message.error(result.error || '加载失败')
    }
    setLoading(false)
  }

  const loadWarehouses = async () => {
    try {
      const resp = await axios.get('/api/warehouses')
      if (resp.data?.success) {
        setWarehouses(resp.data.data || [])
      }
    } catch { /* ignore */ }
  }

  useEffect(() => { loadWarehouses() }, [])
  useEffect(() => { loadOrders() }, [pagination.page, pagination.per_page, filters])

  const handleDelete = (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条调拨单吗？',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        const result = await TransferOrderService.delete(id)
        if (result.success) {
          message.success('删除成功')
          loadOrders()
        } else {
          message.error(result.error || '删除失败')
        }
      },
    })
  }

  const handleStatusAction = async (id, action, label) => {
    Modal.confirm({
      title: `确认${label}`,
      content: `确定要${label}这条调拨单吗？`,
      onOk: async () => {
        let result
        switch (action) {
          case 'submit': result = await TransferOrderService.submit(id); break
          case 'approve': result = await TransferOrderService.approve(id); break
          case 'reject':
            result = await TransferOrderService.reject(id, '审核不通过')
            break
          case 'ship': result = await TransferOrderService.ship(id); break
          case 'receive': result = await TransferOrderService.receive(id); break
          default: return
        }
        if (result.success) {
          message.success(`${label}成功`)
          loadOrders()
        } else {
          message.error(result.error || `${label}失败`)
        }
      },
    })
  }

  const columns = [
    {
      title: '单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 160,
      render: (text, record) => (
        <a onClick={() => navigate(`/transfer-orders/${record.id}`)}>{text || `TO-${record.id}`}</a>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (s) => {
        const info = STATUS_MAP[s] || { label: s, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      },
    },
    {
      title: '调出仓库',
      dataIndex: 'from_warehouse_name',
      key: 'from_warehouse_name',
      ellipsis: true,
    },
    {
      title: '调入仓库',
      dataIndex: 'to_warehouse_name',
      key: 'to_warehouse_name',
      ellipsis: true,
    },
    {
      title: '备件种类',
      dataIndex: 'item_count',
      key: 'item_count',
      width: 90,
      align: 'center',
    },
    {
      title: '创建人',
      dataIndex: 'creator_name',
      key: 'creator_name',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (v) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
      width: 120,
    },
    {
      title: '操作',
      key: 'actions',
      width: 260,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="详情">
            <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/transfer-orders/${record.id}`)} />
          </Tooltip>
          {record.status === 'draft' && (
            <>
              <Tooltip title="编辑">
                <Button size="small" icon={<EditOutlined />} onClick={() => navigate(`/transfer-orders/${record.id}/edit`)} />
              </Tooltip>
              <Tooltip title="提交审批">
                <Button size="small" type="primary" icon={<SendOutlined />} onClick={() => handleStatusAction(record.id, 'submit', '提交审批')}>
                  提交
                </Button>
              </Tooltip>
            </>
          )}
          {record.status === 'submitted' && (
            <>
              <Tooltip title="审批通过">
                <Button size="small" type="primary" icon={<CheckOutlined />} style={{ background: '#52c41a', borderColor: '#52c41a' }} onClick={() => handleStatusAction(record.id, 'approve', '审批通过')}>
                  通过
                </Button>
              </Tooltip>
              <Tooltip title="驳回">
                <Button size="small" danger icon={<CloseOutlined />} onClick={() => handleStatusAction(record.id, 'reject', '驳回')}>
                  驳回
                </Button>
              </Tooltip>
            </>
          )}
          {record.status === 'approved' && (
            <Tooltip title="发货">
              <Button size="small" type="primary" icon={<CarOutlined />} onClick={() => handleStatusAction(record.id, 'ship', '发货')}>
                发货
              </Button>
            </Tooltip>
          )}
          {record.status === 'in_transit' && (
            <Tooltip title="确认收货">
              <Button size="small" type="primary" icon={<InboxOutlined />} style={{ background: '#52c41a', borderColor: '#52c41a' }} onClick={() => handleStatusAction(record.id, 'receive', '确认收货')}>
                收货
              </Button>
            </Tooltip>
          )}
          {['draft'].includes(record.status) && (
            <Tooltip title="删除">
              <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title="调拨单管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/transfer-orders/new')}>
            新建调拨单
          </Button>
        }
      >
        <Space style={{ marginBottom: 16 }} wrap>
          <Search
            placeholder="搜索单号/备注"
            allowClear
            style={{ width: 240 }}
            onSearch={(v) => { setFilters((f) => ({ ...f, keyword: v })); setPagination((p) => ({ ...p, page: 1 })) }}
          />
          <Select
            placeholder="筛选状态"
            allowClear
            style={{ width: 140 }}
            value={filters.status || undefined}
            onChange={(v) => { setFilters((f) => ({ ...f, status: v || '' })); setPagination((p) => ({ ...p, page: 1 })) }}
            options={Object.entries(STATUS_MAP).map(([k, v]) => ({ value: k, label: v.label }))}
          />
          <Select
            placeholder="筛选仓库"
            allowClear
            style={{ width: 180 }}
            value={filters.warehouse_id || undefined}
            onChange={(v) => { setFilters((f) => ({ ...f, warehouse_id: v || '' })); setPagination((p) => ({ ...p, page: 1 })) }}
            options={warehouses.map((w) => ({ value: w.id, label: w.name }))}
            showSearch
            optionFilterProp="label"
          />
        </Space>
        <Table
          columns={columns}
          dataSource={orders}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1300 }}
          pagination={{
            current: pagination.page,
            pageSize: pagination.per_page,
            total: pagination.total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => setPagination((p) => ({ ...p, page, per_page: pageSize })),
          }}
        />
      </Card>
    </div>
  )
}
