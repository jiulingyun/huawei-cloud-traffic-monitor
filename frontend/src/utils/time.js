/**
 * 时间处理工具函数
 * 处理UTC时间到本地时间的转换和格式化
 */

/**
 * 格式化日期时间为本地化格式
 * @param {string|Date} dateString - UTC时间字符串或Date对象
 * @param {Object} options - 格式化选项
 * @returns {string} 本地化格式的时间字符串
 */
export function formatDateTime(dateString, options = {}) {
  if (!dateString) return '-'

  // 规范化输入并按 UTC 解析无时区的时间字符串，保证后续转换为本地时间准确
  const date = parseDateAssumeUTC(dateString)

  // 检查日期是否有效
  if (!date || isNaN(date.getTime())) {
    console.warn('Invalid date string:', dateString)
    return '-'
  }

  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }

  return date.toLocaleString('zh-CN', { ...defaultOptions, ...options })
}

/**
 * 格式化日期（仅日期部分）
 * @param {string|Date} dateString - UTC时间字符串或Date对象
 * @returns {string} 本地化格式的日期字符串
 */
export function formatDate(dateString) {
  return formatDateTime(dateString, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: undefined,
    minute: undefined,
    second: undefined
  })
}

/**
 * 格式化时间（仅时间部分）
 * @param {string|Date} dateString - UTC时间字符串或Date对象
 * @returns {string} 本地化格式的时间字符串
 */
export function formatTime(dateString) {
  return formatDateTime(dateString, {
    year: undefined,
    month: undefined,
    day: undefined,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 格式化为相对时间（例如：3分钟前、2小时前）
 * @param {string|Date} dateString - UTC时间字符串或Date对象
 * @returns {string} 相对时间字符串
 */
export function formatRelativeTime(dateString) {
  if (!dateString) return '-'

  const date = parseDateAssumeUTC(dateString)
  if (!date || isNaN(date.getTime())) return '-'

  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 60) {
    return '刚刚'
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes}分钟前`
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return `${hours}小时前`
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400)
    return `${days}天前`
  } else {
    // 超过一周显示具体日期
    return formatDateTime(dateString, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }
}

/**
 * 格式化为Element Plus时间线组件的时间戳格式
 * @param {string|Date} dateString - UTC时间字符串或Date对象
 * @returns {string} 时间线格式的时间字符串
 */
export function formatTimelineTimestamp(dateString) {
  if (!dateString) return '-'

  const date = parseDateAssumeUTC(dateString)
  if (!date || isNaN(date.getTime())) return '-'

  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  // 今天的时间显示时分
  if (diffInSeconds < 86400 && date.toDateString() === now.toDateString()) {
    return date.toLocaleString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  // 昨天的时间显示"昨天 时:分"
  else if (diffInSeconds < 172800) {
    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    if (date.toDateString() === yesterday.toDateString()) {
      return `昨天 ${date.toLocaleString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })}`
    }
  }

  // 其他时间显示日期和时间
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 获取当前本地时间
 * @returns {string} 当前本地时间字符串
 */
export function getCurrentLocalTime() {
  return new Date().toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 将UTC时间转换为本地时间对象
 * @param {string|Date} dateString - UTC时间字符串或Date对象
 * @returns {Date} 本地时间Date对象
 */
export function utcToLocal(dateString) {
  if (!dateString) return null

  const date = parseDateAssumeUTC(dateString)
  if (!date || isNaN(date.getTime())) return null

  // 返回本地时间 Date 对象（Date 内部是以毫秒纪元存储，parseDateAssumeUTC 已按 UTC 解析）
  return date
}

/**
 * 将各种常见的时间字符串解析为 Date 对象：
 * - 如果传入的是 Date 实例，直接返回（作为本地时间使用）
 * - 如果字符串包含时区信息（Z 或 +/-hh:mm），直接用原始字符串解析
 * - 如果字符串是 ISO-like 但无时区（例如 "2025-12-30T16:27:21" 或 "2025-12-30 16:27:21"）
 *   则按 UTC 解析（在字符串末尾添加 'Z'）以避免浏览器将其错误地当作本地时间解析
 * - 对于 "YYYY/MM/DD HH:mm:ss" 之类使用斜杠的格式，先替换为 ISO 格式再按 UTC 解析
 */
function parseDateAssumeUTC(input) {
  if (!input) return null

  // 已经是 Date 对象
  if (input instanceof Date) return input

  if (typeof input !== 'string') {
    // 其他类型（数字时间戳等），尝试直接构造
    const maybeDate = new Date(input)
    return maybeDate
  }

  const str = input.trim()

  // 如果字符串末尾含 Z 或包含时区偏移 (+/-), 直接按原样解析
  if (/[zZ]$/.test(str) || /[+-]\d{2}:?\d{2}$/.test(str)) {
    return new Date(str)
  }

  // 将 "YYYY/MM/DD HH:mm:ss" -> "YYYY-MM-DDTHH:mm:ss"
  const slashFormatMatch = /^\d{4}\/\d{1,2}\/\d{1,2}[ T]\d{2}:\d{2}:\d{2}$/.test(str)
  if (slashFormatMatch) {
    const isoLike = str.replace(/\//g, '-').replace(' ', 'T')
    return new Date(isoLike + 'Z') // 按 UTC 解析
  }

  // ISO-like without timezone: "YYYY-MM-DDTHH:mm:ss" 或 "YYYY-MM-DD HH:mm:ss"
  const isoLikeMatch = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(str)
  if (isoLikeMatch) {
    const isoNormalized = str.replace(' ', 'T')
    return new Date(isoNormalized + 'Z') // 按 UTC 解析
  }

  // 兜底，尝试直接解析（可能按浏览器本地时区解析）
  return new Date(str)
}
