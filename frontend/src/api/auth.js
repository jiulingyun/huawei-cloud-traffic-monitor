/**
 * 认证 API
 */
import request from '@/utils/request'

/**
 * 用户登录
 * @param {Object} data - 登录数据
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 */
export function login(data) {
  return request({
    url: '/v1/auth/login',
    method: 'post',
    data
  })
}

/**
 * 用户登出
 */
export function logout() {
  return request({
    url: '/v1/auth/logout',
    method: 'post'
  })
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser() {
  return request({
    url: '/v1/auth/me',
    method: 'get'
  })
}
