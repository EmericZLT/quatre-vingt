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
            class="flex-1 px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400"
            @keyup.enter="createRoom"
          />
          <input
            v-model="playerName"
            type="text"
            placeholder="输入你的名字"
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
        <h2 class="text-xl font-semibold text-white mb-4">房间列表</h2>
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
                  玩家: {{ room.players.map(p => p.name).join(', ') || '暂无' }}
                </div>
              </div>
              <div class="flex gap-2 items-center">
                <input
                  v-if="!room.is_full"
                  v-model="joinPlayerNames[room.id]"
                  type="text"
                  placeholder="你的名字"
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRoomStore } from '@/stores/room'
import { getApiUrl } from '@/config/env'

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

// 加载房间列表
async function loadRooms() {
  try {
    loading.value = true
    const apiUrl = getApiUrl('/api/rooms')
    console.log('加载房间列表，请求 URL:', apiUrl)
    const response = await fetch(apiUrl)
    console.log('响应状态:', response.status)
    if (response.ok) {
      rooms.value = await response.json()
      console.log('房间列表加载成功，房间数:', rooms.value.length)
    } else {
      console.error('加载房间列表失败:', response.status, response.statusText)
    }
  } catch (error) {
    console.error('加载房间列表异常:', error)
  } finally {
    loading.value = false
  }
}

// 恢复对局
async function resumeRoom() {
  if (!roomStore.roomId || !roomStore.token) return
  try {
    const response = await fetch(getApiUrl(`/api/rooms/${roomStore.roomId}/reconnect`), {
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
    const apiUrl = getApiUrl('/api/rooms')
    console.log('创建房间，请求 URL:', apiUrl)
    console.log('请求数据:', { name: newRoomName.value })
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newRoomName.value })
    })
    
    console.log('响应状态:', response.status, response.statusText)
    
    if (response.ok) {
      const room = await response.json()
      console.log('房间创建成功:', room)
      // 加入房间
      await joinRoom(room.id, playerName.value)
    } else {
      const errorText = await response.text()
      console.error('创建房间失败，响应:', errorText)
      alert(`创建房间失败: ${response.status} ${response.statusText}\n${errorText}`)
    }
  } catch (error) {
    console.error('创建房间异常:', error)
    alert(`创建房间失败: ${error instanceof Error ? error.message : String(error)}`)
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
    const response = await fetch(getApiUrl(`/api/rooms/${roomId}/join`), {
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

// 定期刷新房间列表
let refreshInterval: number | null = null

onMounted(() => {
  // 尝试从本地恢复上下文
  roomStore.loadFromStorage()
  canResume.value = !!roomStore.roomId && !!roomStore.token
  loadRooms()
  // 每3秒刷新一次房间列表
  refreshInterval = window.setInterval(loadRooms, 3000)
})

// 清理定时器
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

