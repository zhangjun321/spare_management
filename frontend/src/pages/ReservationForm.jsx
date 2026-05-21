import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Form, Input, Select, Button, InputNumber, Space, message, Divider, Row, Col } from 'antd'
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons'
import { ReservationService } from '../services/reservation'
import axios from 'axios'

const { TextArea } = Input

export default function ReservationForm() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const [spareParts, setSpareParts] = useState([])
  const [selectedPart, setSelectedPart] = useState(null)

  useEffect(() => { loadSpareParts() }, [])

  const loadSpareParts = async () => {
    try {
      const resp = await axios.get('/api/spare-parts', { params: { per_page: 500 } })
      if (resp.data?.success) setSpareParts(resp.data.data || [])
    } catch { /* ignore */ }
  }

  const handlePartChange = (value) => {
    const part = spareParts.find((p) => p.id === value)
    setSelectedPart(part)
  }

  const handleSubmit = async (values) => {
    setSubmitting(true)
    const result = await ReservationService.create(values)
    if (result.success) {
      message.success('预留创建成功')
      navigate('/reservations')
    } else {
      message.error(result.error || '创建失败')
    }
    setSubmitting(false)
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/reservations')}>返回</Button>
            <span>新建库存预留</span>
          </Space>
        }
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}
          initialValues={{ expire_days: 30, priority: 5 }}>
          <Divider orientation="left">预留信息</Divider>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item name="spare_part_id" label="备件"
                rules={[{ required: true, message: '请选择备件' }]}>
                <Select placeholder="选择要预留的备件" showSearch
                  optionFilterProp="label"
                  filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  onChange={handlePartChange}>
                  {spareParts.map((sp) => (
                    <Select.Option key={sp.id} value={sp.id} label={`${sp.name} (${sp.sku || sp.code || ''})`}>
                      {sp.name} {sp.sku ? `(${sp.sku})` : ''} - 库存: {sp.quantity || 0}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="quantity" label="预留数量"
                rules={[{ required: true, message: '请输入数量' }]}>
                <InputNumber placeholder="数量" min={1} style={{ width: '100%' }}
                  max={selectedPart?.quantity} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="priority" label="优先级"
                rules={[{ required: true, message: '请选择优先级' }]}>
                <Select>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((p) => (
                    <Select.Option key={p} value={p}>{p} {p >= 8 ? '(高)' : p <= 3 ? '(低)' : ''}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item name="project" label="项目/订单"
                rules={[{ required: true, message: '请输入项目或订单名称' }]}>
                <Input placeholder="例如: 项目X / 订单#12345" maxLength={100} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="expire_days" label="有效天数"
                rules={[{ required: true, message: '请输入有效天数' }]}>
                <InputNumber placeholder="天" min={1} max={365} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="预计到期">
                <Input value={selectedPart ? `${selectedPart.quantity - (form.getFieldValue('quantity') || 0)} 可用` : '-'} disabled />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="reason" label="预留原因">
            <TextArea rows={3} placeholder="说明预留原因" maxLength={500} showCount />
          </Form.Item>

          <Divider />
          <Space>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={submitting}>创建预留</Button>
            <Button onClick={() => navigate('/reservations')}>取消</Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}
