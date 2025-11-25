/**
 * 环境变量配置
 * 从 import.meta.env 读取，支持开发和生产环境
 */

// API 基础 URL（用于 REST API）
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// WebSocket URL（用于实时通信）
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

/**
 * 获取 WebSocket URL
 * 根据当前协议自动选择 ws:// 或 wss://
 */
export function getWebSocketUrl(path: string): string {
  // 如果环境变量已设置，直接使用
  if (WS_URL && (WS_URL.startsWith('ws://') || WS_URL.startsWith('wss://'))) {
    return `${WS_URL}${path.startsWith('/') ? path : '/' + path}`
  }
  
  // 否则根据当前页面协议自动选择
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // 如果 WS_URL 设置了但没有协议，使用它作为 host
    if (WS_URL) {
      const host = WS_URL.replace(/^https?:\/\//, '').replace(/^wss?:\/\//, '')
      return `${protocol}//${host}${path.startsWith('/') ? path : '/' + path}`
    }
    // 否则使用当前页面的 host
    return `${protocol}//${window.location.host}${path.startsWith('/') ? path : '/' + path}`
  }
  
  // 开发环境默认值
  return `ws://localhost:8000${path.startsWith('/') ? path : '/' + path}`
}

/**
 * 获取 API URL
 */
export function getApiUrl(path: string): string {
  const baseUrl = API_URL || 'http://localhost:8000'
  return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`
}

