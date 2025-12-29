/**
 * 仪表板 API
 */
import request from '@/utils/request'

/**
 * 获取仪表板统计数据
 */
export function getDashboardStats() {
  return request({
    url: '/v1/dashboard/stats',
    method: 'get'
  })
}

/**
 * 获取仪表板账户列表
 * @param {Object} params - 查询参数
 */
export function getDashboardAccounts(params) {
  return request({
    url: '/v1/dashboard/accounts',
    method: 'get',
    params
  })
}

/**
 * 获取最近通知列表
 * @param {Object} params - 查询参数
 */
export function getDashboardNotifications(params) {
  return request({
    url: '/v1/dashboard/notifications',
    method: 'get',
    params
  })
}

/**
 * 获取系统信息
 */
export function getSystemInfo() {
  return request({
    url: '/v1/dashboard/system-info',
    method: 'get'
  })
}
