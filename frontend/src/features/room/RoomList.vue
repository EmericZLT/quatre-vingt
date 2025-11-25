<template>
  <div class="room-list-container min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold text-white mb-8 text-center">八十分游戏大厅</h1>
      
      <!-- 创建房间区域 -->
      <div class="bg-slate-800 rounded-lg p-6 mb-6">
        <h2 class="text-xl font-semibold text-white mb-4">创建新房间</h2>
        <div class="flex gap-4">
          <input
            v-model="newRoomName"
            type="text"
            placeholder="输入房间名称"
            data-input-type="newRoomName"
            class="flex-1 px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400"
            @keyup.enter="createRoom"
          />
          <input
            v-model="playerName"
            type="text"
            placeholder="输入你的名字"
            data-input-type="playerName"
            class="flex-1 px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400"
            @keyup.enter="createRoom"
          />
          <button
            @click="createRoom"
            :disabled="!newRoomName || !playerName || creating"
            class="px-6 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white disabled:bg-slate-600 disabled:cursor-not-allowed"
          >
            {{ creating ? '创建中...' : '创建房间' }}
          </button>
        </div>
      </div>

      <!-- 房间列表 -->
      <div class="bg-slate-800 rounded-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-white">房间列表</h2>
          <button
            @click="loadRooms"
            :disabled="loading"
            class="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm disabled:bg-slate-600 disabled:cursor-not-allowed flex items-center gap-2"
            title="手动刷新房间列表"
          >
            <svg v-if="!loading" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span v-if="loading">刷新中...</span>
            <span v-else>刷新</span>
          </button>
        </div>
        <div v-if="canResume" class="mb-4">
          <button
            class="px-4 py-2 rounded bg-amber-600 hover:bg-amber-700 text-white text-sm"
            @click="resumeRoom"
          >
            恢复上次对局
          </button>
        </div>
        <div v-if="loading" class="text-center text-slate-400 py-8">加载中...</div>
        <div v-else-if="rooms.length === 0" class="text-center text-slate-400 py-8">暂无房间</div>
        <div v-else class="space-y-3">
          <div
            v-for="room in rooms"
            :key="room.id"
            class="bg-slate-700 rounded-lg p-4 hover:bg-slate-600 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="text-white font-semibold mb-2">{{ room.name }}</div>
                <div class="text-sm text-slate-300">
                  玩家: {{ room.players.length }} / 4
                  <span v-if="room.is_full" class="ml-2 text-red-400">(已满)</span>
                </div>
                <div class="text-xs text-slate-400 mt-1">
                  玩家: {{ room.players.map((p: any) => p.name).join(', ') || '暂无' }}
                </div>
              </div>
              <div class="flex gap-2 items-center">
                <input
                  v-if="!room.is_full"
                  v-model="joinPlayerNames[room.id]"
                  type="text"
                  placeholder="你的名字"
                  :data-room-id="room.id"
                  class="px-3 py-1 rounded bg-slate-600 text-white text-sm placeholder-slate-400 w-32"
                  @keyup.enter="joinRoom(room.id)"
                />
                <button
                  v-if="!room.is_full"
                  @click="joinRoom(room.id)"
                  :disabled="!joinPlayerNames[room.id] || joining[room.id]"
                  class="px-4 py-2 rounded bg-green-600 hover:bg-green-700 text-white text-sm disabled:bg-slate-600 disabled:cursor-not-allowed"
                >
                  {{ joining[room.id] ? '加入中...' : '加入' }}
                </button>
                <span v-else class="text-slate-400 text-sm">房间已满</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useRoomStore } from '@/stores/room'

const router = useRouter()
const roomStore = useRoomStore()

const newRoomName = ref('')
const playerName = ref('')
const creating = ref(false)
const loading = ref(true)
const joinPlayerNames = ref<Record<string, string>>({})
const joining = ref<Record<string, boolean>>({})

const rooms = ref<any[]>([])
const canResume = ref(false)

// 保存当前聚焦的输入框信息
let focusedInputInfo: {
  type: 'playerName' | 'newRoomName' | 'joinRoom'
  roomId?: string
  selectionStart: number | null
  selectionEnd: number | null
} | null = null

