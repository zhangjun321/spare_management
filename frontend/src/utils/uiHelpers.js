/**
 * 用户体验优化工具
 * 提供统一的 UI 交互组件和工具函数
 */

import { message, notification, Spin, Empty, Alert } from 'antd';

/**
 * Toast 消息工具
 * 统一的提示消息管理
 */
export const toast = {
  /**
   * 成功提示
   */
  success: (content, duration = 3) => {
    message.success(content, duration);
  },

  /**
   * 错误提示
   */
  error: (content, duration = 5) => {
    message.error(content, duration);
  },

  /**
   * 警告提示
   */
  warning: (content, duration = 3) => {
    message.warning(content, duration);
  },

  /**
   * 信息提示
   */
  info: (content, duration = 3) => {
    message.info(content, duration);
  },

  /**
   * 加载中提示
   */
  loading: (content, duration = 0) => {
    return message.loading(content, duration);
  },

  /**
   * 销毁所有提示
   */
  destroy: () => {
    message.destroy();
  }
};

/**
 * 通知工具（用于重要通知）
 */
export const notify = {
  /**
   * 成功通知
   */
  success: (title, description) => {
    notification.success({
      message: title,
      description: description || '',
      duration: 4,
      placement: 'topRight'
    });
  },

  /**
   * 错误通知
   */
  error: (title, description) => {
    notification.error({
      message: title,
      description: description || '',
      duration: 6,
      placement: 'topRight'
    });
  },

  /**
   * 警告通知
   */
  warning: (title, description) => {
    notification.warning({
      message: title,
      description: description || '',
      duration: 5,
      placement: 'topRight'
    });
  },

  /**
   * 信息通知
   */
  info: (title, description) => {
    notification.info({
      message: title,
      description: description || '',
      duration: 4,
      placement: 'topRight'
    });
  },

  /**
   * 销毁所有通知
   */
  destroy: () => {
    notification.destroy();
  }
};

/**
 * 加载状态组件
 */
export const LoadingSpinner = ({
  tip = '加载中...',
  size = 'large',
  fullscreen = false
}) => {
  const spinner = (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: fullscreen ? '100vh' : '200px',
      flexDirection: 'column'
    }}>
      <Spin size={size} tip={tip} />
    </div>
  );

  return spinner;
};

/**
 * 空状态组件
 */
export const EmptyState = ({
  description = '暂无数据',
  image = Empty.PRESENTED_IMAGE_SIMPLE,
  action = null
}) => {
  return (
    <div style={{
      padding: '60px 20px',
      textAlign: 'center'
    }}>
      <Empty
        image={image}
        description={description}
      >
        {action && <div style={{ marginTop: 16 }}>{action}</div>}
      </Empty>
    </div>
  );
};

/**
 * 错误显示组件
 */
export const ErrorDisplay = ({
  message: errorMsg,
  description,
  type = 'error'
}) => {
  return (
    <Alert
      type={type}
      message={errorMsg}
      description={description}
      showIcon
      style={{ margin: '16px 0' }}
    />
  );
};

/**
 * API 错误处理
 * 统一处理 API 请求错误
 */
export const handleApiError = (error, defaultMessage = '操作失败') => {
  console.error('API Error:', error);

  // 网络错误
  if (!error.response) {
    toast.error('网络连接失败，请检查网络');
    return;
  }

  // 服务器错误
  if (error.response.status >= 500) {
    notify.error(
      '服务器错误',
      '服务器发生错误，请稍后重试'
    );
    return;
  }

  // 权限错误
  if (error.response.status === 401 || error.response.status === 403) {
    toast.error('权限不足或登录已过期');
    // 可以在这里添加跳转登录页的逻辑
    return;
  }

  // 业务错误
  const errorMessage = error.response?.data?.error || defaultMessage;
  toast.error(errorMessage);
};

/**
 * 确认对话框
 * 封装 antd 的 Modal.confirm
 */
export const confirm = async ({
  title,
  content,
  onOk,
  onCancel,
  okText = '确定',
  cancelText = '取消',
  okType = 'primary',
  okButtonProps = {},
  cancelButtonProps = {}
}) => {
  const { Modal } = await import('antd');

  return new Promise((resolve) => {
    Modal.confirm({
      title,
      content,
      okText,
      cancelText,
      okType,
      okButtonProps,
      cancelButtonProps,
      onOk: async () => {
        try {
          await onOk?.();
          resolve(true);
        } catch (error) {
          // 错误已在 onOk 中处理
          throw error;
        }
      },
      onCancel: () => {
        onCancel?.();
        resolve(false);
      }
    });
  });
};

/**
 * 批量操作结果处理
 */
export const handleBatchOperationResult = (result, operationName = '操作') => {
  const { success_count, failed_count, failed } = result;

  if (failed_count === 0) {
    toast.success(`${operationName}成功 ${success_count} 项`);
  } else if (success_count === 0) {
    toast.error(`${operationName}全部失败`);
  } else {
    toast.warning(
      `${operationName}完成：成功 ${success_count} 项，失败 ${failed_count} 项`
    );

    // 显示失败详情
    if (failed && failed.length > 0) {
      console.warn(`${operationName}失败详情:`, failed);
      notify.warning(
        `${operationName}部分失败`,
        `共有 ${failed_count} 项失败，详见控制台`
      );
    }
  }
};

/**
 * 表单验证错误处理
 */
export const handleFormValidationErrors = (errors, form) => {
  if (form && errors) {
    // 设置表单错误
    Object.keys(errors).forEach(field => {
      form.setFields([
        {
          name: field,
          errors: [errors[field]]
        }
      ]);
    });
  }
};

/**
 * 文件上传错误处理
 */
export const handleUploadError = (error, file) => {
  console.error('Upload Error:', error);
  toast.error(`文件 "${file.name}" 上传失败`);
};

/**
 * 文件上传成功处理
 */
export const handleUploadSuccess = (info, message = '上传成功') => {
  if (info.file.status === 'done') {
    toast.success(message);
    return info.file.response;
  }
  return null;
};

/**
 * 延迟函数
 */
export const delay = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * 防抖函数
 */
export const debounce = (func, wait = 300) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * 节流函数
 */
export const throttle = (func, limit = 300) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

export default {
  toast,
  notify,
  LoadingSpinner,
  EmptyState,
  ErrorDisplay,
  handleApiError,
  confirm,
  handleBatchOperationResult,
  handleFormValidationErrors,
  handleUploadError,
  handleUploadSuccess,
  delay,
  debounce,
  throttle
};
