import React, { useEffect, useMemo, useState } from 'react'
import { Table, Tag, Space, Button, Form, Input, Select, DatePicker, message, Drawer, Descriptions, Card, Statistic, Row, Col, Empty, Dropdown, Menu } from 'antd'
import { PlusOutlined, ReloadOutlined, DownloadOutlined, SwapOutlined, ArrowUpOutlined, ArrowDownOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { fetchTransactions, fetchTransactionDetail, submitTransaction, approveTransaction, rejectTransaction, exportTransactions } from '../../services/transaction'
import { useNavigate } from 'react-router-dom'

const statusMeta = {


  draft: { color: 'default', text: '草稿' },
  submitted: { color: 'processing', text: '已提交' },
  approved: { color: 'success', text: '已审批' },
  rejected: { color: 'error', text: '已驳回' },
  closed: { color: 'default', text: '已关闭' },
}

const typeText = {
  inbound: '入库',
  outbound: '出库',
  transfer: '调拨',
  inventory_adjust: '盘点/差异',
}

const TransactionList = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [filters, setFilters] = useState({})
  const [detail, setDetail] = useState(null)
  const [detailVisible, setDetailVisible] = useState(false)



  const load = async (extra = {}) => {
    setLoading(true)
    try {
      const { data: res } = await fetchTransactions({ page, page_size: pageSize, ...filters, ...extra })
      setData(res.list || [])
      setTotal(res.total || 0)
    } catch (e) {
      message.error('加载交易列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize])

  const onSearch = (values) => {
    setFilters(values)
    setPage(1)
    load(values)
  }

  const openDetail = async (record) => {
    const { data: res } = await fetchTransactionDetail(record.id)
    setDetail(res)
    setDetailVisible(true)
  }

  const handleApprove = async (record) => {
    await approveTransaction(record.id)
    message.success('审批成功')
    load()
  }

  const handleSubmit = async (record) => {
    await submitTransaction(record.id)
    message.success('提交成功')
    load()
  }

  const handleReject = async (record) => {
    await rejectTransaction(record.id, '前端快速驳回')
    message.success('已驳回')
    load()
  }

  const handleExport = async () => {
    const { data: blob } = await exportTransactions(filters)
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'transactions.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  const stats = useMemo(() => {
    const result = { total: total || 0, draft: 0, submitted: 0, approved: 0 }
    data.forEach((t) => {
      result[t.status] = (result[t.status] || 0) + 1
    })
    return result
  }, [data, total])

  const columns = [
    { title: '单号', dataIndex: 'tx_code', render: (v) => v || '-', sorter: (a, b) => (a.tx_code || '').localeCompare(b.tx_code || '') },
    { title: '类型', dataIndex: 'tx_type', render: (v) => typeText[v] || v, sorter: (a, b) => (a.tx_type || '').localeCompare(b.tx_type || '') },
    { title: '来源仓', dataIndex: 'source_warehouse_id', render: (v) => v || '-', sorter: (a, b) => (a.source_warehouse_id || 0) - (b.source_warehouse_id || 0) },
    { title: '目标仓', dataIndex: 'target_warehouse_id', render: (v) => v || '-', sorter: (a, b) => (a.target_warehouse_id || 0) - (b.target_warehouse_id || 0) },
    { title: '数量', dataIndex: 'total_qty', sorter: (a, b) => (a.total_qty || 0) - (b.total_qty || 0) },
    { title: '状态', dataIndex: 'status', render: (s) => <Tag color={statusMeta[s]?.color || 'default'}>{statusMeta[s]?.text || s}</Tag>, sorter: (a, b) => (a.status || '').localeCompare(b.status || '') },
    { title: '创建时间', dataIndex: 'created_at', render: (t) => t ? t.replace('T', ' ').slice(0, 19) : '', sorter: (a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0) },
    {
      title: '操作',
      fixed: 'right',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button size="small" type="link" onClick={() => openDetail(record)}>查看</Button>
          {record.status === 'draft' && <Button size="small" type="link" onClick={() => handleSubmit(record)}>提交</Button>}
          {record.status === 'submitted' && <Button size="small" type="link" onClick={() => handleApprove(record)}>审批</Button>}
          {record.status === 'submitted' && <Button size="small" type="link" danger onClick={() => handleReject(record)}>驳回</Button>}
        </Space>
      )
    }
  ]

  const menu = (


    <Menu
      items={[
        { key: 'inbound', label: '新建入库单', icon: <ArrowDownOutlined />, onClick: () => navigate('/transactions/inbound') },
        { key: 'outbound', label: '新建出库单', icon: <ArrowUpOutlined />, onClick: () => navigate('/transactions/outbound') },
        { key: 'transfer', label: '新建调拨单', icon: <SwapOutlined />, onClick: () => navigate('/transactions/transfer') },
        { key: 'inventory', label: '盘点 / 差异调整', icon: <CheckCircleOutlined />, onClick: () => navigate('/transactions/inventory') },
      ]}
    />
  )

  return (
    <div className="warehouse-list" style={{ padding: 24 }}>
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space size="large">
              <h2 style={{ margin: 0 }}>交易管理</h2>
              <Space size="middle">
                <Statistic title="总单据" value={stats.total} valueStyle={{ fontSize: 20 }} />
                <Statistic title="草稿" value={stats.draft || 0} valueStyle={{ fontSize: 20 }} />
                <Statistic title="已提交" value={stats.submitted || 0} valueStyle={{ fontSize: 20 }} />
                <Statistic title="已审批" value={stats.approved || 0} valueStyle={{ fontSize: 20 }} />
              </Space>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => load()} loading={loading}>
                刷新
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleExport}>
                导出 CSV
              </Button>
              <Dropdown overlay={menu} placement="bottomRight">
                <Button type="primary" icon={<PlusOutlined />}>新建交易</Button>
              </Dropdown>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card style={{ marginBottom: 24 }}>
        <Form layout="inline" onFinish={onSearch} initialValues={filters}>
          <Form.Item name="keyword">
            <Input placeholder="关键字/单号" allowClear style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="tx_type">
            <Select placeholder="类型" allowClear style={{ width: 160 }}>
              <Select.Option value="inbound">入库</Select.Option>
              <Select.Option value="outbound">出库</Select.Option>
              <Select.Option value="transfer">调拨</Select.Option>
              <Select.Option value="inventory_adjust">盘点/差异</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="status">
            <Select placeholder="状态" allowClear style={{ width: 160 }}>
              <Select.Option value="draft">草稿</Select.Option>
              <Select.Option value="submitted">已提交</Select.Option>
              <Select.Option value="approved">已审批</Select.Option>
              <Select.Option value="rejected">已驳回</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <DatePicker.RangePicker />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">查询</Button>
              <Button onClick={() => { setFilters({}); setPage(1); load({}); }}>重置</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card>
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={data}
          bordered={false}
          size="middle"
          locale={{ emptyText: <Empty description="暂无交易记录，点击右上角“新建交易”创建入库/出库/调拨/盘点单" /> }}
          scroll={{ x: 900 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条记录`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) }
          }}
        />
      </Card>

      <Drawer
        title="交易详情"
        width={560}
        open={detailVisible}
        onClose={() => setDetailVisible(false)}
      >
        {detail && (
          <>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="单号">{detail.tx_code}</Descriptions.Item>
              <Descriptions.Item label="类型">{typeText[detail.tx_type] || detail.tx_type}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusMeta[detail.status]?.color}>{statusMeta[detail.status]?.text || detail.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="数量">{detail.total_qty}</Descriptions.Item>
              <Descriptions.Item label="备注">{detail.remark}</Descriptions.Item>
            </Descriptions>
            <h6 className="mt-3">明细</h6>
            <Table
              size="small"
              rowKey="id"
              pagination={false}
              columns={[
                { title: '备件', dataIndex: 'spare_part_id' },
                { title: '数量', dataIndex: 'quantity' },
                { title: '单价', dataIndex: 'unit_price' },
                { title: '金额', dataIndex: 'amount' },
              ]}
              dataSource={detail.details || []}
            />
            <h6 className="mt-3">库存流水</h6>
            <Table
              size="small"
              rowKey="id"
              pagination={false}
              columns={[
                { title: '仓库', dataIndex: 'warehouse_id' },
                { title: '库位', dataIndex: 'location_id' },
                { title: '变化', dataIndex: 'quantity_delta' },
                { title: '时间', dataIndex: 'created_at' },
              ]}
              dataSource={detail.ledgers || []}
            />
          </>
        )}
      </Drawer>
    </div>
  )
}


export default TransactionList

