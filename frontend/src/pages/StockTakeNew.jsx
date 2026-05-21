import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Form, Input, Select, Button, InputNumber, Space, message, Divider, Row, Col } from 'antd'
import { ArrowLeftOutlined, PlusOutlined } from '@ant-design/icons'
import { StockTakeService } from '../services/stockTake'
import axios from 'axios'

export default function StockTakeNew() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const [warehouses, setWarehouses] = useState([])
  const [spareParts, setSpareParts] = useState([])

  useEffect(() => {
    const load = async () => {
      try {
        const [wResp, spResp] = await Promise.all([
          axios.get('/api/warehouses'),
          axios.get('/api/spare-parts', { params: { per_page: 500 } }),
        ])
        if (wResp.data?.success) setWarehouses(wResp.data.data || [])
        if (spResp.data?.success) setSpareParts(spResp.data.data || [])
      } catch { /* ignore */ }
    }
    load()
  }, [])

  const handleSubmit = async (values) => {
    if (!values.items || values.items.length === 0) {
      message.warning('请至少添加一个盘点项')
      return
    }

    setSubmitting(true)
    const result = await StockTakeService.createTask({
      title: values.title,
      warehouse_id: values.warehouse_id,
      type: values.type,
      remark: values.remark,
      items: values.items.map((item) => ({
        spare_part_id: item.spare_part_id,
        remark: item.remark,
      })),
    })

    if (result.success) {
      message.success('盘点任务创建成功')
      navigate('/stock-take')
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
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/stock-take')}>返回</Button>
            <span>新建盘点任务</span>
          </Space>
        }
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}
          initialValues={{ type: 'full', items: [{}] }}>
          <Divider orientation="left">基本信息</Divider>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item name="title" label="盘点标题"
                rules={[{ required: true, message: '请输入盘点标题' }]}>
                <Input placeholder="例如: 2026年5月仓库A月度盘点" maxLength={100} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="warehouse_id" label="盘点仓库"
                rules={[{ required: true, message: '请选择仓库' }]}>
                <Select placeholder="选择仓库" showSearch optionFilterProp="label">
                  {warehouses.map((w) => (
                    <Select.Option key={w.id} value={w.id} label={w.name}>{w.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="type" label="盘点类型"
                rules={[{ required: true, message: '请选择类型' }]}>
                <Select>
                  <Select.Option value="full">全面盘点</Select.Option>
                  <Select.Option value="partial">部分盘点</Select.Option>
                  <Select.Option value="random">抽盘</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="盘点说明/备注" maxLength={500} showCount />
          </Form.Item>

          <Divider orientation="left">盘点范围</Divider>
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={12} align="middle" style={{ marginBottom: 8 }}>
                    <Col span={14}>
                      <Form.Item {...restField} name={[name, 'spare_part_id']}
                        rules={[{ required: true, message: '请选择备件' }]} noStyle>
                        <Select placeholder="选择备件" showSearch
                          optionFilterProp="label"
                          filterOption={(input, option) =>
                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())}>
                          {spareParts.map((sp) => (
                            <Select.Option key={sp.id} value={sp.id} label={`${sp.name} (${sp.sku || sp.code || ''})`}>
                              {sp.name} {sp.sku ? `(${sp.sku})` : ''} - 库存: {sp.quantity || 0}
                            </Select.Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item {...restField} name={[name, 'remark']} noStyle>
                        <Input placeholder="备注" />
                      </Form.Item>
                    </Col>
                    <Col span={2}>
                      {fields.length > 1 && (
                        <Button danger size="small" onClick={() => remove(name)}>删除</Button>
                      )}
                    </Col>
                  </Row>
                ))}
                <Button type="dashed" onClick={() => add({ spare_part_id: undefined, remark: '' })} block icon={<PlusOutlined />}>
                  添加备件
                </Button>
              </>
            )}
          </Form.List>

          <Divider />
          <Space>
            <Button type="primary" htmlType="submit" loading={submitting}>创建盘点任务</Button>
            <Button onClick={() => navigate('/stock-take')}>取消</Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}
