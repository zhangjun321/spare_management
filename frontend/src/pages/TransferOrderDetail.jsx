import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Descriptions, Table, Tag, Button, Space, message, Timeline, Row, Col, Statistic, Modal, Input } from 'antd'
import { ArrowLeftOutlined, EditOutlined, SendOutlined, CheckOutlined, CloseOutlined, CarOutlined, InboxOutlined, DeleteOutlined } from '@ant-design/icons'
import { TransferOrderService } from '../services/transferOrder'

const STATUS_MAP = {
  draft: { label: '草稿', color: 'default' },
  submitted: { label: '已提交', color: 'blue' },
  approved: { label: '已审批', color: 'cyan' },
  in_transit: { label: '在途', color: 'orange' },
  received: { label: '已收货', color: 'green' },
  completed: { label: '已完成', color: 'green' },
  rejected: { label: '已驳回', color: 'red' },
}

export default function TransferOrderDetail() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadOrder = async () => {
    setLoading(true)
    const result = await TransferOrderService.get(id)
    if (result.success) {
      setOrder(result.data)
    } else {
      message.error(result.error || '加载失败')
    }
    setLoading(false)
  }

  useEffect(() => { loadOrder() }, [id])

  const handleAction = async (action, label, extraData) => {
    let result
    switch (action) {
      case 'submit': result = await TransferOrderService.submit(id); break
      case 'approve': result = await TransferOrderService.approve(id); break
      case 'ship': result = await TransferOrderService.ship(id); break
      case 'receive': result = await TransferOrderService.receive(id); break
      case 'reject':
        result = await TransferOrderService.reject(id, extraData?.reason || '审核不通过')
        break
      case 'delete':
        result = await TransferOrderService.delete(id)
        break
      default: return
    }
    if (result.success) {
      message.success(`${label}成功`)
      if (action === 'delete') {
        navigate('/transfer-orders')
      } else {
        loadOrder()
      }
    } else {
      message.error(result.error || `${label}失败`)
    }
  }

  const handleReject = () => {
    let reason = ''
    Modal.confirm({
      title: '驳回调拨单',
      content: (
        <Input.TextArea
          placeholder="请输入驳回原因"
          rows={3}
          onChange={(e) => { reason = e.target.value }}
        />
      ),
      onOk: () => handleAction('reject', '驳回', { reason }),
    })
  }

  if (loading) return <Card loading={true} />
  if (!order) return <Card><p>调拨单不存在</p></Card>

  const statusInfo = STATUS_MAP[order.status] || { label: order.status, color: 'default' }

  const itemColumns = [
    { title: '备件名称', dataIndex: 'spare_part_name', key: 'spare_part_name' },
    { title: 'SKU', dataIndex: 'spare_part_sku', key: 'spare_part_sku', width: 120 },
    { title: '调拨数量', dataIndex: 'quantity', key: 'quantity', width: 100, align: 'center' },
    { title: '实收数量', dataIndex: 'received_quantity', key: 'received_quantity', width: 100, align: 'center' },
    { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
  ]

  return (
    <div>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/transfer-orders')}>返回列表</Button>
            <span>调拨单详情</span>
            <Tag color={statusInfo.color}>{statusInfo.label}</Tag>
          </Space>
        }
        extra={
          <Space>
            {order.status === 'draft' && (
              <>
                <Button icon={<EditOutlined />} onClick={() => navigate(`/transfer-orders/${id}/edit`)}>编辑</Button>
                <Button type="primary" icon={<SendOutlined />} onClick={() => handleAction('submit', '提交审批')}>提交审批</Button>
                <Button danger icon={<DeleteOutlined />} onClick={() => {
                  Modal.confirm({
                    title: '确认删除',
                    content: '确定要删除这条调拨单吗？',
                    okText: '删除', okType: 'danger',
                    onOk: () => handleAction('delete', '删除'),
                  })
                }}>删除</Button>
              </>
            )}
            {order.status === 'submitted' && (
              <>
                <Button type="primary" icon={<CheckOutlined />} style={{ background: '#52c41a', borderColor: '#52c41a' }} onClick={() => handleAction('approve', '审批通过')}>审批通过</Button>
                <Button danger icon={<CloseOutlined />} onClick={handleReject}>驳回</Button>
              </>
            )}
            {order.status === 'approved' && (
              <Button type="primary" icon={<CarOutlined />} onClick={() => handleAction('ship', '发货')}>确认发货</Button>
            )}
            {order.status === 'in_transit' && (
              <Button type="primary" icon={<InboxOutlined />} style={{ background: '#52c41a', borderColor: '#52c41a' }} onClick={() => handleAction('receive', '确认收货')}>确认收货</Button>
            )}
          </Space>
        }
      >
        <Row gutter={24} style={{ marginBottom: 24 }}>
          <Col span={6}><Statistic title="单号" value={order.order_no || `TO-${order.id}`} /></Col>
          <Col span={6}><Statistic title="调出仓库" value={order.from_warehouse_name || '-'} /></Col>
          <Col span={6}><Statistic title="调入仓库" value={order.to_warehouse_name || '-'} /></Col>
          <Col span={6}><Statistic title="创建人" value={order.creator_name || '-'} /></Col>
        </Row>

        <Descriptions bordered column={2} size="small" style={{ marginBottom: 24 }}>
          <Descriptions.Item label="创建时间">{order.created_at ? new Date(order.created_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="更新时间">{order.updated_at ? new Date(order.updated_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="提交时间">{order.submitted_at ? new Date(order.submitted_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="发货时间">{order.shipped_at ? new Date(order.shipped_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="收货时间">{order.received_at ? new Date(order.received_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="完成时间">{order.completed_at ? new Date(order.completed_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="备注" span={2}>{order.remark || '无'}</Descriptions.Item>
        </Descriptions>

        <h4>调拨明细</h4>
        <Table
          columns={itemColumns}
          dataSource={order.items || []}
          rowKey="id"
          pagination={false}
          size="small"
          style={{ marginBottom: 24 }}
        />

        {(order.logs && order.logs.length > 0) && (
          <>
            <h4>操作日志</h4>
            <Timeline
              items={(order.logs || []).map((log) => ({
                children: (
                  <span>
                    <strong>{log.operator_name || '系统'}</strong>
                    {' '}{log.action_desc || log.action}
                    {log.remark ? ` - ${log.remark}` : ''}
                    <br />
                    <small style={{ color: '#999' }}>{log.created_at ? new Date(log.created_at).toLocaleString() : ''}</small>
                  </span>
                ),
              }))}
            />
          </>
        )}
      </Card>
    </div>
  )
}
