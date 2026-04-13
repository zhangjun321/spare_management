/**
 * 权限验证工具
 * 提供前端权限控制功能
 */

// 权限缓存（避免重复计算）
let permissionsCache = null;
let permissionsCacheTime = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 分钟缓存

/**
 * 获取当前用户权限
 * 从 localStorage 或 API 获取权限数据
 */
export const getUserPermissions = async () => {
  // 检查缓存
  const now = Date.now();
  if (permissionsCache && permissionsCacheTime && (now - permissionsCacheTime) < CACHE_DURATION) {
    return permissionsCache;
  }

  try {
    // 从 localStorage 获取（登录时保存）
    const cached = localStorage.getItem('user_permissions');
    if (cached) {
      permissionsCache = JSON.parse(cached);
      permissionsCacheTime = now;
      return permissionsCache;
    }

    // 如果 localStorage 没有，从 API 获取
    const response = await fetch('/api/auth/permissions');
    if (response.ok) {
      const data = await response.json();
      permissionsCache = data.permissions || {};
      permissionsCacheTime = now;
      localStorage.setItem('user_permissions', JSON.stringify(permissionsCache));
      return permissionsCache;
    }

    return {};
  } catch (error) {
    console.error('获取用户权限失败:', error);
    return {};
  }
};

/**
 * 清除权限缓存
 * 登出或权限变更时调用
 */
export const clearPermissionsCache = () => {
  permissionsCache = null;
  permissionsCacheTime = null;
  localStorage.removeItem('user_permissions');
};

/**
 * 检查用户是否有指定权限
 * @param {string} resource - 资源类型 (如 'warehouse', 'spare_part')
 * @param {string} action - 操作类型 (如 'read', 'create', 'update', 'delete')
 * @returns {Promise<boolean>} 是否有权限
 */
export const hasPermission = async (resource, action) => {
  const permissions = await getUserPermissions();
  
  // 检查是否有超级管理员权限
  if (permissions.is_admin || permissions.is_superuser) {
    return true;
  }

  // 检查具体权限
  const resourcePermissions = permissions[resource];
  if (!resourcePermissions) {
    return false;
  }

  return resourcePermissions[action] === true;
};

/**
 * 检查用户是否有任一权限
 * @param {Array<Array<string>>} permissionPairs - 权限对数组 [['warehouse', 'read'], ['warehouse', 'create']]
 * @returns {Promise<boolean>} 是否有任一权限
 */
export const hasAnyPermission = async (permissionPairs) => {
  for (const [resource, action] of permissionPairs) {
    if (await hasPermission(resource, action)) {
      return true;
    }
  }
  return false;
};

/**
 * 检查用户是否有所有权限
 * @param {Array<Array<string>>} permissionPairs - 权限对数组
 * @returns {Promise<boolean>} 是否有所有权限
 */
export const hasAllPermissions = async (permissionPairs) => {
  for (const [resource, action] of permissionPairs) {
    if (!(await hasPermission(resource, action))) {
      return false;
    }
  }
  return true;
};

/**
 * 权限检查 HOC（高阶组件）
 * @param {string} resource - 资源类型
 * @param {string} action - 操作类型
 * @param {React.Component} Component - 要包装的组件
 * @param {React.Component} FallbackComponent - 无权限时显示的组件
 */
export const withPermission = (resource, action, Component, FallbackComponent = null) => {
  return class extends React.Component {
    state = { hasPermission: false, loading: true };

    async componentDidMount() {
      const permitted = await hasPermission(resource, action);
      this.setState({ hasPermission: permitted, loading: false });
    }

    render() {
      const { hasPermission, loading } = this.state;

      if (loading) {
        return <div>Loading...</div>;
      }

      if (hasPermission) {
        return <Component {...this.props} />;
      }

      if (FallbackComponent) {
        return <FallbackComponent {...this.props} />;
      }

      return null;
    }
  };
};

/**
 * 权限检查 Hook（用于函数组件）
 * @param {string} resource - 资源类型
 * @param {string} action - 操作类型
 * @returns {Object} { hasPermission, loading, checkPermission }
 */
export const usePermission = (resource, action) => {
  const [hasPermission, setHasPermission] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  const checkPermission = React.useCallback(async () => {
    setLoading(true);
    const permitted = await hasPermission(resource, action);
    setHasPermission(permitted);
    setLoading(false);
  }, [resource, action]);

  React.useEffect(() => {
    checkPermission();
  }, [resource, action, checkPermission]);

  return { hasPermission, loading, checkPermission };
};

/**
 * 权限指令（用于模板中）
 * 使用示例：<button v-permission="['warehouse', 'create']">创建仓库</button>
 */
export const permissionDirective = {
  mounted(el, binding) {
    const [resource, action] = binding.value;
    
    hasPermission(resource, action).then(permitted => {
      if (!permitted) {
        // 无权限时移除元素或禁用
        if (binding.arg === 'disabled') {
          el.disabled = true;
          el.style.opacity = '0.5';
          el.style.cursor = 'not-allowed';
        } else {
          el.parentNode?.removeChild(el);
        }
      }
    });
  }
};

/**
 * 获取用户角色
 */
export const getUserRole = async () => {
  const permissions = await getUserPermissions();
  return permissions.role || permissions.roles?.[0] || null;
};

/**
 * 检查用户是否有指定角色
 * @param {string|string[]} roles - 角色名称或角色名称数组
 * @returns {Promise<boolean>} 是否有指定角色
 */
export const hasRole = async (roles) => {
  const userRole = await getUserRole();
  
  if (!userRole) {
    return false;
  }

  if (typeof roles === 'string') {
    return userRole === roles;
  }

  return roles.includes(userRole);
};

// 导出 React 组件（用于条件渲染）
export const PermissionGuard = ({ resource, action, children, fallback = null }) => {
  const [hasPermission, setHasPermission] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    hasPermission(resource, action).then(permitted => {
      setHasPermission(permitted);
      setLoading(false);
    });
  }, [resource, action]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (hasPermission) {
    return children;
  }

  return fallback;
};

export default {
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  hasRole,
  getUserPermissions,
  getUserRole,
  clearPermissionsCache,
  withPermission,
  usePermission,
  PermissionGuard,
  permissionDirective
};
