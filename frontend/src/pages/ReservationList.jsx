import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Card, Button, Tag, Space, Input, Select, message, Modal, Tooltip } from 'antd'
import { PlusOutlined, EyeOutlined, DeleteOutlined, UnlockOutlined, ClockCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { ReservationService } from '../services/reservation'
import axios from 'axios'

const { Search } = Input

const STATUS_MAP = {
  active: { label: '有效', color: 'green' },
  released: { label: '已释放', color: 'blue' },
  expired: { label: '已过期', color: 'red' },
}

export default function ReservationList() {
  const navigate = useNavigate()
  const [reservations, setReservations] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0 })
  const [filters, setFilters] = useState({ keyword: '', status: '' })
  const [spareParts, setSpareParts] = useState([])

  const loadData = async () => {
    setLoading(true)
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status

    const result = await ReservationService.list(params)
    if (result.success) {
      setReservations(result.data || [])
      setPagination((prev) => ({ ...prev, total: result.pagination?.total || 0 }))
    } else {
      message.error(result.error || '加载失败')
    }
    setLoading(false)
  }

  const loadSpareParts = async () => {
    try {
      const resp = await axios.get('/api/spare-parts', { params: { per_page: 500 } })
      if (resp.data?.success) setSpareParts(resp.data.data || [])
    } catch { /* ignore */ }
  }

  useEffect(() => { loadSpareParts() }, [])
  useEffect(() => { loadData() }, [pagination.page, pagination.per_page, filters])

  const handleRelease = (id) => {
    Modal.confirm({
      title: '确认释放',
      content: '确定要释放这条预留吗？释放后库存将恢复可用。',
      okText: '释放',
      okType: 'primary',
      onOk: async () => {
        const result = await ReservationService.release(id)
        if (result.success) { message.success('释放成功'); loadData() }
        else message.error(result.error || '释放失败')
      },
    })
  }

  const handleExtend = (id) => {
    Modal.confirm({
      title: '延长有效期',
      content: (
        <div>
          <p>请输入延长天数：</p>
          <Input type="number" id="extend-days" defaultValue={30} min={1} />
        </div>
      ),
      onOk: async () => {
        const days = parseInt(document.getElementById('extend-days')?.value || 30)
        const result = await ReservationService.extend(id, days)
        if (result.success) { message.success('延长成功'); loadData() }
        else message.error(result.error || '延长失败')
      },
    })
  }

  const handleDelete = (id) => {
    Modal.confirm({
      title: '确认删除', content: '确定要删除这条预留记录吗？',
      okText: '删除', okType: 'danger',
      onOk: async () => {
        const result = await ReservationService.delete(id)
        if (result.success) { message.success('删除成功'); loadData() }
        else message.error(result.error || '删除失败')
      },
    })
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '备件', dataIndex: 'spare_part_name', key: 'spare_part_name',
      render: (text, record) => (
        <a onClick={() => navigate(`/reservations/${record.id}`)}>{text || `备件#${record.spare_part_id}`}</a>
      ),
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (s) => {
        const info = STATUS_MAP[s] || { label: s, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      },
    },
    { title: '预留数量', dataIndex: 'quantity', key: 'quantity', width: 90, align: 'center' },
    { title: '项目/订单', dataIndex: 'project', key: 'project', ellipsis: true },
    { title: '预留原因', dataIndex: 'reason', key: 'reason', ellipsis: true, width: 150 },
    { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80, align: 'center' },
    {
      title: '到期时间', dataIndex: 'expire_at', key: 'expire_at', width: 170,
      render: (v) => v ? new Date(v).toLocaleString() : '-',
      sorter: (a, b) => new Date(a.expire_at) - new Date(b.expire_at),
    },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170,
      render: (v) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: '操作', key: 'actions', width: 200, fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="详情"><Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/reservations/${record.id}`)} /></Tooltip>
          {record.status === 'active' && (
            <>
              <Tooltip title="释放"><Button size="small" icon={<UnlockOutlined />} onClick={() => handleRelease(record.id)}>释放</Button></Tooltip>
              <Tooltip title="延长有效期"><Button size="small" icon={<ClockCircleOutlined />} onClick={() => handleExtend(record.id)}>延长</Button></Tooltip>
            </>
          )}
          {record.status === 'active' && (
            <Tooltip title="删除"><Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} /></Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title="库存预留管理"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/reservations/new')}>新建预留</Button>}
      >
        <Space style={{ marginBottom: 16 }} wrap>
          <Search placeholder="搜索项目/原因" allowClear style={{ width: 240 }}
            onSearch={(v) => { setFilters((f) => ({ ...f, keyword: v })); setPagination((p) => ({ ...p, page: 1 })) }} />
          <Select placeholder="筛选状态" allowClear style={{ width: 140 }}
            value={filters.status || undefined}
            onChange={(v) => { setFilters((f) => ({ ...f, status: v || '' })); setPagination((p) => ({ ...p, page: 1 })) }}
            options={Object.entries(STATUS_MAP).map(([k, v]) => ({ value: k, label: v.label }))} />
        </Space>
        <Table columns={columns} dataSource={reservations} rowKey="id" loading={loading}
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
