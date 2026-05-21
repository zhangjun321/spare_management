import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Card, Tag, Space, Button, message, Modal } from 'antd'
import { ArrowLeftOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons'
import { StockTakeService } from '../services/stockTake'

const STATUS_MAP = {
  pending: { label: '待审批', color: 'orange' },
  approved: { label: '已批准', color: 'green' },
  rejected: { label: '已驳回', color: 'red' },
  executed: { label: '已执行', color: 'blue' },
}

export default function AdjustmentsList() {
  const navigate = useNavigate()
  const [adjustments, setAdjustments] = useState([])
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    setLoading(true)
    const result = await StockTakeService.listAdjustments()
    if (result.success) setAdjustments(result.data || [])
    else message.error(result.error || '加载失败')
    setLoading(false)
  }

  useEffect(() => { loadData() }, [])

  const handleApprove = (id) => {
    Modal.confirm({
      title: '审批通过', content: '确认批准此调整单？',
      onOk: async () => {
        const result = await StockTakeService.approveAdjustment(id)
        if (result.success) { message.success('审批通过'); loadData() }
        else message.error(result.error || '审批失败')
      },
    })
  }

  const handleReject = (id) => {
    Modal.confirm({
      title: '驳回调整单', content: '确认驳回此调整单？',
      onOk: async () => {
        const result = await StockTakeService.rejectAdjustment(id, '审核不通过')
        if (result.success) { message.success('已驳回'); loadData() }
        else message.error(result.error || '操作失败')
      },
    })
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '盘点任务', dataIndex: 'stock_take_title', key: 'stock_take_title', ellipsis: true },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (s) => {
        const info = STATUS_MAP[s] || { label: s, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      },
    },
    { title: '备件', dataIndex: 'spare_part_name', key: 'spare_part_name' },
    {
      title: '类型', dataIndex: 'type', key: 'type', width: 80,
      render: (v) => v === 'surplus' ? <Tag color="orange">盘盈</Tag> : <Tag color="red">盘亏</Tag>,
    },
    {
      title: '调整数量', dataIndex: 'quantity', key: 'quantity', width: 100, align: 'center',
      render: (v, record) => (
        <span style={{ color: record.type === 'surplus' ? '#fa8c16' : '#ff4d4f', fontWeight: 'bold' }}>
          {record.type === 'surplus' ? '+' : ''}{Math.abs(v)}
        </span>
      ),
    },
    { title: '创建人', dataIndex: 'creator_name', key: 'creator_name', width: 100 },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170,
      render: (v) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: '操作', key: 'actions', width: 160, fixed: 'right',
      render: (_, record) => (
        record.status === 'pending' ? (
          <Space size="small">
            <Button size="small" type="primary" icon={<CheckOutlined />}
              style={{ background: '#52c41a', borderColor: '#52c41a' }}
              onClick={() => handleApprove(record.id)}>
              通过
            </Button>
            <Button size="small" danger icon={<CloseOutlined />}
              onClick={() => handleReject(record.id)}>
              驳回
            </Button>
          </Space>
        ) : null
      ),
    },
  ]

  return (
    <div>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/stock-take')}>返回盘点</Button>
            <span>调整单管理</span>
          </Space>
        }
      >
        <Table columns={columns} dataSource={adjustments} rowKey="id" loading={loading}
          scroll={{ x: 1000 }}
          pagination={{ showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }} />
      </Card>
    </div>
  )
}
