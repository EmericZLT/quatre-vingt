import { defineStore } from 'pinia'

interface UserInfo {
  username: str
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('auth_token') || null,
    username: localStorage.getItem('auth_username') || null,
    isAdmin: localStorage.getItem('auth_is_admin') === 'true',
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  
  actions: {
    setAuth(token: string, username: string, isAdmin: boolean) {
      this.token = token
      this.username = username
      this.isAdmin = isAdmin
      localStorage.setItem('auth_token', token)
      localStorage.setItem('auth_username', username)
      localStorage.setItem('auth_is_admin', String(isAdmin))
    },
    
    logout() {
      this.token = null
      this.username = null
      this.isAdmin = false
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_username')
      localStorage.removeItem('auth_is_admin')
    }
  }
})

