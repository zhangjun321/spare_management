import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Card, Button, Tag, Space, Input, Select, Modal, message, Tooltip } from 'antd'
import { PlusOutlined, EyeOutlined, PlayCircleOutlined, CheckCircleOutlined, DeleteOutlined } from '@ant-design/icons'
import { StockTakeService } from '../services/stockTake'
import axios from 'axios'

const { Search } = Input

const STATUS_MAP = {
  draft: { label: '草稿', color: 'default' },
  in_progress: { label: '进行中', color: 'blue' },
  completed: { label: '已完成', color: 'green' },
  cancelled: { label: '已取消', color: 'red' },
}

export default function StockTakeList() {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0 })
  const [filters, setFilters] = useState({ keyword: '', status: '', warehouse_id: '' })
  const [warehouses, setWarehouses] = useState([])

  const loadTasks = async () => {
    setLoading(true)
    const params = { page: pagination.page, per_page: pagination.per_page }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    if (filters.warehouse_id) params.warehouse_id = filters.warehouse_id

    const result = await StockTakeService.listTasks(params)
    if (result.success) {
      setTasks(result.data || [])
      setPagination((prev) => ({ ...prev, total: result.pagination?.total || 0 }))
    } else message.error(result.error || '加载失败')
    setLoading(false)
  }

  const loadWarehouses = async () => {
    try {
      const resp = await axios.get('/api/warehouses')
      if (resp.data?.success) setWarehouses(resp.data.data || [])
    } catch { /* ignore */ }
  }

  useEffect(() => { loadWarehouses() }, [])
  useEffect(() => { loadTasks() }, [pagination.page, pagination.per_page, filters])

  const handleStart = (id) => {
    Modal.confirm({
      title: '开始盘点', content: '确认开始盘点任务？',
      onOk: async () => {
        const result = await StockTakeService.startTask(id)
        if (result.success) { message.success('盘点任务已开始'); loadTasks() }
        else message.error(result.error || '启动失败')
      },
    })
  }

  const handleDelete = (id) => {
    Modal.confirm({
      title: '确认删除', content: '确定要删除这个盘点任务吗？',
      okText: '删除', okType: 'danger',
      onOk: async () => {
        const result = await StockTakeService.deleteTask(id)
        if (result.success) { message.success('删除成功'); loadTasks() }
        else message.error(result.error || '删除失败')
      },
    })
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '标题', dataIndex: 'title', key: 'title',
      render: (text, record) => <a onClick={() => navigate(`/stock-take/${record.id}`)}>{text}</a>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (s) => {
        const info = STATUS_MAP[s] || { label: s, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      },
    },
    {
      title: '盘点仓库', dataIndex: 'warehouse_name', key: 'warehouse_name', ellipsis: true,
    },
    {
      title: '盘点类型', dataIndex: 'type', key: 'type', width: 100,
      render: (v) => {
        const types = { full: '全面盘点', partial: '部分盘点', random: '抽盘' }
        return types[v] || v || '-'
      },
    },
    {
      title: '备件数', dataIndex: 'item_count', key: 'item_count', width: 80, align: 'center',
    },
    {
      title: '差异数', dataIndex: 'diff_count', key: 'diff_count', width: 80, align: 'center',
      render: (v) => v > 0 ? <Tag color="orange">{v}</Tag> : <span style={{ color: '#999' }}>0</span>,
    },
    {
      title: '创建人', dataIndex: 'creator_name', key: 'creator_name', width: 100,
    },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170,
      render: (v) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: '操作', key: 'actions', width: 200, fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="详情"><Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/stock-take/${record.id}`)} /></Tooltip>
          {record.status === 'draft' && (
            <Tooltip title="开始盘点">
              <Button size="small" type="primary" icon={<PlayCircleOutlined />} onClick={() => handleStart(record.id)}>
                开始
              </Button>
            </Tooltip>
          )}
          {record.status === 'in_progress' && (
            <Tooltip title="继续盘点">
              <Button size="small" type="primary" icon={<CheckCircleOutlined />} onClick={() => navigate(`/stock-take/${record.id}/execute`)}>
                盘点
              </Button>
            </Tooltip>
          )}
          {['draft', 'cancelled'].includes(record.status) && (
            <Tooltip title="删除"><Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} /></Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title="盘点任务管理"
        extra={
          <Space>
            <Button onClick={() => navigate('/stock-take/adjustments')}>调整单</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/stock-take/new')}>新建盘点</Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }} wrap>
          <Search placeholder="搜索标题" allowClear style={{ width: 240 }}
            onSearch={(v) => { setFilters((f) => ({ ...f, keyword: v })); setPagination((p) => ({ ...p, page: 1 })) }} />
          <Select placeholder="筛选状态" allowClear style={{ width: 140 }}
            value={filters.status || undefined}
            onChange={(v) => { setFilters((f) => ({ ...f, status: v || '' })); setPagination((p) => ({ ...p, page: 1 })) }}
            options={Object.entries(STATUS_MAP).map(([k, v]) => ({ value: k, label: v.label }))} />
          <Select placeholder="筛选仓库" allowClear style={{ width: 180 }}
            value={filters.warehouse_id || undefined}
            onChange={(v) => { setFilters((f) => ({ ...f, warehouse_id: v || '' })); setPagination((p) => ({ ...p, page: 1 })) }}
            options={warehouses.map((w) => ({ value: w.id, label: w.name }))}
            showSearch optionFilterProp="label" />
        </Space>
        <Table columns={columns} dataSource={tasks} rowKey="id" loading={loading}
          scroll={{ x: 1100 }}
          pagination={{
            current: pagination.page, pageSize: pagination.per_page, total: pagination.total,
            showSizeChanger: true, showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => setPagination((p) => ({ ...p, page, per_page: pageSize })),
          }} />
      </Card>
    </div>
  )
}
