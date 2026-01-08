import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { apiClient } from '../api/client'

interface User {
  id: string
  email: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for stored token on mount
    const token = localStorage.getItem('auth_token')
    if (token) {
      // Verify token and get user info
      apiClient.get('/api/auth/me')
        .then((response) => {
          setUser({
            id: response.data.id,
            email: response.data.email,
          })
        })
        .catch(() => {
          // Token invalid, clear it
          localStorage.removeItem('auth_token')
        })
        .finally(() => {
          setLoading(false)
        })
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    const response = await apiClient.post('/api/auth/login', {
      email,
      password,
    })
    
    const { access_token } = response.data
    localStorage.setItem('auth_token', access_token)
    
    // Get user info
    const userResponse = await apiClient.get('/api/auth/me')
    setUser({
      id: userResponse.data.id,
      email: userResponse.data.email,
    })
  }

  const register = async (email: string, password: string) => {
    const response = await apiClient.post('/api/auth/register', {
      email,
      password,
    })
    
    const { access_token } = response.data
    localStorage.setItem('auth_token', access_token)
    
    // Get user info
    const userResponse = await apiClient.get('/api/auth/me')
    setUser({
      id: userResponse.data.id,
      email: userResponse.data.email,
    })
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setUser(null)
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

