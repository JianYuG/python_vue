import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getUserInfo as getUserInfoApi } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))

  /**
   * 登录
   */
  async function loginAction(username, password) {
    try {
      const res = await loginApi({ username, password })
      const newToken = res.data.token
      token.value = newToken
      localStorage.setItem('token', newToken)
      // 登录后获取用户信息
      await fetchUserInfo()
      return res
    } catch (error) {
      throw error
    }
  }

  /**
   * 获取用户信息
   */
  async function fetchUserInfo() {
    try {
      const res = await getUserInfoApi()
      userInfo.value = res.data
      localStorage.setItem('userInfo', JSON.stringify(res.data))
      return res.data
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  /**
   * 退出登录
   */
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  /**
   * 是否已登录
   */
  function isLoggedIn() {
    return !!token.value
  }

  return {
    token,
    userInfo,
    loginAction,
    fetchUserInfo,
    logout,
    isLoggedIn
  }
})
