/**
 * 仓库表单组件
 * 用于创建和编辑仓库
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Card,
  Row,
  Col,
  Upload,
  message,
  Space,
  Divider
} from 'antd';
import { ArrowLeftOutlined, UploadOutlined } from '@ant-design/icons';
import WarehouseService from '../services/warehouse';
import axios from 'axios';

const { TextArea } = Input;
const { Option } = Select;

// 仓库类型选项
const WAREHOUSE_TYPES = [
  { value: 'general', label: '普通仓库' },
  { value: 'cold', label: '冷库' },
  { value: 'hazardous', label: '危险品仓库' },
  { value: 'bonded', label: '保税仓库' },
  { value: 'automated', label: '自动化仓库' }
];

const WarehouseForm = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [warehouse, setWarehouse] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [userOptions, setUserOptions] = useState([]);

  const isEditMode = !!id;

  useEffect(() => {
    if (isEditMode) {
      loadWarehouse();
    }
    loadUsers();
  }, [id]);

  // 加载用户列表（供管理员选择）
  const loadUsers = async () => {
    try {
      const response = await axios.get('/api/users?per_page=200');
      const items = response.data?.data?.items || response.data?.items || [];
      setUserOptions(items.map(u => ({
        value: u.id,
        label: u.real_name ? `${u.real_name}（${u.username}）` : u.username
      })));
    } catch {
      // 获取用户列表失败时静默处理，不影响表单使用
    }
  };

  // 加载仓库数据（编辑模式）
  const loadWarehouse = async () => {
    setLoading(true);
    try {
      const response = await WarehouseService.getWarehouse(id);
      if (response.success) {
        setWarehouse(response.data);
        form.setFieldsValue(response.data);
      } else {
        message.error('加载仓库数据失败');
      }
    } catch (error) {
      console.error('加载仓库数据失败:', error);
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  // 提交表单
  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      let response;
      if (isEditMode) {
        response = await WarehouseService.updateWarehouse(id, values);
      } else {
        response = await WarehouseService.createWarehouse(values);
      }

      if (response.success) {
        message.success(isEditMode ? '更新成功' : '创建成功');
        navigate('/warehouse/warehouses');
      } else {
        message.error(response.error || '操作失败');
      }
    } catch (error) {
      console.error('提交表单失败:', error);
      message.error(error.response?.data?.error || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  // 图片上传
  const handleUpload = async (file, fieldName) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('field', fieldName);

    try {
      // TODO: 实现图片上传 API
      // const response = await uploadImage(formData);
      // if (response.success) {
      //   form.setFieldValue(fieldName, response.data.url);
      //   message.success('上传成功');
      // }
      message.info('图片上传功能待实现');
    } catch (error) {
      console.error('上传失败:', error);
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
  };

  // 上传组件配置
  const uploadProps = (fieldName) => ({
    name: 'file',
    action: '/api/upload', // TODO: 实现上传接口
    showUploadList: false,
    beforeUpload: (file) => handleUpload(file, fieldName),
    accept: 'image/*'
  });

  return (
    <div className="warehouse-form" style={{ padding: 24 }}>
      {/* 返回按钮和标题 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/warehouse/warehouses')}>
              返回
            </Button>
          </Col>
          <Col flex="auto">
            <h2 style={{ margin: 0 }}>
              {isEditMode ? '编辑仓库' : '新建仓库'}
            </h2>
          </Col>
        </Row>
      </Card>

      {/* 表单 */}
      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            type: 'general',
            is_active: true,
            capacity_warning_threshold: 90,
            utilization_warning_threshold: 85,
            enable_auto_alert: true
          }}
        >
          <Divider orientation="left">基本信息</Divider>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                label="仓库编码"
                name="code"
                rules={[
                  { required: true, message: '请输入仓库编码' },
                  { max: 50, message: '编码长度不能超过 50 个字符' }
                ]}
              >
                <Input placeholder="例如：BJ-WH-001" disabled={isEditMode} />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                label="仓库名称"
                name="name"
                rules={[
                  { required: true, message: '请输入仓库名称' },
                  { max: 100, message: '名称长度不能超过 100 个字符' }
                ]}
              >
                <Input placeholder="例如：北京一号仓库" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={8}>
              <Form.Item
                label="仓库类型"
                name="type"
                rules={[{ required: true, message: '请选择仓库类型' }]}
              >
                <Select placeholder="请选择">
                  {WAREHOUSE_TYPES.map(type => (
                    <Option key={type.value} value={type.value}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                label="仓库状态"
                name="is_active"
              >
                <Select>
                  <Option value={true}>启用</Option>
                  <Option value={false}>停用</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                label="仓库管理员"
                name="manager_id"
              >
                <Select
                  showSearch
                  allowClear
                  placeholder="请选择管理员"
                  optionFilterProp="label"
                  options={userOptions}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                label="仓库面积"
                name="area"
              >
                <InputNumber
                  placeholder="单位：平方米"
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  addonAfter="㎡"
                />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                label="仓库容量"
                name="capacity"
              >
                <InputNumber
                  placeholder="单位：件"
                  style={{ width: '100%' }}
                  min={0}
                  addonAfter="件"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                label="联系电话"
                name="phone"
                rules={[{ pattern: /^[\d-]+$/, message: '请输入正确的电话号码' }]}
              >
                <Input placeholder="例如：010-12345678" />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                label="仓库地址"
                name="address"
              >
                <Input placeholder="详细地址" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="仓库描述"
            name="description"
          >
            <TextArea
              rows={4}
              placeholder="请输入仓库描述"
              showCount
              maxLength={500}
            />
          </Form.Item>

          <Divider orientation="left">预警配置</Divider>

          <Row gutter={24}>
            <Col span={8}>
              <Form.Item
                label="容量预警阈值"
                name="capacity_warning_threshold"
                rules={[{ min: 0, max: 100 }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={100}
                  addonAfter="%"
                />
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                label="利用率预警阈值"
                name="utilization_warning_threshold"
                rules={[{ min: 0, max: 100 }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={100}
                  addonAfter="%"
                />
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                label="自动预警"
                name="enable_auto_alert"
              >
                <Select>
                  <Option value={true}>启用</Option>
                  <Option value={false}>禁用</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">图片管理（可选）</Divider>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item label="仓库主图">
                <Upload {...uploadProps('image_url')} disabled>
                  <Button icon={<UploadOutlined />} disabled>
                    上传图片（功能开发中）
                  </Button>
                </Upload>
                {warehouse?.image_url && (
                  <div style={{ marginTop: 8 }}>
                    <img
                      src={warehouse.image_url}
                      alt="仓库主图"
                      style={{ width: 200, height: 150, objectFit: 'cover' }}
                    />
                  </div>
                )}
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item label="仓库内部图">
                <Upload {...uploadProps('interior_image_url')} disabled>
                  <Button icon={<UploadOutlined />} disabled>
                    上传图片（功能开发中）
                  </Button>
                </Upload>
                {warehouse?.interior_image_url && (
                  <div style={{ marginTop: 8 }}>
                    <img
                      src={warehouse.interior_image_url}
                      alt="内部图"
                      style={{ width: 200, height: 150, objectFit: 'cover' }}
                    />
                  </div>
                )}
              </Form.Item>
            </Col>
          </Row>

          {/* 提交按钮 */}
          <Divider />

          <Form.Item>
            <Space size="large">
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                size="large"
              >
                {isEditMode ? '保存修改' : '创建仓库'}
              </Button>
              <Button
                onClick={() => navigate('/warehouse/warehouses')}
                size="large"
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default WarehouseForm;
