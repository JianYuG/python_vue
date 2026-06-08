import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 —— 自动携带 Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求发送失败:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 —— 统一处理错误
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端 Result 约定：code=200 为成功
    if (res.code === 200) {
      return res
    }
    // 业务错误
    const message = res.message || '请求失败'
    ElMessage.error(message)

    // 401 未授权 —— 跳转登录页
    if (res.code === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      router.push('/login')
    }

    return Promise.reject(new Error(message))
  },
  (error) => {
    // HTTP 状态码层面的错误
    let message = '网络异常，请稍后重试'
    if (error.response) {
      const status = error.response.status
      switch (status) {
        case 400:
          message = '请求参数错误'
          break
        case 401:
          message = '未登录或Token已过期'
          localStorage.removeItem('token')
          localStorage.removeItem('userInfo')
          router.push('/login')
          break
        case 403:
          message = '无权限访问'
          break
        case 404:
          message = '请求资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = `请求失败(${status})`
      }
      // 尝试获取后端返回的错误信息
      if (error.response.data && error.response.data.message) {
        message = error.response.data.message
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时，请稍后重试'
    } else if (!navigator.onLine) {
      message = '网络已断开，请检查网络连接'
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