// 加载房间列表
async function loadRooms() {
  // 保存当前聚焦的输入框信息（仅在手动刷新时保留，自动刷新时如果输入框聚焦则跳过）
  const activeElement = document.activeElement
  if (activeElement && activeElement.tagName === 'INPUT') {
    const input = activeElement as HTMLInputElement
    const dataInputType = input.getAttribute('data-input-type')
    const dataRoomId = input.getAttribute('data-room-id')
    
    if (dataInputType === 'playerName' || dataInputType === 'newRoomName') {
      focusedInputInfo = {
        type: dataInputType,
        selectionStart: input.selectionStart,
        selectionEnd: input.selectionEnd
      }
    } else if (dataRoomId) {
      focusedInputInfo = {
        type: 'joinRoom',
        roomId: dataRoomId,
        selectionStart: input.selectionStart,
        selectionEnd: input.selectionEnd
      }
    } else {
      focusedInputInfo = null
    }
  } else {
    focusedInputInfo = null
  }

  try {
    loading.value = true
    const response = await fetch('http://127.0.0.1:8000/api/rooms')
    if (response.ok) {
      rooms.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to load rooms:', error)
  } finally {
    loading.value = false
  }

  // 恢复焦点（仅在之前有焦点时恢复）
  await nextTick()
  if (focusedInputInfo) {
    let inputToFocus: HTMLInputElement | null = null
    if (focusedInputInfo.type === 'playerName') {
      inputToFocus = document.querySelector('input[data-input-type="playerName"]') as HTMLInputElement
    } else if (focusedInputInfo.type === 'newRoomName') {
      inputToFocus = document.querySelector('input[data-input-type="newRoomName"]') as HTMLInputElement
    } else if (focusedInputInfo.type === 'joinRoom' && focusedInputInfo.roomId) {
      inputToFocus = document.querySelector(`input[data-room-id="${focusedInputInfo.roomId}"]`) as HTMLInputElement
    }
    
    if (inputToFocus) {
      inputToFocus.focus()
      if (focusedInputInfo.selectionStart !== null && focusedInputInfo.selectionEnd !== null) {
        inputToFocus.setSelectionRange(focusedInputInfo.selectionStart, focusedInputInfo.selectionEnd)
      }
    }
  }
}

// 恢复对局
async function resumeRoom() {
  if (!roomStore.roomId || !roomStore.token) return
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/rooms/${roomStore.roomId}/reconnect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: roomStore.token })
    })
    if (response.ok) {
      const room = await response.json()
      const me = (room.players || []).find((p: any) => p.token === roomStore.token)
      if (me) {
        roomStore.setRoom(room.id, me.id, me.name, me.position, room.owner_id, room.name, me.token)
        router.push(`/game/${room.id}`)
        return
      }
    }
    // 如果失败，清理上下文
    console.warn('[Resume] token invalid, clearing context')
    roomStore.clearRoom()
    canResume.value = false
  } catch (e) {
    console.error('Failed to resume room:', e)
  }
}

// 创建房间
async function createRoom() {
  if (!newRoomName.value || !playerName.value) return
  
  try {
    creating.value = true
    const response = await fetch('http://127.0.0.1:8000/api/rooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newRoomName.value })
    })
    
    if (response.ok) {
      const room = await response.json()
      // 加入房间
      await joinRoom(room.id, playerName.value)
    } else {
      alert('创建房间失败')
    }
  } catch (error) {
    console.error('Failed to create room:', error)
    alert('创建房间失败')
  } finally {
    creating.value = false
  }
}

// 加入房间
async function joinRoom(roomId: string, name?: string) {
  const playerNameToUse = name || joinPlayerNames.value[roomId]
  if (!playerNameToUse) return
  
  try {
    joining.value[roomId] = true
    const response = await fetch(`http://127.0.0.1:8000/api/rooms/${roomId}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_name: playerNameToUse })
    })
    
    if (response.ok) {
      const room = await response.json()
      // 找到刚加入的玩家
      const player = room.players.find((p: any) => p.name === playerNameToUse)
      if (player) {
        // 保存房间和玩家信息（含token）
        roomStore.setRoom(room.id, player.id, player.name, player.position, room.owner_id, room.name, player.token)
        // 跳转到游戏界面
        router.push(`/game/${room.id}`)
      }
    } else {
      const error = await response.json()
      alert(error.detail || '加入房间失败')
    }
  } catch (error) {
    console.error('Failed to join room:', error)
    alert('加入房间失败')
  } finally {
    joining.value[roomId] = false
  }
}

// 定期刷新房间列表（只在没有输入框聚焦时刷新）
let refreshInterval: number | null = null

// 检查是否有输入框正在聚焦
function isAnyInputFocused(): boolean {
  const activeElement = document.activeElement
  if (!activeElement || activeElement.tagName !== 'INPUT') {
    return false
  }
  const input = activeElement as HTMLInputElement
  return input.getAttribute('data-input-type') !== null || 
         input.getAttribute('data-room-id') !== null
}

// 智能刷新：只在没有输入框聚焦时才刷新
function smartRefresh() {
  if (!isAnyInputFocused()) {
    loadRooms()
  }
}

onMounted(() => {
  // 尝试从本地恢复上下文
  roomStore.loadFromStorage()
  canResume.value = !!roomStore.roomId && !!roomStore.token
  loadRooms()
  // 每3秒智能刷新一次房间列表（只在没有输入框聚焦时）
  refreshInterval = window.setInterval(smartRefresh, 3000)
})

// 清理定时器
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

