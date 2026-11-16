import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail
    let message = '请求失败，请稍后重试'

    if (typeof detail === 'string') {
      message = detail
    } else if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      const field = Array.isArray(first.loc) ? first.loc.slice(1).join('.') : ''
      const reason = first.msg?.replace(/^Value error, /, '') || '参数校验失败'
      message = field ? `${field}：${reason}` : reason
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时，请确认后端服务已启动'
    } else if (!error.response) {
      message = '无法连接后端服务，请确认 http://localhost:8000 已启动'
    }

    return Promise.reject(new Error(message))
  }
)

export default http
