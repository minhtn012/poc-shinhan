import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail ?? error.message ?? 'Unknown error'
    return Promise.reject(new Error(detail))
  },
)

export default apiClient
