'use client'

import { create } from 'zustand'
import type { AuthUser } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003/api/v1'

interface AuthState {
  user: AuthUser | null
  accessToken: string | null
  isLoading: boolean
  /** True once the initial auth check (refresh attempt) has completed */
  isInitialized: boolean
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  /** Register returns a message — user must verify email before logging in */
  register: (email: string, password: string) => Promise<string>
  logout: () => Promise<void>
  /** Try to restore session from refresh token cookie */
  initialize: () => Promise<void>
  /** Get a valid access token, refreshing if needed */
  getAccessToken: () => Promise<string | null>
  clearAuth: () => void
  verifyEmail: (token: string) => Promise<string>
  forgotPassword: (email: string) => Promise<string>
  resetPassword: (token: string, password: string) => Promise<string>
  resendVerification: (email: string) => Promise<string>
}

type AuthStore = AuthState & AuthActions

/** Call the auth API. Separate from fetchApi to avoid circular dependency. */
async function authFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/auth${endpoint}`, {
    ...options,
    credentials: 'include', // Send HTTP-only cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (response.status === 204) return undefined as T

  const data = await response.json()

  if (!response.ok) {
    const message = data?.detail || data?.error?.message || 'Authentication failed'
    throw new Error(message)
  }

  return data as T
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  accessToken: null,
  isLoading: false,
  isInitialized: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true })
    try {
      const data = await authFetch<{ access_token: string }>('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      set({ accessToken: data.access_token })

      // Fetch user profile
      const user = await authFetch<AuthUser>('/me', {
        headers: { Authorization: `Bearer ${data.access_token}` },
      })
      set({ user, isLoading: false })
    } catch (error) {
      set({ user: null, accessToken: null, isLoading: false })
      throw error
    }
  },

  register: async (email: string, password: string) => {
    set({ isLoading: true })
    try {
      const data = await authFetch<{ message: string }>('/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      set({ isLoading: false })
      return data.message
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  logout: async () => {
    try {
      await authFetch('/logout', { method: 'POST' })
    } catch {
      // Logout endpoint failure is non-critical — clear local state regardless
    }
    set({ user: null, accessToken: null })
  },

  initialize: async () => {
    // Don't re-initialize if already done or in progress
    if (get().isInitialized || get().isLoading) return
    set({ isLoading: true })

    try {
      // Try refreshing — the HTTP-only cookie is sent automatically
      const data = await authFetch<{ access_token: string }>('/refresh', {
        method: 'POST',
      })
      set({ accessToken: data.access_token })

      const user = await authFetch<AuthUser>('/me', {
        headers: { Authorization: `Bearer ${data.access_token}` },
      })
      set({ user, isLoading: false, isInitialized: true })
    } catch {
      // No valid session — user needs to log in
      set({ user: null, accessToken: null, isLoading: false, isInitialized: true })
    }
  },

  getAccessToken: async () => {
    const { accessToken } = get()
    if (accessToken) return accessToken

    // Try refreshing
    try {
      const data = await authFetch<{ access_token: string }>('/refresh', {
        method: 'POST',
      })
      set({ accessToken: data.access_token })
      return data.access_token
    } catch {
      get().clearAuth()
      return null
    }
  },

  clearAuth: () => {
    set({ user: null, accessToken: null })
  },

  verifyEmail: async (token: string) => {
    const data = await authFetch<{ message: string }>('/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
    return data.message
  },

  forgotPassword: async (email: string) => {
    const data = await authFetch<{ message: string }>('/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
    return data.message
  },

  resetPassword: async (token: string, password: string) => {
    const data = await authFetch<{ message: string }>('/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    })
    return data.message
  },

  resendVerification: async (email: string) => {
    const data = await authFetch<{ message: string }>('/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
    return data.message
  },
}))
