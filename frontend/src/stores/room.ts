import { defineStore } from 'pinia'

export const useRoomStore = defineStore('room', {
  state: () => ({
    roomId: '',
    playerId: '',
    playerName: '',
    playerPosition: '' as 'NORTH' | 'WEST' | 'SOUTH' | 'EAST' | '',
  }),
  actions: {
    setRoom(roomId: string, playerId: string, playerName: string, playerPosition: string) {
      this.roomId = roomId
      this.playerId = playerId
      this.playerName = playerName
      this.playerPosition = playerPosition.toUpperCase() as 'NORTH' | 'WEST' | 'SOUTH' | 'EAST'
    },
    clearRoom() {
      this.roomId = ''
      this.playerId = ''
      this.playerName = ''
      this.playerPosition = ''
    }
  },
  // 如果需要持久化，可以安装 pinia-plugin-persistedstate
  // persist: {
  //   storage: localStorage,
  // }
})

