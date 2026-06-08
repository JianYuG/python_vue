/**
 * 密码加密工具
 *
 * 策略：前端使用 SHA-256 对原始密码做哈希，再传输给后端。
 * 好处：
 *   - 网络层：即使被抓包也无法还原明文密码
 *   - 数据库层：后端仍用 BCrypt 对哈希值二次加密存储，双重保护
 */
import SHA256 from 'crypto-js/sha256'

/**
 * 对密码做 SHA-256 哈希，返回十六进制字符串（64位）
 * @param {string} password - 原始明文密码
 * @returns {string} SHA-256 哈希字符串（小写十六进制）
 */
export function hashPassword(password) {
  return SHA256(password).toString()
}
