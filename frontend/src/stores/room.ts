import { defineStore } from 'pinia'

export const useRoomStore = defineStore('room', {
  state: () => ({
    roomId: '',
    playerId: '',
    playerName: '',
    playerPosition: '' as 'NORTH' | 'WEST' | 'SOUTH' | 'EAST' | '',
    ownerId: '',
    roomName: '',
    token: '',
  }),
  actions: {
    loadFromStorage() {
      try {
        const raw = sessionStorage.getItem('roomCtx')
        if (!raw) return
        const j = JSON.parse(raw)
        this.roomId = j.roomId || ''
        this.playerId = j.playerId || ''
        this.playerName = j.playerName || ''
        this.playerPosition = j.playerPosition || ''
        this.ownerId = j.ownerId || ''
        this.roomName = j.roomName || ''
        this.token = j.token || ''
      } catch {}
    },
    persist() {
      const payload = {
        roomId: this.roomId,
        playerId: this.playerId,
        playerName: this.playerName,
        playerPosition: this.playerPosition,
        ownerId: this.ownerId,
        roomName: this.roomName,
        token: this.token,
      }
      sessionStorage.setItem('roomCtx', JSON.stringify(payload))
    },
    setRoom(roomId: string, playerId: string, playerName: string, playerPosition: string, ownerId?: string, roomName?: string, token?: string) {
      this.roomId = roomId
      this.playerId = playerId
      this.playerName = playerName
      this.playerPosition = playerPosition.toUpperCase() as 'NORTH' | 'WEST' | 'SOUTH' | 'EAST'
      if (ownerId) this.ownerId = ownerId
      if (roomName) this.roomName = roomName
      if (token) this.token = token
      this.persist()
    },
    updateOwner(ownerId: string) {
      this.ownerId = ownerId
      this.persist()
    },
    updateRoomName(name: string) {
      this.roomName = name
      this.persist()
    },
    clearRoom() {
      this.roomId = ''
      this.playerId = ''
      this.playerName = ''
      this.playerPosition = ''
      this.ownerId = ''
      this.roomName = ''
      this.token = ''
      sessionStorage.removeItem('roomCtx')
    }
  },
  // 手工持久化
})

