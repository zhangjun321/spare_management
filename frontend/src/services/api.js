import axios from 'axios'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从 cookie 获取 CSRF token
    const csrfToken = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrf_token='))
      ?.split('=')[1]

    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API 请求错误:', error)
    
    if (error.response) {
      // 服务器返回错误响应
      const { status, data } = error.response
      
      if (status === 401) {
        // 未授权，跳转到登录页
        window.location.href = '/login'
      } else if (status === 403) {
        // 禁止访问
        console.error('没有权限访问')
      } else if (status === 404) {
        // 资源未找到
        console.error('请求的资源不存在')
      } else if (status >= 500) {
        // 服务器错误
        console.error('服务器错误:', data)
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('网络错误，请检查网络连接')
    } else {
      // 设置请求时发生错误
      console.error('请求配置错误:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
