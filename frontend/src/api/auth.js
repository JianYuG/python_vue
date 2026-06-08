import request from '../utils/request'
import { hashPassword } from '../utils/crypto'

/**
 * 用户注册（密码经 SHA-256 哈希后传输）
 */
export function register(data) {
  return request({
    url: '/api/auth/register',
    method: 'post',
    data: {
      ...data,
      password: hashPassword(data.password)
    }
  })
}

/**
 * 用户登录（密码经 SHA-256 哈希后传输）
 */
export function login(data) {
  return request({
    url: '/api/auth/login',
    method: 'post',
    data: {
      ...data,
      password: hashPassword(data.password)
    }
  })
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
  return request({
    url: '/api/auth/user-info',
    method: 'get'
  })
}
