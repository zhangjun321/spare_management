/**
 * 仓库列表页面组件
 * 支持列表视图和卡片视图切换
 * 集成 AI 货位推荐功能
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Button,
  Table,
  Tag,
  Progress,
  Input,
  Select,
  Space,
  Modal,
  message,
  Tooltip,
  Badge,
  Statistic
} from 'antd';
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  BarChartOutlined,
  PlusOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  SearchOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import WarehouseService from '../services/warehouse';

const { Search } = Input;
const { Option } = Select;

// 仓库类型映射
const WAREHOUSE_TYPES = {
  general: '普通仓库',
  cold: '冷库',
  hazardous: '危险品仓库',
  bonded: '保税仓库',
  automated: '自动化仓库'
};

// 仓库状态颜色
const getStatusColor = (utilization) => {
  if (utilization >= 90) return '#ff4d4f'; // 红色 - 超负荷
  if (utilization >= 75) return '#faad14'; // 橙色 - 高利用率
  if (utilization >= 50) return '#52c41a'; // 绿色 - 正常
  return '#1890ff'; // 蓝色 - 低利用率
};

const WarehouseList = () => {
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('card'); // 'card' | 'list'
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0
  });
  const [filters, setFilters] = useState({
    name: '',
    type: '',
    is_active: null
  });

  useEffect(() => {
    loadWarehouses();
  }, [pagination.page, filters]);

  // 加载仓库列表
  const loadWarehouses = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...filters
      };

      const response = await WarehouseService.getWarehouses(params);
      
      if (response.success) {
        setWarehouses(response.data.warehouses);
        setPagination(response.data.pagination);
      } else {
        message.error('加载仓库列表失败');
      }
    } catch (error) {
      console.error('加载仓库列表失败:', error);
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  // 搜索
  const handleSearch = (value) => {
    setFilters(prev => ({ ...prev, name: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  // 类型筛选
  const handleTypeChange = (value) => {
    setFilters(prev => ({ ...prev, type: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  // 查看仓库详情
  const viewDetail = (warehouseId) => {
    navigate(`/warehouse/warehouses/${warehouseId}`);
  };

  // 编辑仓库
  const editWarehouse = (warehouseId) => {
    navigate(`/warehouse/warehouses/${warehouseId}/edit`);
  };

  // 删除仓库
  const deleteWarehouse = async (warehouseId) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除该仓库吗？此操作不可恢复！',
      okText: '确认',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          const response = await WarehouseService.deleteWarehouse(warehouseId);
          if (response.success) {
            message.success('删除成功');
            loadWarehouses();
          } else {
            message.error(response.error || '删除失败');
          }
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 新建仓库
  const createWarehouse = () => {
    navigate('/warehouse/warehouses/new');
  };

  // 卡片视图渲染
  const renderCardView = () => (
    <Row gutter={[24, 24]}>
      {warehouses.map(warehouse => (
        <Col key={warehouse.id} xs={24} sm={12} lg={8} xl={6}>
          <Card
            hoverable
            cover={
              <img
                alt={warehouse.name}
                src={warehouse.image_url || '/static/images/default-warehouse.png'}
                style={{ height: 200, objectFit: 'cover' }}
                onError={(e) => {
                  e.target.src = '/static/images/default-warehouse.png';
                }}
              />
            }
            actions={[
              <EyeOutlined
                key="view"
                onClick={() => viewDetail(warehouse.id)}
                title="查看详情"
              />,
              <EditOutlined
                key="edit"
                onClick={() => editWarehouse(warehouse.id)}
                title="编辑"
              />,
              <DeleteOutlined
                key="delete"
                onClick={() => deleteWarehouse(warehouse.id)}
                title="删除"
              />,
              <BarChartOutlined
                key="stats"
                onClick={() => viewDetail(warehouse.id)}
                title="统计分析"
              />
            ]}
          >
            <Card.Meta
              title={
                <div>
                  <span>{warehouse.name}</span>
                  {warehouse.utilization_rate > warehouse.utilization_warning_threshold && (
                    <Tooltip title="利用率高，请注意">
                      <WarningOutlined
                        style={{ color: '#ff4d4f', marginLeft: 8 }}
                      />
                    </Tooltip>
                  )}
                </div>
              }
              description={
                <div>
                  <p style={{ color: '#666', marginBottom: 4 }}>
                    编码：{warehouse.code}
                  </p>
                  <p style={{ color: '#666', marginBottom: 4 }}>
                    类型：{WAREHOUSE_TYPES[warehouse.type] || warehouse.type}
                  </p>
                  <p style={{ color: '#666', marginBottom: 8 }}>
                    容量：{warehouse.capacity || 0} 件
                  </p>
                  <Progress
                    percent={warehouse.utilization_rate || 0}
                    strokeColor={getStatusColor(warehouse.utilization_rate)}
                    format={(percent) => `利用率 ${percent}%`}
                    size="small"
                  />
                  <div style={{ marginTop: 12 }}>
                    <Space size="small">
                      <Badge
                        count={warehouse.total_inventory || 0}
                        style={{ backgroundColor: '#1890ff' }}
                        title="总库存"
                      />
                      <span style={{ fontSize: 12, color: '#999' }}>
                        备件种类：{warehouse.total_spare_parts || 0}
                      </span>
                    </Space>
                  </div>
                </div>
              }
            />
          </Card>
        </Col>
      ))}
    </Row>
  );

  // 列表视图渲染
  const renderListView = () => {
    const columns = [
      {
        title: '仓库编码',
        dataIndex: 'code',
        key: 'code',
        width: 120,
        fixed: 'left'
      },
      {
        title: '仓库名称',
        dataIndex: 'name',
        key: 'name',
        width: 200,
        render: (text, record) => (
          <div>
            <span>{text}</span>
            {record.utilization_rate > record.utilization_warning_threshold && (
              <WarningOutlined
                style={{ color: '#ff4d4f', marginLeft: 8 }}
              />
            )}
          </div>
        )
      },
      {
        title: '仓库类型',
        dataIndex: 'type',
        key: 'type',
        width: 100,
        render: (type) => (
          <Tag color="blue">{WAREHOUSE_TYPES[type] || type}</Tag>
        )
      },
      {
        title: '容量',
        dataIndex: 'capacity',
        key: 'capacity',
        width: 100,
        render: (capacity) => `${capacity || 0} 件`
      },
      {
        title: '总库存',
        dataIndex: 'total_inventory',
        key: 'total_inventory',
        width: 100,
        render: (count) => (
          <span style={{ color: '#1890ff' }}>{count || 0} 件</span>
        )
      },
      {
        title: '备件种类',
        dataIndex: 'total_spare_parts',
        key: 'total_spare_parts',
        width: 100,
        render: (count) => `${count || 0} 种`
      },
      {
        title: '利用率',
        dataIndex: 'utilization_rate',
        key: 'utilization_rate',
        width: 150,
        render: (rate) => (
          <Progress
            percent={rate || 0}
            strokeColor={getStatusColor(rate)}
            size="small"
            format={(percent) => `${percent}%`}
          />
        )
      },
      {
        title: '状态',
        key: 'is_active',
        width: 80,
        render: (isActive) => (
          <Tag color={isActive ? 'green' : 'red'}>
            {isActive ? '启用' : '停用'}
          </Tag>
        )
      },
      {
        title: '操作',
        key: 'action',
        width: 200,
        fixed: 'right',
        render: (_, record) => (
          <Space size="small">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => viewDetail(record.id)}
            >
              详情
            </Button>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => editWarehouse(record.id)}
            >
              编辑
            </Button>
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => deleteWarehouse(record.id)}
            >
              删除
            </Button>
          </Space>
        )
      }
    ];

    return (
      <Table
        columns={columns}
        dataSource={warehouses}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagination.page,
          pageSize: pagination.per_page,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条记录`
        }}
        scroll={{ x: 1200 }}
      />
    );
  };

  return (
    <div className="warehouse-list" style={{ padding: 24 }}>
      {/* 顶部操作栏 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space size="large">
              <h2 style={{ margin: 0 }}>仓库管理</h2>
              <Space size="middle">
                <Statistic
                  title="总仓库数"
                  value={pagination.total}
                  valueStyle={{ fontSize: 20 }}
                />
                <Statistic
                  title="总库存"
                  value={warehouses.reduce(
                    (sum, wh) => sum + (wh.total_inventory || 0),
                    0
                  )}
                  suffix="件"
                  valueStyle={{ fontSize: 20 }}
                />
              </Space>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                type={viewMode === 'card' ? 'primary' : 'default'}
                icon={<AppstoreOutlined />}
                onClick={() => setViewMode('card')}
              >
                卡片视图
              </Button>
              <Button
                type={viewMode === 'list' ? 'primary' : 'default'}
                icon={<UnorderedListOutlined />}
                onClick={() => setViewMode('list')}
              >
                列表视图
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={createWarehouse}>
                新建仓库
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 筛选栏 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Search
              placeholder="搜索仓库名称"
              allowClear
              enterButton
              onSearch={handleSearch}
              defaultValue={filters.name}
            />
          </Col>
          <Col span={6}>
            <Select
              placeholder="仓库类型"
              style={{ width: '100%' }}
              allowClear
              onChange={handleTypeChange}
              defaultValue={filters.type || undefined}
            >
              <Option value="general">普通仓库</Option>
              <Option value="cold">冷库</Option>
              <Option value="hazardous">危险品仓库</Option>
              <Option value="bonded">保税仓库</Option>
              <Option value="automated">自动化仓库</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 仓库列表 */}
      {loading && viewMode === 'list' ? (
        <Card><div style={{ textAlign: 'center', padding: 40 }}>加载中...</div></Card>
      ) : (
        viewMode === 'card' ? renderCardView() : renderListView()
      )}
    </div>
  );
};

export default WarehouseList;
