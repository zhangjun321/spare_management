import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Descriptions, Table, Tag, Button, Space, message, Row, Col, Statistic } from 'antd'
import { ArrowLeftOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { StockTakeService } from '../services/stockTake'

const STATUS_MAP = {
  draft: { label: '草稿', color: 'default' },
  in_progress: { label: '进行中', color: 'blue' },
  completed: { label: '已完成', color: 'green' },
  cancelled: { label: '已取消', color: 'red' },
}

export default function StockTakeDetail() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [task, setTask] = useState(null)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    const [taskResult, itemsResult] = await Promise.all([
      StockTakeService.getTask(id),
      StockTakeService.listItems(id),
    ])
    if (taskResult.success) setTask(taskResult.data)
    else message.error(taskResult.error || '加载失败')
    if (itemsResult.success) setItems(itemsResult.data || [])
    setLoading(false)
  }

  useEffect(() => { loadData() }, [id])

  const handleStart = async () => {
    const result = await StockTakeService.startTask(id)
    if (result.success) {
      message.success('盘点任务已开始')
      navigate(`/stock-take/${id}/execute`)
    } else {
      message.error(result.error || '启动失败')
    }
  }

  if (loading) return <Card loading={true} />
  if (!task) return <Card><p>盘点任务不存在</p></Card>

  const statusInfo = STATUS_MAP[task.status] || { label: task.status, color: 'default' }
  const diffItems = items.filter((i) =>
    i.actual_quantity !== null && i.actual_quantity !== i.system_quantity
  )

  const itemColumns = [
    { title: '备件', dataIndex: 'spare_part_name', key: 'spare_part_name' },
    { title: 'SKU', dataIndex: 'spare_part_sku', key: 'spare_part_sku', width: 120 },
    { title: '系统库存', dataIndex: 'system_quantity', key: 'system_quantity', width: 100, align: 'center' },
    {
      title: '盘点数量', dataIndex: 'actual_quantity', key: 'actual_quantity', width: 100, align: 'center',
      render: (v) => v !== null && v !== undefined ? v : <span style={{ color: '#999' }}>未录入</span>,
    },
    {
      title: '差异', key: 'diff', width: 80, align: 'center',
      render: (_, record) => {
        if (record.actual_quantity === null || record.actual_quantity === undefined) return '-'
        const diff = record.actual_quantity - record.system_quantity
        if (diff === 0) return <Tag color="green">0</Tag>
        return <Tag color="red">{diff > 0 ? `+${diff}` : diff}</Tag>
      },
    },
    { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
  ]

  return (
    <div>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/stock-take')}>返回列表</Button>
            <span>盘点任务详情</span>
            <Tag color={statusInfo.color}>{statusInfo.label}</Tag>
          </Space>
        }
        extra={
          task.status === 'draft' && (
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>
              开始盘点
            </Button>
          )
        }
      >
        <Row gutter={24} style={{ marginBottom: 24 }}>
          <Col span={6}><Statistic title="盘点仓库" value={task.warehouse_name || '-'} /></Col>
          <Col span={6}>
            <Statistic title="盘点类型" value={
              { full: '全面盘点', partial: '部分盘点', random: '抽盘' }[task.type] || task.type || '-'
            } />
          </Col>
          <Col span={6}><Statistic title="总项数" value={items.length} /></Col>
          <Col span={6}>
            <Statistic title="差异项" value={diffItems.length}
              valueStyle={{ color: diffItems.length > 0 ? '#ff4d4f' : '#52c41a' }} />
          </Col>
        </Row>

        <Descriptions bordered column={2} size="small" style={{ marginBottom: 24 }}>
          <Descriptions.Item label="创建人">{task.creator_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{task.created_at ? new Date(task.created_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="开始时间">{task.started_at ? new Date(task.started_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="完成时间">{task.completed_at ? new Date(task.completed_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="备注" span={2}>{task.remark || '无'}</Descriptions.Item>
        </Descriptions>

        <h4>盘点明细</h4>
        <Table columns={itemColumns} dataSource={items} rowKey="id"
          loading={loading} pagination={false} size="small"
          style={{ marginBottom: task.status === 'completed' && diffItems.length > 0 ? 24 : 0 }}
        />

        {task.status === 'completed' && diffItems.length > 0 && (
          <Card title="差异汇总" size="small" style={{ marginTop: 16, background: '#fff7e6' }}>
            <Table
              columns={[
                ...itemColumns.filter((c) => c.key !== 'remark'),
                {
                  title: '建议操作', key: 'suggestion', width: 120,
                  render: (_, record) => {
                    const diff = record.actual_quantity - record.system_quantity
                    return diff > 0
                      ? <Tag color="orange">盘盈 +{diff}</Tag>
                      : <Tag color="red">盘亏 {diff}</Tag>
                  },
                },
              ]}
              dataSource={diffItems}
              rowKey="id"
              pagination={false}
              size="small"
            />
            <div style={{ marginTop: 12 }}>
              <Button onClick={() => navigate('/stock-take/adjustments')}>
                查看调整单
              </Button>
            </div>
          </Card>
        )}
      </Card>
    </div>
  )
}
