/**
 * 仓库详情页面组件
 * 展示仓库基本信息、统计图表、AI 健康分析
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Descriptions,
  Statistic,
  Progress,
  Tag,
  Button,
  Space,
  Table,
  Alert,
  Spin,
  Tabs,
  Badge,
  Divider
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DashboardOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  HomeOutlined
} from '@ant-design/icons';
import WarehouseService from '../services/warehouse';

const { TabPane } = Tabs;

// 仓库类型映射
const WAREHOUSE_TYPES = {
  general: '普通仓库',
  cold: '冷库',
  hazardous: '危险品仓库',
  bonded: '保税仓库',
  automated: '自动化仓库'
};

const WarehouseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [warehouse, setWarehouse] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [healthReport, setHealthReport] = useState(null);
  const [inventoryRecords, setInventoryRecords] = useState([]);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [inventoryPagination, setInventoryPagination] = useState({ page: 1, per_page: 20, total: 0 });
  const [healthLoading, setHealthLoading] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadWarehouseDetail();
    loadStatistics();
    loadInventoryRecords();
  }, [id]);

  // 加载仓库详情
  const loadWarehouseDetail = async () => {
    setLoading(true);
    try {
      const response = await WarehouseService.getWarehouse(id);
      if (response.success) {
        setWarehouse(response.data);
      }
    } catch (error) {
      console.error('加载仓库详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 加载统计数据
  const loadStatistics = async () => {
    try {
      const response = await WarehouseService.getWarehouseStatistics(id);
      if (response.success) {
        setStatistics(response.data);
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  };

  // 加载库存记录（后端分页）
  const loadInventoryRecords = async (page = 1, per_page = 20) => {
    setInventoryLoading(true);
    try {
      const response = await WarehouseService.getWarehouseInventory(id, { page, per_page });
      if (response.success) {
        setInventoryRecords(response.data || []);
        const pg = response.pagination || {};
        setInventoryPagination({ page: pg.page || page, per_page: pg.per_page || per_page, total: pg.total || 0 });
      }
    } catch (error) {
      console.error('加载库存记录失败:', error);
    } finally {
      setInventoryLoading(false);
    }
  };

  // 加载 AI 健康分析
  const loadHealthAnalysis = async () => {
    setHealthLoading(true);
    try {
      const response = await WarehouseService.getWarehouseHealth(id);
      if (response.success) {
        setHealthReport(response.data);
      }
    } catch (error) {
      console.error('加载健康分析失败:', error);
    } finally {
      setHealthLoading(false);
    }
  };

  // 获取健康度颜色
  const getHealthColor = (score) => {
    if (score >= 90) return '#52c41a';
    if (score >= 75) return '#1890ff';
    if (score >= 60) return '#faad14';
    return '#ff4d4f';
  };

  // 获取利用率颜色
  const getUtilizationColor = (rate) => {
    if (rate >= 90) return '#ff4d4f';
    if (rate >= 75) return '#faad14';
    if (rate >= 50) return '#52c41a';
    return '#1890ff';
  };

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (!warehouse) {
    return (
      <Alert
        message="仓库不存在"
        description="该仓库不存在或已被删除"
        type="error"
        showIcon
        action={
          <Button type="primary" onClick={() => navigate('/warehouse/warehouses')}>
            返回列表
          </Button>
        }
      />
    );
  }

  return (
    <div className="warehouse-detail" style={{ padding: 24 }}>
      {/* 返回按钮和标题 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/warehouse/warehouses')}>
              返回
            </Button>
          </Col>
          <Col flex="auto">
            <h2 style={{ margin: 0, display: 'inline-block', marginLeft: 16 }}>
              <WarehouseOutlined style={{ marginRight: 8 }} />
              {warehouse.name}
              {warehouse.utilization_rate > warehouse.utilization_warning_threshold && (
                <WarningOutlined
                  style={{ color: '#ff4d4f', marginLeft: 8 }}
                />
              )}
            </h2>
          </Col>
          <Col>
            <Space>
              <Button icon={<EditOutlined />} onClick={() => navigate(`/warehouse/warehouses/${id}/edit`)}>
                编辑
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Tabs defaultActiveKey="basic">
        {/* 基本信息标签页 */}
        <TabPane
          tab={
            <span>
              <DashboardOutlined />
              基本信息
            </span>
          }
          key="basic"
        >
          <Card style={{ marginBottom: 24 }}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="仓库编码" span={1}>
                {warehouse.code}
              </Descriptions.Item>
              <Descriptions.Item label="仓库名称" span={1}>
                {warehouse.name}
              </Descriptions.Item>
              <Descriptions.Item label="仓库类型" span={1}>
                <Tag color="blue">{WAREHOUSE_TYPES[warehouse.type] || warehouse.type}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态" span={1}>
                <Tag color={warehouse.is_active ? 'green' : 'red'}>
                  {warehouse.is_active ? '启用' : '停用'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="仓库面积" span={1}>
                {warehouse.area ? `${warehouse.area} ㎡` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="仓库容量" span={1}>
                {warehouse.capacity ? `${warehouse.capacity} 件` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="仓库地址" span={2}>
                {warehouse.address || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="联系电话" span={1}>
                {warehouse.phone || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="仓库管理员" span={1}>
                {warehouse.manager ? warehouse.manager.username : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="仓库描述" span={2}>
                {warehouse.description || '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* 统计卡片 */}
          <Row gutter={[24, 24]}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="总库存"
                  value={warehouse.total_inventory || 0}
                  suffix="件"
                  prefix={<DashboardOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="备件种类"
                  value={warehouse.total_spare_parts || 0}
                  suffix="种"
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="利用率"
                  value={warehouse.utilization_rate || 0}
                  precision={2}
                  suffix="%"
                  prefix={<TrendingUpOutlined />}
                  valueStyle={{ color: getUtilizationColor(warehouse.utilization_rate) }}
                />
                <Progress
                  percent={warehouse.utilization_rate || 0}
                  strokeColor={getUtilizationColor(warehouse.utilization_rate)}
                  size="small"
                  style={{ marginTop: 8 }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="库区数量"
                  value={warehouse.zones_count || 0}
                  suffix="个"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* 图片展示标签页 */}
        <TabPane
          tab={
            <span>
              <DashboardOutlined />
              图片展示
            </span>
          }
          key="images"
        >
          <Row gutter={[16, 16]}>
            {warehouse.image_url && (
              <Col span={24}>
                <Card title="仓库主图">
                  <img
                    src={warehouse.image_url}
                    alt="仓库主图"
                    style={{ width: '100%', maxHeight: 400, objectFit: 'cover' }}
                    onError={(e) => {
                      e.target.src = '/static/images/default-warehouse.png';
                    }}
                  />
                </Card>
              </Col>
            )}
            {warehouse.interior_image_url && (
              <Col span={12}>
                <Card title="内部图">
                  <img
                    src={warehouse.interior_image_url}
                    alt="仓库内部"
                    style={{ width: '100%', maxHeight: 300, objectFit: 'cover' }}
                  />
                </Card>
              </Col>
            )}
            {warehouse.exterior_image_url && (
              <Col span={12}>
                <Card title="外观图">
                  <img
                    src={warehouse.exterior_image_url}
                    alt="仓库外观"
                    style={{ width: '100%', maxHeight: 300, objectFit: 'cover' }}
                  />
                </Card>
              </Col>
            )}
            {warehouse.layout_image_url && (
              <Col span={12}>
                <Card title="布局图">
                  <img
                    src={warehouse.layout_image_url}
                    alt="仓库布局"
                    style={{ width: '100%', maxHeight: 300, objectFit: 'cover' }}
                  />
                </Card>
              </Col>
            )}
            {warehouse.location_map_url && (
              <Col span={12}>
                <Card title="位置地图">
                  <img
                    src={warehouse.location_map_url}
                    alt="位置地图"
                    style={{ width: '100%', maxHeight: 300, objectFit: 'cover' }}
                  />
                </Card>
              </Col>
            )}
          </Row>
        </TabPane>

        {/* 库存列表标签页 */}
        <TabPane
          tab={
            <span>
              <DashboardOutlined />
              库存列表
            </span>
          }
          key="inventory"
        >
          <Card title={`库存记录（共 ${inventoryPagination.total} 条）`} bordered={false}>
            {inventoryLoading ? (
              <div style={{ padding: 40, textAlign: 'center' }}>
                <Spin size="large" tip="加载库存数据..." />
              </div>
            ) : inventoryRecords.length === 0 ? (
              <Alert
                message="暂无库存"
                description="该仓库还没有任何库存记录"
                type="info"
                showIcon
              />
            ) : (
              <Table
                rowKey="id"
                dataSource={inventoryRecords}
                loading={inventoryLoading}
                pagination={{
                  current: inventoryPagination.page,
                  pageSize: inventoryPagination.per_page,
                  total: inventoryPagination.total,
                  showSizeChanger: true,
                  showTotal: (total) => `共 ${total} 条`,
                  onChange: (page, pageSize) => loadInventoryRecords(page, pageSize)
                }}
                scroll={{ x: 1200 }}
              >
                <Table.Column 
                  title="备件编码" 
                  dataIndex={['spare_part', 'part_code']} 
                  key="part_code"
                  fixed="left"
                  width={120}
                />
                <Table.Column 
                  title="备件名称" 
                  dataIndex={['spare_part', 'name']} 
                  key="name"
                  fixed="left"
                  width={150}
                />
                <Table.Column 
                  title="规格型号" 
                  dataIndex={['spare_part', 'specification']} 
                  key="specification"
                  ellipsis
                  width={150}
                />
                <Table.Column 
                  title="分类" 
                  dataIndex={['spare_part', 'category']} 
                  key="category"
                  width={100}
                />
                <Table.Column 
                  title="库位编码" 
                  dataIndex={['location', 'location_code']} 
                  key="location_code"
                  width={100}
                />
                <Table.Column 
                  title="区域" 
                  dataIndex={['location', 'zone_name']} 
                  key="zone_name"
                  width={80}
                />
                <Table.Column 
                  title="库存数量" 
                  dataIndex="quantity" 
                  key="quantity"
                  align="right"
                  width={100}
                  sorter={(a, b) => a.quantity - b.quantity}
                />
                <Table.Column 
                  title="可用数量" 
                  dataIndex="available_quantity" 
                  key="available_quantity"
                  align="right"
                  width={100}
                  sorter={(a, b) => a.available_quantity - b.available_quantity}
                  render={(value, record) => {
                    const available = record.available_quantity || value || 0;
                    return (
                      <span style={{ color: available < 10 ? '#ff4d4f' : '#52c41a' }}>
                        {available}
                      </span>
                    );
                  }}
                />
                <Table.Column 
                  title="锁定数量" 
                  dataIndex="locked_quantity" 
                  key="locked_quantity"
                  align="right"
                  width={100}
                />
                <Table.Column 
                  title="库存状态" 
                  dataIndex="stock_status" 
                  key="stock_status"
                  width={100}
                  render={(status) => {
                    const statusMap = {
                      normal: { color: 'green', text: '正常' },
                      low: { color: 'orange', text: '低库存' },
                      out: { color: 'red', text: '缺货' },
                      overstock: { color: 'blue', text: '超储' }
                    };
                    const { color, text } = statusMap[status] || { color: 'default', text: status };
                    return <Tag color={color}>{text}</Tag>;
                  }}
                />
                <Table.Column 
                  title="批次号" 
                  dataIndex="batch_number" 
                  key="batch_number"
                  ellipsis
                  width={120}
                />
                <Table.Column 
                  title="入库日期" 
                  dataIndex="entry_date" 
                  key="entry_date"
                  width={120}
                />
                <Table.Column 
                  title="库龄 (天)" 
                  dataIndex="stock_age_days" 
                  key="stock_age_days"
                  align="right"
                  width={80}
                  sorter={(a, b) => a.stock_age_days - b.stock_age_days}
                />
              </Table>
            )}
          </Card>
        </TabPane>

        {/* AI 健康分析标签页 */}
        <TabPane
          tab={
            <span>
              <WarningOutlined />
              AI 健康分析
            </span>
          }
          key="health"
        >
          <Button
            type="primary"
            icon={<WarningOutlined />}
            onClick={loadHealthAnalysis}
            loading={healthLoading}
            style={{ marginBottom: 16 }}
          >
            运行 AI 健康分析
          </Button>

          {healthLoading && (
            <div style={{ padding: 40, textAlign: 'center' }}>
              <Spin size="large" tip="AI 正在分析库存健康状况..." />
            </div>
          )}

          {healthReport && !healthLoading && (
            <Row gutter={[24, 24]}>
              <Col span={8}>
                <Card title="健康度评分" bordered={false}>
                  <div style={{ textAlign: 'center' }}>
                    <div
                      style={{
                        fontSize: 48,
                        color: getHealthColor(healthReport.health_score),
                        fontWeight: 'bold'
                      }}
                    >
                      {healthReport.health_score}分
                    </div>
                    <div style={{ fontSize: 20, color: '#666', marginTop: 8 }}>
                      {healthReport.health_level}
                    </div>
                    <div style={{ marginTop: 16 }}>
                      <Tag color={getHealthColor(healthReport.health_score)}>
                        {healthReport.health_level}
                      </Tag>
                    </div>
                  </div>
                </Card>
              </Col>

              <Col span={16}>
                <Card title="库存结构分析" bordered={false}>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Statistic
                        title="正常库存"
                        value={healthReport.metrics?.normal_count || 0}
                        suffix="种"
                        valueStyle={{ color: '#52c41a' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="低库存"
                        value={healthReport.metrics?.low_stock_count || 0}
                        suffix="种"
                        valueStyle={{ color: '#faad14' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="缺货"
                        value={healthReport.metrics?.out_of_stock_count || 0}
                        suffix="种"
                        valueStyle={{ color: '#ff4d4f' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="超储"
                        value={healthReport.metrics?.overstock_count || 0}
                        suffix="种"
                        valueStyle={{ color: '#1890ff' }}
                      />
                    </Col>
                  </Row>

                  <Divider />

                  {healthReport.risks && healthReport.risks.length > 0 && (
                    <Alert
                      message="风险预警"
                      description={
                        <ul>
                          {healthReport.risks.map((risk, index) => (
                            <li key={index}>{risk}</li>
                          ))}
                        </ul>
                      }
                      type="warning"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />
                  )}

                  {healthReport.suggestions && healthReport.suggestions.length > 0 && (
                    <Alert
                      message="优化建议"
                      description={
                        <ul>
                          {healthReport.suggestions.map((suggestion, index) => (
                            <li key={index}>{suggestion}</li>
                          ))}
                        </ul>
                      }
                      type="success"
                      showIcon
                    />
                  )}
                </Card>
              </Col>
            </Row>
          )}

          {!healthReport && !healthLoading && (
            <Alert
              message="AI 健康分析"
              description="点击'运行 AI 健康分析'按钮，AI 将全面分析库存健康状况并提供优化建议"
              type="info"
              showIcon
            />
          )}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default WarehouseDetail;
