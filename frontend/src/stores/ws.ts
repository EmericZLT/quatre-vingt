import { defineStore } from 'pinia'
import { createWsClient } from '@/services/ws'
import { useGameStore } from '@/stores/game'

type Msg = { type?: string; [k: string]: any }

export const useWsStore = defineStore('ws', {
  state: () => ({
    url: (import.meta.env.VITE_WS_URL as string) || '',
    connected: false,
    log: [] as string[],
    client: null as null | { send: (d: unknown) => void; close: () => void },
    listeners: [] as Array<(msg: Msg) => void>,
  }),
  actions: {
    connect(customUrl?: string) {
      const url = customUrl || this.url
      if (!url) {
        this._push('WS URL 未配置')
        return
      }
      this.disconnect()
      const client = createWsClient({
        url,
        onOpen: () => { this.connected = true; this._push('WS 连接成功') },
        onClose: () => { this.connected = false; this._push('WS 连接关闭') },
        onMessage: (ev) => {
          try {
            const data = JSON.parse(ev.data) as Msg
            const msgStr = JSON.stringify(data).slice(0, 150)
            this._push(`<- ${data.type || 'message'}${msgStr.length < 100 ? ': ' + msgStr : ''}`)
            this._dispatch(data)
          } catch {
            this._push(`<raw> ${String(ev.data).slice(0,200)}`)
          }
        },
      })
      this.client = client
    },
    disconnect() {
      if (this.client) {
        this.client.close()
        this.client = null
      }
    },
    send(data: unknown) {
      if (!this.client) return
      this.client.send(data)
      this._push(`-> ${JSON.stringify(data).slice(0,200)}`)
    },
    on(handler: (msg: Msg) => void) { this.listeners.push(handler) },
    off(handler: (msg: Msg) => void) { this.listeners = this.listeners.filter(h => h !== handler) },
    _dispatch(msg: Msg) {
      // 分发到 GameStore（内置集成）
      const game = useGameStore()
      switch (msg.type) {
        case 'state_snapshot':
          game.applySnapshot(msg)
          break
        case 'deal_tick':
          game.applyDealTick(msg)
          break
        case 'phase_changed':
          game.applyPhaseChanged(msg)
          break
        case 'score_updated':
          game.applyScoreUpdated(msg)
          break
        case 'koudi_applied':
          game.applyKoudiApplied(msg)
          break
        case 'play_card':
          game.applyPlayCard(msg)
          break
        case 'trick_won':
          game.applyTrickWon(msg)
          break
        case 'bottom_updated':
          game.applyBottomUpdate(msg)
          if (Array.isArray(msg.bottom_cards)) {
            game.applySnapshotBottomCards(msg.bottom_cards)
          }
          break
        case 'card_played':
          game.applyCardPlayed(msg)
          break
        case 'trick_complete':
          game.applyTrickComplete(msg)
          break
        case 'countdown_updated':
          // 添加日志记录收到的倒计时更新
          console.log('[前端调试] 收到倒计时更新消息:', msg)
          console.log('[前端调试] 转换后的数据:', {
            countdown: msg.remaining_time,
            countdown_active: msg.countdown_active || false
          })
          // 转换后端字段名，使用消息中的countdown_active值
          game.applyCountdownUpdated({
            countdown: msg.remaining_time,
            countdown_active: msg.countdown_active || false
          })
          console.log('[前端调试] 更新后gameStore状态:', {
            countdown: game.countdown,
            countdownActive: game.countdownActive
          })
          break
        case 'error':
          // 错误消息已经在日志中显示，这里可以额外处理
          break
        case 'auto_play':
          game.applyAutoPlay(msg)
          break
      }
      // 通知外部监听者
      for (const h of this.listeners) {
        try { h(msg) } catch {}
      }
    },
    _push(s: string) { this.log.unshift(`${new Date().toLocaleTimeString()} ${s}`); if (this.log.length > 200) this.log.pop() }
  }
})


