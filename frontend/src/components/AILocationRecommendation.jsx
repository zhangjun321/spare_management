/**
 * AI 货位推荐组件
 * 集成百度千帆 AI，智能推荐最佳仓库和货位
 */

import React, { useState } from 'react';
import { Card, Button, Alert, Descriptions, Tag, Space, Spin, Divider } from 'antd';
import { ThunderboltOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import WarehouseService from '../../services/warehouse';

const AILocationRecommendation = ({ sparePartData, onConfirm, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [recommendation, setRecommendation] = useState(null);
  const [error, setError] = useState(null);

  // 获取 AI 推荐
  const fetchRecommendation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await WarehouseService.recommendLocation(sparePartData);
      if (response.success) {
        setRecommendation(response.data);
      } else {
        setError(response.error || 'AI 推荐失败');
      }
    } catch (error) {
      console.error('获取 AI 推荐失败:', error);
      setError(error.response?.data?.error || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理确认
  const handleConfirm = () => {
    if (recommendation) {
      onConfirm({
        warehouse_id: recommendation.recommended_warehouse_id,
        location_id: recommendation.recommended_location_id,
        recommendation: recommendation
      });
    }
  };

  // 获取置信度颜色
  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return '#52c41a';
    if (confidence >= 60) return '#1890ff';
    if (confidence >= 40) return '#faad14';
    return '#ff4d4f';
  };

  // 初始状态
  if (!recommendation && !loading && !error) {
    return (
      <Card
        title={
          <span>
            <ThunderboltOutlined style={{ color: '#1890ff', marginRight: 8 }} />
            AI 智能推荐
          </span>
        }
        bordered={true}
        style={{ marginBottom: 16 }}
      >
        <Alert
          message="AI 货位推荐"
          description="点击"获取 AI 推荐"按钮，AI 将根据备件特性（名称、规格、分类、尺寸、重量等）自动分析并推荐最佳存储位置"
          type="info"
          showIcon
          action={
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={fetchRecommendation}
              disabled={!sparePartData?.name}
            >
              获取 AI 推荐
            </Button>
          }
        />
      </Card>
    );
  }

  // 加载中状态
  if (loading) {
    return (
      <Card
        title={
          <span>
            <ThunderboltOutlined style={{ color: '#1890ff', marginRight: 8 }} />
            AI 智能推荐
          </span>
        }
        bordered={true}
        style={{ marginBottom: 16 }}
      >
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <p style={{ marginTop: 16, fontSize: 14, color: '#666' }}>
            AI 正在分析备件特性并推荐最佳仓库和货位...
          </p>
          <p style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
            考虑因素：仓库类型、专长、货位承重、出入库频率、价值等级等
          </p>
        </div>
      </Card>
    );
  }

  // 错误状态
  if (error) {
    return (
      <Card
        title={
          <span>
            <ThunderboltOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
            AI 智能推荐
          </span>
        }
        bordered={true}
        style={{ marginBottom: 16 }}
      >
        <Alert
          message="AI 推荐失败"
          description={error}
          type="error"
          showIcon
          action={
            <Space>
              <Button size="small" onClick={fetchRecommendation}>
                重试
              </Button>
              <Button size="small" onClick={onCancel}>
                手动选择
              </Button>
            </Space>
          }
        />
      </Card>
    );
  }

  // 推荐结果展示
  return (
    <Card
      title={
        <span>
          <ThunderboltOutlined style={{ color: '#52c41a', marginRight: 8 }} />
          AI 推荐结果
        </span>
      }
      bordered={true}
      style={{ marginBottom: 16 }}
      extra={
        <Space>
          <Button icon={<CheckCircleOutlined />} type="primary" onClick={handleConfirm}>
            使用推荐
          </Button>
          <Button icon={<CloseCircleOutlined />} onClick={onCancel}>
            手动选择
          </Button>
        </Space>
      }
    >
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="推荐仓库" span={2}>
          <strong style={{ fontSize: 14 }}>{recommendation.recommended_warehouse_name}</strong>
        </Descriptions.Item>
        <Descriptions.Item label="仓库 ID">
          {recommendation.recommended_warehouse_id}
        </Descriptions.Item>
        <Descriptions.Item label="推荐货位" span={2}>
          <Tag color="blue" style={{ fontSize: 12 }}>
            {recommendation.recommended_location_code}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="货位 ID">
          {recommendation.recommended_location_id}
        </Descriptions.Item>
        <Descriptions.Item label="置信度">
          <Tag
            color={getConfidenceColor(recommendation.confidence)}
            style={{ minWidth: 60, textAlign: 'center' }}
          >
            {recommendation.confidence}%
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="推荐理由" span={2}>
          <div style={{ fontSize: 13, lineHeight: 1.6 }}>
            {recommendation.reason}
          </div>
        </Descriptions.Item>
      </Descriptions>

      {recommendation.notes && (
        <>
          <Divider style={{ margin: '16px 0' }} />
          <Alert
            message="注意事项"
            description={recommendation.notes}
            type="info"
            showIcon
            icon={<ThunderboltOutlined />}
          />
        </>
      )}

      {recommendation.alternative_warehouses && recommendation.alternative_warehouses.length > 0 && (
        <>
          <Divider style={{ margin: '16px 0' }} />
          <div>
            <strong>备选仓库：</strong>
            <Space style={{ marginLeft: 8 }}>
              {recommendation.alternative_warehouses.map((whId, index) => (
                <Tag key={index} color="default">
                  仓库 ID: {whId}
                </Tag>
              ))}
            </Space>
          </div>
        </>
      )}
    </Card>
  );
};

export default AILocationRecommendation;
