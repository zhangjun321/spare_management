import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Space, message, Statistic, Row, Col, Modal, Input } from 'antd'
import { ArrowLeftOutlined, UnlockOutlined, ClockCircleOutlined, DeleteOutlined } from '@ant-design/icons'
import { ReservationService } from '../services/reservation'

const STATUS_MAP = {
  active: { label: '有效', color: 'green' },
  released: { label: '已释放', color: 'blue' },
  expired: { label: '已过期', color: 'red' },
}

export default function ReservationDetail() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [reservation, setReservation] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    const result = await ReservationService.get(id)
    if (result.success) setReservation(result.data)
    else message.error(result.error || '加载失败')
    setLoading(false)
  }

  useEffect(() => { loadData() }, [id])

  const handleRelease = () => {
    Modal.confirm({
      title: '确认释放', content: '释放后库存将恢复可用，确定继续？',
      okText: '释放', onOk: async () => {
        const result = await ReservationService.release(id)
        if (result.success) { message.success('释放成功'); loadData() }
        else message.error(result.error || '释放失败')
      },
    })
  }

  const handleExtend = () => {
    let days = 30
    Modal.confirm({
      title: '延长有效期',
      content: (
        <div>
          <p>请输入延长天数：</p>
          <Input type="number" id="extend-days-input" defaultValue={30} min={1}
            onChange={(e) => { days = parseInt(e.target.value) || 30 }} />
        </div>
      ),
      onOk: async () => {
        const result = await ReservationService.extend(id, days)
        if (result.success) { message.success('延长成功'); loadData() }
        else message.error(result.error || '延长失败')
      },
    })
  }

  const handleDelete = () => {
    Modal.confirm({
      title: '确认删除', content: '确定要删除这条预留记录吗？',
      okText: '删除', okType: 'danger',
      onOk: async () => {
        const result = await ReservationService.delete(id)
        if (result.success) { message.success('删除成功'); navigate('/reservations') }
        else message.error(result.error || '删除失败')
      },
    })
  }

  if (loading) return <Card loading={true} />
  if (!reservation) return <Card><p>预留不存在</p></Card>

  const statusInfo = STATUS_MAP[reservation.status] || { label: reservation.status, color: 'default' }

  return (
    <div>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/reservations')}>返回列表</Button>
            <span>预留详情</span>
            <Tag color={statusInfo.color}>{statusInfo.label}</Tag>
          </Space>
        }
        extra={
          reservation.status === 'active' && (
            <Space>
              <Button icon={<UnlockOutlined />} onClick={handleRelease}>释放</Button>
              <Button icon={<ClockCircleOutlined />} onClick={handleExtend}>延长</Button>
              <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>删除</Button>
            </Space>
          )
        }
      >
        <Row gutter={24} style={{ marginBottom: 24 }}>
          <Col span={6}><Statistic title="备件" value={reservation.spare_part_name || '-'} /></Col>
          <Col span={6}><Statistic title="预留数量" value={reservation.quantity} /></Col>
          <Col span={6}><Statistic title="项目/订单" value={reservation.project || '-'} /></Col>
          <Col span={6}><Statistic title="优先级" value={reservation.priority} /></Col>
        </Row>

        <Descriptions bordered column={2} size="small">
          <Descriptions.Item label="预留原因">{reservation.reason || '无'}</Descriptions.Item>
          <Descriptions.Item label="创建人">{reservation.creator_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{reservation.created_at ? new Date(reservation.created_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="到期时间">{reservation.expire_at ? new Date(reservation.expire_at).toLocaleString() : '-'}</Descriptions.Item>
          {reservation.released_at && (
            <Descriptions.Item label="释放时间">{new Date(reservation.released_at).toLocaleString()}</Descriptions.Item>
          )}
          {reservation.released_by_name && (
            <Descriptions.Item label="释放人">{reservation.released_by_name}</Descriptions.Item>
          )}
        </Descriptions>
      </Card>
    </div>
  )
}
