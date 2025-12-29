/**
 * 账户管理 API
 */
import request from '@/utils/request'

/**
 * 获取账户列表
 * @param {Object} params - 查询参数
 * @param {boolean} params.is_enabled - 过滤启用状态
 * @param {number} params.limit - 返回数量限制
 * @param {number} params.offset - 偏移量
 */
export function getAccounts(params) {
  return request({
    url: '/v1/accounts',
    method: 'get',
    params
  })
}

/**
 * 获取账户详情
 * @param {number} accountId - 账户 ID
 */
export function getAccountDetail(accountId) {
  return request({
    url: `/v1/accounts/${accountId}`,
    method: 'get'
  })
}

/**
 * 创建账户
 * @param {Object} data - 账户数据
 */
export function createAccount(data) {
  return request({
    url: '/v1/accounts',
    method: 'post',
    data
  })
}

/**
 * 更新账户
 * @param {number} accountId - 账户 ID
 * @param {Object} data - 更新数据
 */
export function updateAccount(accountId, data) {
  return request({
    url: `/v1/accounts/${accountId}`,
    method: 'put',
    data
  })
}

/**
 * 删除账户
 * @param {number} accountId - 账户 ID
 */
export function deleteAccount(accountId) {
  return request({
    url: `/v1/accounts/${accountId}`,
    method: 'delete'
  })
}

/**
 * 启用账户
 * @param {number} accountId - 账户 ID
 */
export function enableAccount(accountId) {
  return request({
    url: `/v1/accounts/${accountId}/enable`,
    method: 'post'
  })
}

/**
 * 禁用账户
 * @param {number} accountId - 账户 ID
 */
export function disableAccount(accountId) {
  return request({
    url: `/v1/accounts/${accountId}/disable`,
    method: 'post'
  })
}

/**
 * 测试账户连接
 * @param {number} accountId - 账户 ID
 */
export function testAccountConnection(accountId) {
  return request({
    url: `/v1/accounts/${accountId}/test`,
    method: 'post'
  })
}
