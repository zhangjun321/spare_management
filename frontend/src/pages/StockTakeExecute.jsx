import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Table, Button, Space, message, InputNumber, Tag, Statistic, Row, Col, Modal } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, SaveOutlined } from '@ant-design/icons'
import { StockTakeService } from '../services/stockTake'

export default function StockTakeExecute() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [task, setTask] = useState(null)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const loadData = async () => {
    setLoading(true)
    const [taskResult, itemsResult] = await Promise.all([
      StockTakeService.getTask(id),
      StockTakeService.listItems(id),
    ])
    if (taskResult.success) setTask(taskResult.data)
    else message.error(taskResult.error || '加载失败')

    if (itemsResult.success) {
      setItems((itemsResult.data || []).map((item) => ({
        ...item,
        _counted: item.actual_quantity !== null && item.actual_quantity !== undefined
          ? item.actual_quantity
          : null,
      })))
    }
    setLoading(false)
  }

  useEffect(() => { loadData() }, [id])

  const updateQuantity = (itemId, value) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, _counted: value } : item
      )
    )
  }

  const handleSave = async () => {
    setSaving(true)
    const updates = items
      .filter((item) => item._counted !== null)
      .map((item) => ({
        id: item.id,
        actual_quantity: item._counted,
      }))

    if (updates.length === 0) {
      message.warning('请至少录入一个盘点数量')
      setSaving(false)
      return
    }

    const result = await StockTakeService.batchUpdateItems(id, updates)
    if (result.success) {
      message.success(`已保存 ${updates.length} 条盘点记录`)
      loadData()
    } else {
      message.error(result.error || '保存失败')
    }
    setSaving(false)
  }

  const handleComplete = () => {
    const unCounted = items.filter((item) => item._counted === null && item.actual_quantity === null)
    if (unCounted.length > 0) {
      message.warning(`还有 ${unCounted.length} 个备件未录入盘点数量`)
      return
    }

    Modal.confirm({
      title: '完成盘点',
      content: '确认完成盘点？完成后将生成差异报告。',
      okText: '确认完成',
      onOk: async () => {
        // Save first, then complete
        const updates = items
          .filter((item) => item._counted !== null)
          .map((item) => ({ id: item.id, actual_quantity: item._counted }))
        if (updates.length > 0) {
          await StockTakeService.batchUpdateItems(id, updates)
        }
        const result = await StockTakeService.completeTask(id)
        if (result.success) {
          message.success('盘点完成！')
          navigate(`/stock-take/${id}`)
        } else {
          message.error(result.error || '完成失败')
        }
      },
    })
  }

  const countedCount = items.filter((i) => i._counted !== null).length
  const diffCount = items.filter((i) =>
    i._counted !== null && i._counted !== i.system_quantity
  ).length

  const columns = [
    { title: '#', dataIndex: 'id', key: 'id', width: 50 },
    {
      title: '备件', dataIndex: 'spare_part_name', key: 'spare_part_name',
      render: (text, record) => text || `备件#${record.spare_part_id}`,
    },
    { title: 'SKU', dataIndex: 'spare_part_sku', key: 'spare_part_sku', width: 120 },
    {
      title: '系统库存', dataIndex: 'system_quantity', key: 'system_quantity',
      width: 100, align: 'center',
    },
    {
      title: '盘点数量', key: 'actual', width: 160, align: 'center',
      render: (_, record) => (
        <InputNumber
          min={0}
          value={record._counted}
          onChange={(v) => updateQuantity(record.id, v)}
          placeholder="录入"
          style={{ width: 120 }}
          status={
            record._counted !== null && record._counted !== record.system_quantity
              ? 'warning'
              : record._counted !== null
                ? ''
                : undefined
          }
        />
      ),
    },
    {
      title: '差异', key: 'diff', width: 80, align: 'center',
      render: (_, record) => {
        if (record._counted === null) return <span style={{ color: '#999' }}>-</span>
        const diff = record._counted - record.system_quantity
        if (diff === 0) return <Tag color="green">0</Tag>
        return <Tag color="red">{diff > 0 ? `+${diff}` : diff}</Tag>
      },
    },
    { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
  ]

  if (!task) return <Card loading={true} />

  return (
    <div>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/stock-take/${id}`)}>返回详情</Button>
            <span>执行盘点: {task.title}</span>
            <Tag color="blue">进行中</Tag>
          </Space>
        }
      >
        <Row gutter={24} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic title="总项数" value={items.length} />
          </Col>
          <Col span={6}>
            <Statistic title="已盘点" value={countedCount}
              suffix={`/ ${items.length}`}
              valueStyle={{ color: countedCount === items.length ? '#52c41a' : '#1890ff' }} />
          </Col>
          <Col span={6}>
            <Statistic title="差异项" value={diffCount}
              valueStyle={{ color: diffCount > 0 ? '#ff4d4f' : '#52c41a' }} />
          </Col>
          <Col span={6}>
            <Statistic title="盘点仓库" value={task.warehouse_name || '-'} />
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="middle"
          style={{ marginBottom: 24 }}
        />

        <Space>
          <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} loading={saving}>
            保存盘点记录
          </Button>
          <Button type="primary" icon={<CheckCircleOutlined />}
            style={{ background: '#52c41a', borderColor: '#52c41a' }}
            onClick={handleComplete} loading={saving}>
            完成盘点
          </Button>
          <Button onClick={() => navigate(`/stock-take/${id}`)}>返回</Button>
        </Space>
      </Card>
    </div>
  )
}
