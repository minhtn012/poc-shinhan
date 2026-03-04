import { defineStore } from 'pinia'
import { ref } from 'vue'

const SESSION_KEY = 'ocr:auth'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(sessionStorage.getItem(SESSION_KEY) === 'true')

  function login(user: string, pass: string): boolean {
    if (user === import.meta.env.VITE_AUTH_USER && pass === import.meta.env.VITE_AUTH_PASS) {
      isAuthenticated.value = true
      sessionStorage.setItem(SESSION_KEY, 'true')
      return true
    }
    return false
  }

  function logout(): void {
    isAuthenticated.value = false
    sessionStorage.removeItem(SESSION_KEY)
  }

  return { isAuthenticated, login, logout }
})
