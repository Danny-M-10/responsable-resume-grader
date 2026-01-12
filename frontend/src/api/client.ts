import axios from 'axios'

// Use environment variable if set, otherwise use relative URL for same-origin (production) or localhost for dev
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? '' : 'http://localhost:8000')

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // Set timeout to 10 minutes (600000ms) for long-running operations like file uploads
  timeout: 600000, // 10 minutes
})

// Request interceptor to add auth token and set Content-Type appropriately
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Only set Content-Type for non-FormData requests
    // FormData requests should let axios set multipart/form-data with boundary automatically
    if (!(config.data instanceof FormData) && !config.headers['Content-Type']) {
      config.headers['Content-Type'] = 'application/json'
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

