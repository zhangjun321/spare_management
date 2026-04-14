import React from 'react'
import { Form, Input, InputNumber, Button, Space, Card, message, Select } from 'antd'
import { createTransaction, validateTransaction } from '../../services/transaction'

const TransactionFormBase = ({ txType, title, requireSource = false, requireTarget = false }) => {
  const [form] = Form.useForm()

  const onFinish = async (values) => {
    const payload = {
      tx_type: txType,
      remark: values.remark,
      source_warehouse_id: values.source_warehouse_id,
      target_warehouse_id: values.target_warehouse_id,
      items: values.items,
    }
    await validateTransaction(payload)
    const { data } = await createTransaction(payload)
    message.success(`${title}已创建：${data.tx_code}`)
    form.resetFields()
  }

  return (
    <Card title={title} className="mt-3">
      <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ items: [{}] }}>
        {requireSource && (
          <Form.Item name="source_warehouse_id" label="来源仓库" rules={[{ required: true, message: '请选择来源仓库ID' }]}>
            <Input placeholder="仓库ID" />
          </Form.Item>
        )}
        {requireTarget && (
          <Form.Item name="target_warehouse_id" label="目标仓库" rules={[{ required: true, message: '请选择目标仓库ID' }]}>
            <Input placeholder="仓库ID" />
          </Form.Item>
        )}
        <Form.List name="items">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Card key={key} size="small" className="mb-2" title={`明细 ${name + 1}`} extra={<a onClick={() => remove(name)}>删除</a>}>
                  <Space align="baseline" wrap style={{ width: '100%' }}>
                    <Form.Item {...restField} name={[name, 'spare_part_id']} label="备件ID" rules={[{ required: true, message: '必填' }]}> <Input placeholder="spare_part_id" /> </Form.Item>
                    <Form.Item {...restField} name={[name, 'batch_id']} label="批次ID"> <Input placeholder="batch_id" /> </Form.Item>
                    {requireSource && (
                      <Form.Item {...restField} name={[name, 'source_location_id']} label="来源库位"> <Input placeholder="source location" /> </Form.Item>
                    )}
                    {requireTarget && (
                      <Form.Item {...restField} name={[name, 'target_location_id']} label="目标库位"> <Input placeholder="target location" /> </Form.Item>
                    )}
                    <Form.Item {...restField} name={[name, 'quantity']} label="数量" rules={[{ required: true, message: '必填' }]}> <InputNumber min={0} /> </Form.Item>
                    <Form.Item {...restField} name={[name, 'unit_price']} label="单价"> <InputNumber min={0} /> </Form.Item>
                  </Space>
                  <Form.Item {...restField} name={[name, 'remark']} label="备注"> <Input.TextArea rows={2} /> </Form.Item>
                </Card>
              ))}
              <Form.Item>
                <Button type="dashed" onClick={() => add()} block>新增明细</Button>
              </Form.Item>
            </>
          )}
        </Form.List>
        <Form.Item name="remark" label="整单备注">
          <Input.TextArea rows={2} />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">保存草稿</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default TransactionFormBase
