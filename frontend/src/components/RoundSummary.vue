<template>
  <div
    v-if="show && roundSummary"
    class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 bg-slate-900/95 text-white rounded-lg shadow-2xl border-2 border-amber-500 p-8 min-w-[500px]"
  >
    <div class="text-center mb-6">
      <h2 class="text-2xl font-bold text-amber-300 mb-2">本局游戏总结</h2>
      <!-- 胜利信息 -->
      <div v-if="roundSummary.dealer_wins" class="mt-4 bg-gradient-to-r from-yellow-600 to-amber-600 rounded-lg p-4 border-2 border-yellow-400">
        <div class="text-3xl font-bold text-white mb-2">🎉 {{ roundSummary.winner_side_name }} 胜利！🎉</div>
        <div class="text-lg text-yellow-100">游戏将从级牌2重新开始</div>
      </div>
    </div>
    
    <div class="space-y-4 mb-6">
      <!-- 闲家得分 -->
      <div class="flex justify-between items-center">
        <span class="text-slate-300">闲家得分：</span>
        <span class="text-lg font-semibold">{{ roundSummary.idle_score }}分</span>
      </div>
      
      <!-- 扣底信息 -->
      <div v-if="roundSummary.bottom_bonus > 0" class="flex justify-between items-center">
        <span class="text-slate-300">扣底得分：</span>
        <span class="text-lg font-semibold text-amber-300">
          +{{ roundSummary.bottom_bonus }}分
          <span class="text-sm text-slate-400 ml-2">
            (底牌{{ roundSummary.bottom_score }}分 × {{ roundSummary.bottom_score > 0 ? (roundSummary.bottom_bonus / roundSummary.bottom_score).toFixed(0) : 1 }}倍)
          </span>
        </span>
      </div>
      
      <!-- 总得分 -->
      <div class="flex justify-between items-center border-t border-slate-700 pt-2">
        <span class="text-lg font-semibold">闲家总得分：</span>
        <span class="text-2xl font-bold text-amber-300">{{ roundSummary.total_score }}分</span>
      </div>
      
      <!-- 升级信息 -->
      <div class="flex flex-col gap-2 border-t border-slate-700 pt-2">
        <div class="flex justify-between items-center">
          <span class="text-slate-300">南北家级别：</span>
          <span class="text-lg font-semibold">
            {{ getLevelLabel(roundSummary.old_north_south_level) }} → {{ getLevelLabel(roundSummary.new_north_south_level) }}
            <span v-if="roundSummary.dealer_side === 'north_south' && roundSummary.dealer_level_up > 0" class="text-sm text-slate-400 ml-2">(升{{ roundSummary.dealer_level_up }}级)</span>
            <span v-if="roundSummary.idle_side === 'north_south' && roundSummary.idle_level_up > 0" class="text-sm text-slate-400 ml-2">(升{{ roundSummary.idle_level_up }}级)</span>
          </span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-slate-300">东西家级别：</span>
          <span class="text-lg font-semibold">
            {{ getLevelLabel(roundSummary.old_east_west_level) }} → {{ getLevelLabel(roundSummary.new_east_west_level) }}
            <span v-if="roundSummary.dealer_side === 'east_west' && roundSummary.dealer_level_up > 0" class="text-sm text-slate-400 ml-2">(升{{ roundSummary.dealer_level_up }}级)</span>
            <span v-if="roundSummary.idle_side === 'east_west' && roundSummary.idle_level_up > 0" class="text-sm text-slate-400 ml-2">(升{{ roundSummary.idle_level_up }}级)</span>
          </span>
        </div>
      </div>
      
      <!-- 下一轮庄家 -->
      <div class="flex justify-between items-center border-t border-slate-700 pt-2">
        <span class="text-slate-300">下一轮庄家：</span>
        <span class="text-lg font-semibold">{{ roundSummary.next_dealer_name || getPositionLabel(roundSummary.next_dealer) }}</span>
      </div>
    </div>
    
    <!-- 打A计数信息 -->
    <div v-if="shouldShowAceCount && roundSummary" class="border-t border-slate-700 pt-4 mt-4">
      <div class="text-sm text-slate-400 mb-2">打A计数：</div>
      <!-- 南北方打A计数 -->
      <div v-if="shouldShowNorthSouthAceCount" class="mb-2">
        <div class="text-slate-300">
          南北方打A计数：{{ roundSummary.north_south_ace_count ?? 0 }}
          <span v-if="roundSummary.dealer_is_playing_ace === true && roundSummary.dealer_side === 'north_south' && !roundSummary.dealer_wins && roundSummary.north_south_ace_count_before !== undefined && roundSummary.north_south_ace_count_before >= 0" class="text-slate-400">
            （{{ roundSummary.north_south_ace_count_before }}+1）
          </span>
        </div>
        <div v-if="roundSummary.dealer_side === 'north_south' && roundSummary.dealer_penalty" class="text-amber-300 text-sm mt-1">
          南北方级别从2重新开始，打A计数清零
        </div>
      </div>
      <!-- 东西方打A计数 -->
      <div v-if="shouldShowEastWestAceCount" class="mb-2">
        <div class="text-slate-300">
          东西方打A计数：{{ roundSummary.east_west_ace_count ?? 0 }}
          <span v-if="roundSummary.dealer_is_playing_ace === true && roundSummary.dealer_side === 'east_west' && !roundSummary.dealer_wins && roundSummary.east_west_ace_count_before !== undefined && roundSummary.east_west_ace_count_before >= 0" class="text-slate-400">
            （{{ roundSummary.east_west_ace_count_before }}+1）
          </span>
        </div>
        <div v-if="roundSummary.dealer_side === 'east_west' && roundSummary.dealer_penalty" class="text-amber-300 text-sm mt-1">
          东西方级别从2重新开始，打A计数清零
        </div>
      </div>
    </div>
    
    <!-- 底部按钮 -->
    <div class="flex gap-2 justify-center border-t border-slate-700 pt-4">
      <button
        @click="emit('open-bottom-cards')"
        class="px-4 py-2 rounded bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold"
      >
        查看底牌
      </button>
      <button
        @click="emit('update:show', false)"
        class="px-4 py-2 rounded bg-slate-600 hover:bg-slate-500 text-white text-sm font-semibold"
      >
        隐藏总结
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface RoundSummary {
  idle_score: number
  bottom_score: number
  bottom_bonus: number
  total_score: number
  dealer_side: 'north_south' | 'east_west'
  idle_side: 'north_south' | 'east_west'
  dealer_level_up: number
  idle_level_up: number
  old_north_south_level: number
  old_east_west_level: number
  new_north_south_level: number
  new_east_west_level: number
  next_dealer: string
  next_dealer_name?: string
  bottom_cards?: string[]
  tricks_won?: {
    north_south: number
    east_west: number
  }
  dealer_wins: boolean
  winner_side?: string | null
  winner_side_name?: string | null
  dealer_penalty: boolean
  north_south_ace_count: number
  east_west_ace_count: number
  north_south_ace_count_before?: number
  east_west_ace_count_before?: number
  dealer_is_playing_ace: boolean
}

interface Props {
  roundSummary: RoundSummary | null
  show: boolean
  shouldShowAceCount: boolean
  shouldShowNorthSouthAceCount: boolean
  shouldShowEastWestAceCount: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'open-bottom-cards': []
}>()

// 获取级别标签
function getLevelLabel(level: number): string {
  const levelMap: Record<number, string> = {
    2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
    11: 'J', 12: 'Q', 13: 'K', 14: 'A'
  }
  return levelMap[level] || String(level)
}

// 获取位置标签
function getPositionLabel(position: string): string {
  const positionMap: Record<string, string> = {
    'NORTH': '北',
    'SOUTH': '南',
    'EAST': '东',
    'WEST': '西'
  }
  return positionMap[position.toUpperCase()] || position
}
</script>

