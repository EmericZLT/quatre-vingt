<template>
  <div class="room-list-container min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
    <div class="max-w-4xl mx-auto">
      <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-bold text-white">游戏大厅</h1>
        <!-- 用户信息/登录入口 -->
        <div class="flex items-center gap-4">
          <template v-if="authStore.isLoggedIn">
            <span class="text-slate-300">
              欢迎, <span class="text-blue-400 font-semibold">{{ authStore.username }}</span>
              <span v-if="authStore.isAdmin" class="ml-1 text-xs bg-amber-600 text-white px-1 rounded">管理员</span>
            </span>
            <button v-if="authStore.isAdmin" @click="showAdminModal = true" class="text-sm text-amber-400 hover:text-amber-300">管理</button>
            <span v-if="authStore.isAdmin" class="text-slate-600">|</span>
            <button @click="authStore.logout()" class="text-sm text-red-400 hover:text-red-300">退出登录</button>
          </template>
          <template v-else>
            <button @click="showAuthModal = 'login'" class="text-sm text-blue-400 hover:text-blue-300">登录</button>
            <span class="text-slate-600">|</span>
            <button @click="showAuthModal = 'register'" class="text-sm text-blue-400 hover:text-blue-300">注册</button>
          </template>
        </div>
      </div>
      
      <!-- 创建房间区域 -->
      <div class="bg-slate-800 rounded-lg p-6 mb-6">
        <h2 class="text-xl font-semibold text-white mb-4">创建新房间</h2>
        <div class="space-y-4">
          <!-- 房间名和玩家名输入 -->
          <div class="flex gap-4">
            <input
              v-model="newRoomName"
              type="text"
              placeholder="输入房间名称"
              data-input-type="newRoomName"
              maxlength="15"
              class="flex-1 px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400"
              @keyup.enter="createRoom"
            />
            <input
              v-model="playerName"
              type="text"
              placeholder="输入你的名字"
              data-input-type="playerName"
              maxlength="8"
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
          
          <!-- 房间配置下拉框 -->
          <div>
            <button
              @click="showRoomConfig = !showRoomConfig"
              class="flex items-center gap-2 text-slate-300 text-sm hover:text-white transition-colors"
            >
              <span>房间配置</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4 transition-transform"
                :class="{ 'rotate-180': showRoomConfig }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div v-show="showRoomConfig" class="mt-3 flex flex-col gap-4">
              <div class="flex items-center gap-3">
                <label class="text-slate-300 text-sm">出牌等待时间：</label>
                <div class="flex gap-2">
                  <button
                    @click="playTimeLimit = 10"
                    :class="[
                      'px-4 py-2 rounded text-sm transition-colors',
                      playTimeLimit === 10
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    ]"
                  >
                    短 (10秒)
                  </button>
                  <button
                    @click="playTimeLimit = 18"
                    :class="[
                      'px-4 py-2 rounded text-sm transition-colors',
                      playTimeLimit === 18
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    ]"
                  >
                    中 (18秒)
                  </button>
                  <button
                    @click="playTimeLimit = 25"
                    :class="[
                      'px-4 py-2 rounded text-sm transition-colors',
                      playTimeLimit === 25
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    ]"
                  >
                    长 (25秒)
                  </button>
                  <button
                    @click="playTimeLimit = 0"
                    :class="[
                      'px-4 py-2 rounded text-sm transition-colors',
                      playTimeLimit === 0
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    ]"
                  >
                    不限制
                  </button>
                </div>
              </div>
              
              <div class="flex items-center gap-3">
                <label class="text-slate-300 text-sm">升级模式：</label>
                <div class="flex gap-2 items-center">
                  <div class="relative group">
                    <button
                      @click="levelUpMode = 'default'"
                      :class="[
                        'px-4 py-2 rounded text-sm transition-colors flex items-center gap-2',
                        levelUpMode === 'default'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      ]"
                    >
                      滁州版
                      <div class="relative">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                          <div class="font-semibold mb-1">滁州版规则</div>
                          <div>• 分数抹零（向下取整到10的倍数）</div>
                          <div>• 得分≤0：庄家升12级</div>
                          <div>• 得分≥80：闲家每10分升1级</div>
                          <div>• 得分＜80：庄家每10分升1级</div>
                          <div>• 75分特殊处理：庄家连庄但不升级</div>
                        </div>
                      </div>
                    </button>
                  </div>
                  <div class="relative group">
                    <button
                      @click="levelUpMode = 'standard'"
                      :class="[
                        'px-4 py-2 rounded text-sm transition-colors flex items-center gap-2',
                        levelUpMode === 'standard'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      ]"
                    >
                      国标版
                      <div class="relative">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                          <div class="font-semibold mb-1">国标版规则</div>
                          <div>• 分数不抹零（使用原始分数）</div>
                          <div>• 得分≤0：庄家升3级，每少40分多升1级</div>
                          <div>• 得分5-35：庄家升2级</div>
                          <div>• 得分40-75：庄家升1级</div>
                          <div>• 得分≥80：闲家每多40分升1级</div>
                        </div>
                      </div>
                    </button>
                  </div>
                </div>
              </div>
              
              <div class="flex items-center gap-3">
                <label class="text-slate-300 text-sm">打A不过重置：</label>
                <div class="flex gap-2 items-center">
                  <button
                    @click="aceResetEnabled = true"
                    :class="[
                      'px-4 py-2 rounded text-sm transition-colors',
                      aceResetEnabled
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    ]"
                  >
                    是
                  </button>
                  <button
                    @click="aceResetEnabled = false"
                    :class="[
                      'px-4 py-2 rounded text-sm transition-colors',
                      !aceResetEnabled
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    ]"
                  >
                    否
                  </button>
                  <div class="relative group">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-slate-400 cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-56 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                      <div class="font-semibold mb-1">打A不过重置规则</div>
                      <div>• 是：连续3次打A不过，级别重置为2</div>
                      <div>• 否：打A不过不影响级别</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
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
                  <span class="ml-3 text-blue-400">
                    ⏱ {{ getPlayTimeLimitLabel(room.play_time_limit) }}
                  </span>
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
                  maxlength="8"
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

    <!-- 认证弹窗 -->
    <div v-if="showAuthModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div class="bg-slate-800 p-8 rounded-lg shadow-2xl w-full max-md border border-slate-700" style="max-width: 400px;">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-white">{{ showAuthModal === 'login' ? '登录' : '注册' }}</h2>
          <button @click="showAuthModal = null" class="text-slate-400 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form @submit.prevent="handleAuth" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">用户名</label>
            <input
              v-model="authForm.username"
              type="text"
              required
              class="w-full px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:border-blue-500 focus:outline-none"
              placeholder="2-15位字符"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">密码</label>
            <input
              v-model="authForm.password"
              type="password"
              required
              class="w-full px-4 py-2 rounded bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:border-blue-500 focus:outline-none"
              placeholder="至少6位"
            />
          </div>
          <div v-if="authError" class="text-red-400 text-sm">{{ authError }}</div>
          <button
            type="submit"
            :disabled="authLoading"
            class="w-full py-3 rounded bg-blue-600 hover:bg-blue-700 text-white font-bold transition-colors disabled:bg-slate-600"
          >
            {{ authLoading ? '处理中...' : (showAuthModal === 'login' ? '立即登录' : '注册账号') }}
          </button>
        </form>
        
        <div class="mt-4 text-center">
          <button
            @click="showAuthModal = showAuthModal === 'login' ? 'register' : 'login'"
            class="text-sm text-slate-400 hover:text-blue-400"
          >
            {{ showAuthModal === 'login' ? '没有账号？立即注册' : '已有账号？立即登录' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 管理员弹窗 -->
    <div v-if="showAdminModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div class="bg-slate-800 p-8 rounded-lg shadow-2xl w-full max-md border border-slate-700" style="max-width: 450px;">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-white">系统管理</h2>
          <button @click="showAdminModal = false" class="text-slate-400 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="space-y-6">
          <!-- 数据清理 -->
          <div class="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
            <h3 class="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              用户数据清理
            </h3>
            <p class="text-sm text-slate-400 mb-4">
              该操作将永久删除指定天数内未登录的非管理员用户及其战绩数据。
            </p>
            <div class="flex items-center gap-4">
              <div class="flex-1">
                <label class="block text-xs text-slate-500 mb-1">未登录天数</label>
                <input
                  v-model.number="cleanupDays"
                  type="number"
                  min="1"
                  class="w-full px-3 py-2 rounded bg-slate-800 text-white border border-slate-600 focus:border-red-500 focus:outline-none"
                />
              </div>
              <button
                @click="handleCleanup"
                :disabled="adminLoading"
                class="mt-5 px-6 py-2 rounded bg-red-600 hover:bg-red-700 text-white font-bold transition-colors disabled:bg-slate-600"
              >
                {{ adminLoading ? '执行中...' : '立即执行' }}
              </button>
            </div>
          </div>
          
          <div v-if="adminMessage" :class="['p-3 rounded text-sm', adminMessage.type === 'success' ? 'bg-green-900/50 text-green-400 border border-green-700' : 'bg-red-900/50 text-red-400 border border-red-700']">
            {{ adminMessage.text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useRoomStore } from '@/stores/room'
import { useAuthStore } from '@/stores/auth'
import { getApiUrl } from '@/config/env'

const router = useRouter()
const roomStore = useRoomStore()
const authStore = useAuthStore()

const newRoomName = ref('')
const playerName = ref(authStore.username || '') // 默认使用已登录用户名
const playTimeLimit = ref(18)  // 默认18秒（中等）
const levelUpMode = ref('default')  // 升级模式：'default'（滁州版）或'standard'（国标版）
const aceResetEnabled = ref(true)  // 打A不过重置：连续3次打A不过是否重置级别
const showRoomConfig = ref(false)  // 房间配置下拉框是否展开
const creating = ref(false)
const loading = ref(true)
const joinPlayerNames = ref<Record<string, string>>({})
const joining = ref<Record<string, boolean>>({})

const rooms = ref<any[]>([])
const canResume = ref(false)

// 认证相关
const showAuthModal = ref<'login' | 'register' | null>(null)
const authLoading = ref(false)
const authError = ref('')
const authForm = ref({ username: '', password: '' })

// 管理相关
const showAdminModal = ref(false)
const adminLoading = ref(false)
const cleanupDays = ref(30)
const adminMessage = ref<{text: string, type: 'success' | 'error'} | null>(null)

// 监听登录状态变化，自动填充 playerName
watch(() => authStore.username, (newVal) => {
  if (newVal) playerName.value = newVal
})

// 处理认证逻辑
async function handleAuth() {
  authLoading.value = true
  authError.value = ''
  const endpoint = showAuthModal.value === 'login' ? '/api/auth/login' : '/api/auth/register'
  
  try {
    const response = await fetch(getApiUrl(endpoint), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(authForm.value)
    })
    
    const data = await response.json()
    if (response.ok) {
      authStore.setAuth(data.access_token, data.username, data.is_admin)
      playerName.value = data.username
      showAuthModal.value = null
      authForm.value = { username: '', password: '' }
    } else {
      authError.value = data.detail || '操作失败'
    }
  } catch (err) {
    authError.value = '网络错误，请稍后再试'
  } finally {
    authLoading.value = false
  }
}

// 统一带 Token 的 fetch 封装
async function authenticatedFetch(url: string, options: RequestInit = {}) {
  const headers = {
    ...(options.headers || {}),
    'Content-Type': 'application/json',
  } as Record<string, string>

  if (authStore.token) {
    headers['Authorization'] = `Bearer ${authStore.token}`
  }

  return fetch(url, { ...options, headers })
}

// 处理清理逻辑
async function handleCleanup() {
  if (!confirm(`确定要清理 ${cleanupDays.value} 天内未登录的用户吗？此操作不可逆！`)) return
  
  adminLoading.value = true
  adminMessage.value = null
  
  try {
    const response = await authenticatedFetch(getApiUrl(`/api/auth/cleanup?days=${cleanupDays.value}`), {
      method: 'DELETE'
    })
    const data = await response.json()
    if (response.ok) {
      adminMessage.value = { text: data.message, type: 'success' }
    } else {
      adminMessage.value = { text: data.detail || '清理失败', type: 'error' }
    }
  } catch (err) {
    adminMessage.value = { text: '网络错误', type: 'error' }
  } finally {
    adminLoading.value = false
  }
}

// 保存当前聚焦的输入框信息
let focusedInputInfo: {
  type: 'playerName' | 'newRoomName' | 'joinRoom'
  roomId?: string
  selectionStart: number | null
  selectionEnd: number | null
} | null = null

// 加载房间列表 (保留你的焦点恢复逻辑)
async function loadRooms() {
  const activeElement = document.activeElement
  if (activeElement && activeElement.tagName === 'INPUT') {
    const input = activeElement as HTMLInputElement
    const dataInputType = input.getAttribute('data-input-type')
    const dataRoomId = input.getAttribute('data-room-id')
    
    if (dataInputType === 'playerName' || dataInputType === 'newRoomName') {
      focusedInputInfo = {
        type: dataInputType as any,
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
    const apiUrl = getApiUrl('/api/rooms')
    const response = await fetch(apiUrl)
    if (response.ok) {
      rooms.value = await response.json()
    }
  } catch (error) {
    console.error('加载房间列表异常:', error)
  } finally {
    loading.value = false
  }

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

// 恢复对局 (使用 authenticatedFetch)
async function resumeRoom() {
  if (!roomStore.roomId || !roomStore.token) return
  try {
    const response = await authenticatedFetch(getApiUrl(`/api/rooms/${roomStore.roomId}/reconnect`), {
      method: 'POST',
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
    roomStore.clearRoom()
    canResume.value = false
  } catch (e) {
    console.error('Failed to resume room:', e)
  }
}

// 创建房间 (保留你的验证和 log 逻辑)
async function createRoom() {
  const roomName = newRoomName.value.trim()
  const name = playerName.value.trim()
  
  if (!roomName || !name) {
    alert('房间名和玩家名不能为空')
    return
  }
  
  if (roomName.length > 15) {
    alert('房间名不能超过15个字符')
    return
  }
  
  if (name.length > 8) {
    alert('玩家名不能超过8个字符')
    return
  }
  
  try {
    creating.value = true
    const apiUrl = getApiUrl('/api/rooms')
    console.log('创建房间，请求 URL:', apiUrl)
    
    const response = await authenticatedFetch(apiUrl, {
      method: 'POST',
      body: JSON.stringify({ 
        name: roomName,
        play_time_limit: playTimeLimit.value,
        level_up_mode: levelUpMode.value,
        ace_reset_enabled: aceResetEnabled.value
      })
    })
    
    if (response.ok) {
      const room = await response.json()
      await joinRoom(room.id, name)
    } else {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      alert(`创建房间失败: ${errorData.detail || response.statusText}`)
    }
  } catch (error) {
    console.error('创建房间异常:', error)
    alert(`创建房间失败: ${error instanceof Error ? error.message : String(error)}`)
  } finally {
    creating.value = false
  }
}

// 加入房间 (保留你的验证逻辑)
async function joinRoom(roomId: string, name?: string) {
  const playerNameToUse = (name || joinPlayerNames.value[roomId] || playerName.value || '').trim()
  if (!playerNameToUse) {
    alert('请输入玩家名')
    return
  }
  
  if (playerNameToUse.length > 8) {
    alert('玩家名不能超过8个字符')
    return
  }
  
  try {
    joining.value[roomId] = true
    const response = await authenticatedFetch(getApiUrl(`/api/rooms/${roomId}/join`), {
      method: 'POST',
      body: JSON.stringify({ player_name: playerNameToUse })
    })
    
    if (response.ok) {
      const room = await response.json()
      // 识别玩家（如果是登录状态，优先匹配用户名）
      const player = room.players.find((p: any) => 
        (authStore.isLoggedIn && p.name === authStore.username) || p.name === playerNameToUse
      )
      if (player) {
        roomStore.setRoom(room.id, player.id, player.name, player.position, room.owner_id, room.name, player.token)
        router.push(`/game/${roomId}`)
      }
    } else {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      alert(errorData.detail || '加入房间失败')
    }
  } catch (error) {
    console.error('Failed to join room:', error)
    alert('网络错误，加入房间失败')
  } finally {
    joining.value[roomId] = false
  }
}

// 智能刷新
let refreshInterval: number | null = null

function isAnyInputFocused(): boolean {
  const activeElement = document.activeElement
  if (!activeElement || activeElement.tagName !== 'INPUT') return false
  const input = activeElement as HTMLInputElement
  return input.getAttribute('data-input-type') !== null || 
         input.getAttribute('data-room-id') !== null
}

function smartRefresh() {
  if (!isAnyInputFocused() && !showAuthModal.value && !showAdminModal.value) {
    loadRooms()
  }
}

function getPlayTimeLimitLabel(timeLimit: number): string {
  switch(timeLimit) {
    case 10: return '短 (10秒)'
    case 18: return '中 (18秒)'
    case 25: return '长 (25秒)'
    case 0: return '不限制'
    default: return `${timeLimit}秒`
  }
}

onMounted(() => {
  roomStore.loadFromStorage()
  canResume.value = !!roomStore.roomId && !!roomStore.token
  loadRooms()
  refreshInterval = window.setInterval(smartRefresh, 10000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.room-list-container {
  background-attachment: fixed;
}
</style>
