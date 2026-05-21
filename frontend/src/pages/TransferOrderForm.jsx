import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Form, Input, Select, Button, InputNumber, Space, message, Divider, Row, Col, Popconfirm } from 'antd'
import { ArrowLeftOutlined, PlusOutlined, DeleteOutlined, SaveOutlined, SendOutlined } from '@ant-design/icons'
import { TransferOrderService } from '../services/transferOrder'
import axios from 'axios'

const { TextArea } = Input
const { Option } = Select

export default function TransferOrderForm() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [form] = Form.useForm()
  const isEditMode = !!id
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [warehouses, setWarehouses] = useState([])
  const [spareParts, setSpareParts] = useState([])

  useEffect(() => {
    loadWarehouses()
    loadSpareParts()
    if (isEditMode) loadOrder()
  }, [id])

  const loadWarehouses = async () => {
    try {
      const resp = await axios.get('/api/warehouses')
      if (resp.data?.success) setWarehouses(resp.data.data || [])
    } catch { /* ignore */ }
  }

  const loadSpareParts = async () => {
    try {
      const resp = await axios.get('/api/spare-parts', { params: { per_page: 500 } })
      if (resp.data?.success) setSpareParts(resp.data.data || [])
    } catch { /* ignore */ }
  }

  const loadOrder = async () => {
    setLoading(true)
    const result = await TransferOrderService.get(id)
    if (result.success && result.data) {
      const d = result.data
      form.setFieldsValue({
        from_warehouse_id: d.from_warehouse_id,
        to_warehouse_id: d.to_warehouse_id,
        remark: d.remark,
        items: (d.items || []).map((item) => ({
          spare_part_id: item.spare_part_id,
          quantity: item.quantity,
          key: item.id || Date.now() + Math.random(),
        })),
      })
    } else {
      message.error(result.error || '加载调拨单失败')
    }
    setLoading(false)
  }

  const handleSubmit = async (values) => {
    if (!values.items || values.items.length === 0) {
      message.warning('请至少添加一个调拨明细')
      return
    }

    setSubmitting(true)
    const payload = {
      from_warehouse_id: values.from_warehouse_id,
      to_warehouse_id: values.to_warehouse_id,
      remark: values.remark,
      items: values.items.map((item) => ({
        spare_part_id: item.spare_part_id,
        quantity: item.quantity,
      })),
    }

    let result
    if (isEditMode) {
      result = await TransferOrderService.update(id, payload)
    } else {
      result = await TransferOrderService.create(payload)
    }

    if (result.success) {
      message.success(isEditMode ? '更新成功' : '创建成功')
      navigate('/transfer-orders')
    } else {
      message.error(result.error || '操作失败')
    }
    setSubmitting(false)
  }

  const handleSubmitAndSend = async () => {
    try {
      const values = await form.validateFields()
      await handleSubmit(values)
    } catch { /* validation error */ }
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/transfer-orders')}>返回</Button>
            <span>{isEditMode ? '编辑调拨单' : '新建调拨单'}</span>
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ items: [{}] }}
        >
          <Divider orientation="left">基本信息</Divider>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="from_warehouse_id"
                label="调出仓库"
                rules={[{ required: true, message: '请选择调出仓库' }]}
              >
                <Select placeholder="选择调出仓库" showSearch optionFilterProp="label">
                  {warehouses.map((w) => (
                    <Option key={w.id} value={w.id} label={w.name}>{w.name} ({w.code || ''})</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="to_warehouse_id"
                label="调入仓库"
                rules={[
                  { required: true, message: '请选择调入仓库' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (value && value === getFieldValue('from_warehouse_id')) {
                        return Promise.reject(new Error('调入仓库不能与调出仓库相同'))
                      }
                      return Promise.resolve()
                    },
                  }),
                ]}
              >
                <Select placeholder="选择调入仓库" showSearch optionFilterProp="label">
                  {warehouses.map((w) => (
                    <Option key={w.id} value={w.id} label={w.name}>{w.name} ({w.code || ''})</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="remark" label="备注">
            <TextArea rows={2} placeholder="调拨原因/备注" maxLength={500} showCount />
          </Form.Item>

          <Divider orientation="left">调拨明细</Divider>
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={12} align="middle" style={{ marginBottom: 8 }}>
                    <Col span={10}>
                      <Form.Item
                        {...restField}
                        name={[name, 'spare_part_id']}
                        rules={[{ required: true, message: '请选择备件' }]}
                        noStyle
                      >
                        <Select placeholder="选择备件" showSearch
                          optionFilterProp="label"
                          filterOption={(input, option) =>
                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                          }
                        >
                          {spareParts.map((sp) => (
                            <Option key={sp.id} value={sp.id} label={`${sp.name} (${sp.sku || sp.code || ''})`}>
                              {sp.name} {sp.sku ? `(${sp.sku})` : ''} - 库存: {sp.quantity || 0}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Form.Item
                        {...restField}
                        name={[name, 'quantity']}
                        rules={[{ required: true, message: '请输入数量' }]}
                        noStyle
                      >
                        <InputNumber placeholder="数量" min={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={2}>
                      {fields.length > 1 && (
                        <Button icon={<DeleteOutlined />} danger size="small" onClick={() => remove(name)} />
                      )}
                    </Col>
                  </Row>
                ))}
                <Button type="dashed" onClick={() => add({ spare_part_id: undefined, quantity: 1 })} block icon={<PlusOutlined />}>
                  添加备件
                </Button>
              </>
            )}
          </Form.List>

          <Divider />
          <Space>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={submitting}>
              {isEditMode ? '保存修改' : '保存草稿'}
            </Button>
            <Button icon={<SendOutlined />} onClick={handleSubmitAndSend} loading={submitting}>
              保存并提交审批
            </Button>
            <Button onClick={() => navigate('/transfer-orders')}>取消</Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}
