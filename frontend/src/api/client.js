import axios from 'axios'

// Создаем базовый экземпляр axios
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Добавляем интерцепторы
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Экспортируем методы API
export default {
  async getMessages() {
    return apiClient.get('/messages')
  },
  
  async uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // Добавляем другие методы по необходимости
  async getSomeData(params) {
    return apiClient.get('/data', { params })
  }
}