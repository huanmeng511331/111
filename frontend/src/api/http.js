import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

function extractMessage(error) {
  const response = error.response
  if (!response) {
    return error.message?.includes('timeout')
      ? '请求超时，请确认后端服务已启动'
      : '无法连接后端服务，请检查是否已启动 http://localhost:8000'
  }
  const detail = response.data?.detail
  if (typeof detail === 'string' && detail) {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join('；')
  }
  if (response.status === 404) {
    return '请求的资源不存在'
  }
  return `请求失败（HTTP ${response.status}）`
}

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = extractMessage(error)
    const normalized = new Error(message)
    normalized.status = error.response?.status
    normalized.code = error.response?.data?.code
    return Promise.reject(normalized)
  },
)

export default http
