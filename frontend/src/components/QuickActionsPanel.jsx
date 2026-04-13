/**
 * 快捷操作面板组件
 * 提供常用功能的快速访问入口
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Drawer, Card, Row, Col, Statistic, Progress, Tag, Button, Space, Divider } from 'antd';
import {
  PlusOutlined,
  ImportOutlined,
  ExportOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  ShoppingCartOutlined,
  WarehouseOutlined,
  FileTextOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';

const QuickActionsPanel = ({ visible, onClose }) => {
  const navigate = useNavigate();
  
  // 快捷操作列表
  const quickActions = [
    {
      title: '新建仓库',
      icon: <PlusOutlined />,
      color: '#1890ff',
      action: () => {
        navigate('/warehouse/warehouses/new');
        onClose();
      },
      description: '创建新的仓库'
    },
    {
      title: '入库操作',
      icon: <ImportOutlined />,
      color: '#52c41a',
      action: () => {
        navigate('/warehouse/inbound/new');
        onClose();
      },
      description: '备件入库登记'
    },
    {
      title: '出库操作',
      icon: <ExportOutlined />,
      color: '#faad14',
      action: () => {
        navigate('/warehouse/outbound/new');
        onClose();
      },
      description: '备件出库登记'
    },
    {
      title: '库存盘点',
      icon: <FileTextOutlined />,
      color: '#722ed1',
      action: () => {
        navigate('/warehouse/inventory');
        onClose();
      },
      description: '查看和盘点库存'
    },
    {
      title: '数据分析',
      icon: <BarChartOutlined />,
      color: '#13c2c2',
      action: () => {
        navigate('/warehouse/analysis');
        onClose();
      },
      description: '库存分析和预测'
    },
    {
      title: '补货建议',
      icon: <ShoppingCartOutlined />,
      color: '#eb2f96',
      action: () => {
        // TODO: 导航到补货建议页面
        onClose();
      },
      description: '查看智能补货建议'
    }
  ];
  
  // 常用功能
  const commonFeatures = [
    {
      title: '仓库列表',
      icon: <WarehouseOutlined />,
      path: '/warehouse/warehouses'
    },
    {
      title: '备件管理',
      icon: <ThunderboltOutlined />,
      path: '/spare-parts'
    },
    {
      title: '预警中心',
      icon: <AlertOutlined />,
      path: '/warehouse/alerts'
    },
    {
      title: '操作日志',
      icon: <ClockCircleOutlined />,
      path: '/warehouse/logs'
    }
  ];
  
  // 统计卡片
  const statistics = [
    {
      title: '总仓库数',
      value: 12,
      icon: <WarehouseOutlined />,
      color: '#1890ff',
      trend: '+2',
      trendType: 'up'
    },
    {
      title: '库存品种',
      value: 1268,
      icon: <FileTextOutlined />,
      color: '#52c41a',
      trend: '+15',
      trendType: 'up'
    },
    {
      title: '待处理入库',
      value: 8,
      icon: <ImportOutlined />,
      color: '#faad14',
      trend: '-3',
      trendType: 'down'
    },
    {
      title: '待处理出库',
      value: 15,
      icon: <ExportOutlined />,
      color: '#eb2f96',
      trend: '+5',
      trendType: 'up'
    }
  ];
  
  return (
    <Drawer
      title="快捷操作面板"
      placement="right"
      width={400}
      visible={visible}
      onClose={onClose}
      destroyOnClose
    >
      {/* 统计数据 */}
      <div style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {statistics.map((stat, index) => (
            <Col span={12} key={index}>
              <Card size="small" bordered={false} style={{ textAlign: 'center' }}>
                <Statistic
                  title={stat.title}
                  value={stat.value}
                  prefix={stat.icon}
                  valueStyle={{ color: stat.color, fontSize: 20 }}
                />
                {stat.trend && (
                  <div style={{ marginTop: 8, fontSize: 12 }}>
                    <Tag color={stat.trendType === 'up' ? 'red' : 'green'}>
                      {stat.trend}
                    </Tag>
                  </div>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      </div>
      
      <Divider>快捷操作</Divider>
      
      {/* 快捷操作 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {quickActions.map((action, index) => (
          <Col span={12} key={index}>
            <Card
              hoverable
              size="small"
              onClick={action.action}
              style={{
                textAlign: 'center',
                cursor: 'pointer',
                height: 120,
                borderLeft: `4px solid ${action.color}`
              }}
              bodyStyle={{ padding: 12 }}
            >
              <div style={{ color: action.color, fontSize: 24, marginBottom: 8 }}>
                {action.icon}
              </div>
              <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                {action.title}
              </div>
              <div style={{ fontSize: 12, color: '#999' }}>
                {action.description}
              </div>
            </Card>
          </Col>
        ))}
      </Row>
      
      <Divider>常用功能</Divider>
      
      {/* 常用功能 */}
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {commonFeatures.map((feature, index) => (
          <Card
            key={index}
            hoverable
            size="small"
            onClick={() => navigate(feature.path)}
            style={{ cursor: 'pointer' }}
            bodyStyle={{ padding: '12px 16px' }}
          >
            <Space>
              <div style={{ color: '#1890ff', fontSize: 18 }}>
                {feature.icon}
              </div>
              <div style={{ fontWeight: 500 }}>
                {feature.title}
              </div>
            </Space>
          </Card>
        ))}
      </Space>
      
      {/* 底部提示 */}
      <div style={{
        marginTop: 24,
        padding: 16,
        background: '#f5f5f5',
        borderRadius: 4,
        fontSize: 12,
        color: '#666'
      }}>
        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
        提示：使用快捷键 Ctrl+K 可快速打开此面板
      </div>
    </Drawer>
  );
};

export default QuickActionsPanel;
