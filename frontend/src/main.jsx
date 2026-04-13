import React from 'react'
import ReactDOM from 'react-dom/client'
import axios from 'axios'
import App from './App.jsx'
// bootstrap CSS 已通过 index.css 中 @import 或按需引入，此处仅保留全局样式
import './index.css'

// 全局 axios 响应拦截器：统一处理 401 未登录（JSON 格式）
// 覆盖所有直接使用 axios 的请求（warehouse.js 等）
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Flask 返回 JSON 401，跳转到登录页
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
