<template>
  <div class="min-h-screen bg-slate-900 text-slate-100">
    <div class="max-w-6xl mx-auto p-4">
      <header class="py-2">
        <div class="flex items-center justify-between mb-2">
          <h1 class="text-xl font-semibold">八十分（升级） | Quatre-Vingt</h1>
          <nav class="space-x-4 text-slate-300">
          <RouterLink
            v-if="hasActiveRoom"
            :to="`/game/${roomStore.roomId}`"
          >
            牌局界面
          </RouterLink>
          <RouterLink
            v-else
            to="/rooms"
          >
            房间列表
          </RouterLink>
          <RouterLink
            v-if="isDev"
            to="/"
          >
            桌面
          </RouterLink>
          <RouterLink
            v-if="isDev"
            to="/dealing"
          >
            发牌演示
          </RouterLink>
          </nav>
        </div>
        <div class="flex items-center">
          <button
            @click="showRules = true"
            class="px-4 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm transition-colors"
          >
            查看游戏规则
          </button>
        </div>
      </header>
      
      <!-- 游戏规则弹窗 -->
      <div
        v-if="showRules"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="showRules = false"
      >
        <div class="bg-slate-800 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 relative">
          <button
            @click="showRules = false"
            class="absolute top-4 right-4 text-slate-400 hover:text-white text-2xl font-bold"
            aria-label="关闭"
          >
            ×
          </button>
          <h2 class="text-2xl font-bold text-white mb-6">八十分（升级）游戏规则</h2>
          <div class="space-y-4 text-slate-200 text-sm leading-relaxed">
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">一、基本规则</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li>游戏需要<strong class="text-amber-300">4名玩家</strong>，<strong class="text-amber-300">面对面的两人为同一阵营</strong>（南北对家一队，东西对家一队）</li>
                <li>使用<strong class="text-amber-300">两副扑克牌</strong>（共108张，含4张大小王）</li>
                <li>游戏从<strong class="text-amber-300">2</strong>开始，通过升级机制达到<strong class="text-amber-300">A</strong></li>
                <li>每局游戏中，<strong class="text-amber-300">庄家和闲家的身份会发生变化</strong>，不是固定的两个人为庄家方</li>
                <li>每局游戏的目标是<strong class="text-amber-300">庄家方</strong>要防止<strong class="text-amber-300">闲家方</strong>得分，<strong class="text-amber-300">闲家方</strong>要尽量得分</li>
              </ul>
            </div>
            
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">二、发牌与定主</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li>发牌阶段：系统自动发牌，每人<strong class="text-amber-300">25张牌</strong>，剩余<strong class="text-amber-300">8张</strong>作为底牌</li>
                <li>定主阶段：玩家通过<strong class="text-amber-300">亮主</strong>来确定主牌花色</li>
                <li>亮主方式（优先级从低到高）：
                  <ul class="list-circle list-inside ml-4 mt-1 space-y-1">
                    <li><strong class="text-amber-300">单张级牌</strong>：亮出当前级别的单张牌（如当前级别是5，亮出5♠）</li>
                    <li><strong class="text-amber-300">级牌对子</strong>：亮出当前级别的对子（如5♠5♠），优先级高于单张</li>
                    <li><strong class="text-amber-300">双小王</strong>：亮出两张小王，主牌为<strong class="text-amber-300">无主</strong></li>
                    <li><strong class="text-amber-300">双大王</strong>：亮出两张大王，主牌为<strong class="text-amber-300">无主</strong>，优先级最高</li>
                  </ul>
                </li>
                <li>级牌对子的花色大小关系：<strong class="text-amber-300">黑桃(♠) > 红心(♥) > 梅花(♣) > 方块(♦)</strong></li>
                <li>特殊规则：<strong class="text-amber-300">方块对子可以反双大王</strong>（这是特殊逻辑，不按大小判断）</li>
                <li>后亮主可以<strong class="text-amber-300">反主</strong>，但必须使用更高优先级的牌（如单张被对子反，对子被双王反）</li>
                <li>定主后，<strong class="text-amber-300">亮主玩家所在的一方成为庄家方</strong>，另一方为闲家方</li>
              </ul>
            </div>
            
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">三、主牌与副牌</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li><strong class="text-amber-300">主牌</strong>：当前级别的所有花色牌（如级别是5，则5♠、5♥、5♣、5♦都是主牌）</li>
                <li><strong class="text-amber-300">大小王</strong>：无论定什么主，大小王都是主牌，且<strong class="text-amber-300">大王 > 小王</strong></li>
                <li><strong class="text-amber-300">副牌</strong>：非主牌花色的牌</li>
                <li>主牌可以<strong class="text-amber-300">管</strong>（压过）副牌，但必须跟牌型一致（单张对单张，对子对对子等）</li>
              </ul>
            </div>
            
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">四、扣底与翻底</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li>定主后，<strong class="text-amber-300">庄家</strong>需要从手牌中选择<strong class="text-amber-300">8张牌</strong>放回底牌</li>
                <li>扣底完成后，庄家可以查看底牌，然后开始出牌</li>
                <li>如果<strong class="text-amber-300">闲家方在最后一轮获胜</strong>，可以<strong class="text-amber-300">翻底</strong>，根据最后一轮的牌型获得底牌分数×特定倍数</li>
                <li>翻底倍数规则：
                  <ul class="list-circle list-inside ml-4 mt-1 space-y-1">
                    <li><strong class="text-amber-300">单张</strong>：2倍</li>
                    <li><strong class="text-amber-300">对子</strong>：4倍</li>
                    <li><strong class="text-amber-300">连对（拖拉机）</strong>：8倍（每多一对×2，如3对连对为16倍）</li>
                    <li><strong class="text-amber-300">甩牌</strong>：按最大牌型计算倍数</li>
                  </ul>
                </li>
                <li>翻底得分 = 底牌中的分牌分数 × 倍数</li>
              </ul>
            </div>
            
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">五、出牌规则</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li>每轮由一名玩家先出牌，其他玩家按顺序跟牌</li>
                <li><strong class="text-amber-300">必须跟牌型</strong>：如果先出单张，必须跟单张；如果先出对子，必须跟对子</li>
                <li><strong class="text-amber-300">必须跟花色</strong>：如果有先出牌的花色，必须跟该花色；如果没有，可以出其他牌</li>
                <li><strong class="text-amber-300">主牌可以管副牌</strong>：如果没有先出牌的花色，可以用主牌管</li>
                <li>每轮出牌最大的玩家获得该轮的所有牌，并在下一轮先出牌</li>
                <li>支持<strong class="text-amber-300">甩牌</strong>：如果手中有多张相同花色的牌，且分类后每一类（参考下方的牌型与大小）的最小牌都比他人手中该类的最大牌要大，可以一次性打出</li>
                <li>如果甩牌失败（有其他玩家有更大的牌），会被<strong class="text-amber-300">强制打出</strong>其中小于他人的最小牌</li>
              </ul>
            </div>
            
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">六、牌型与大小</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li><strong class="text-amber-300">单张</strong>：一张牌</li>
                <li><strong class="text-amber-300">对子</strong>：两张相同点数的牌（如5♠5♥）</li>
                <li><strong class="text-amber-300">拖拉机</strong>：连续的对子（如5♠5♥ 6♠6♥）</li>
                <li>主牌大小：<strong class="text-amber-300">大王 > 小王 > 主级牌 > 其他主牌</strong></li>
                <li>副牌大小：<strong class="text-amber-300">A > K > Q > J > 10 > 9 > 8 > 7 > 6 > 5 > 4 > 3 > 2</strong></li>
                <li>相同点数时，<strong class="text-amber-300">主牌 > 副牌</strong></li>
              </ul>
            </div>
            
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">七、得分规则</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li><strong class="text-amber-300">分牌</strong>：5、10、K是分牌，分别代表<strong class="text-amber-300">5分、10分、10分</strong></li>
                <li>每轮出牌后，<strong class="text-amber-300">获胜方</strong>获得该轮所有牌中的分牌</li>
                <li>如果闲家方在最后一轮获胜，可以<strong class="text-amber-300">翻底</strong>，根据最后一轮牌型获得底牌分数×特定倍数（详见"扣底与翻底"部分）</li>
              </ul>
            </div>
            
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">八、升级规则</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li><strong class="text-amber-300">两个阵营的级别独立计算</strong>：南北方和东西方各自维护自己的级别</li>
                <li>升级计算前，分数会<strong class="text-amber-300">抹零</strong>（向下取整到10的倍数，如65分视为60分，但75分特殊处理）</li>
                <li>如果闲家得分<strong class="text-amber-300">≥80分</strong>：
                  <ul class="list-circle list-inside ml-4 mt-1 space-y-1">
                    <li>闲家方升级：<strong class="text-amber-300">(得分-80)÷10</strong>级（向下取整）</li>
                    <li>庄家方不升级</li>
                    <li>下一局庄家：<strong class="text-amber-300">本轮庄家的下家</strong>（逆时针）</li>
                  </ul>
                </li>
                <li>如果闲家得分<strong class="text-amber-300">&lt;80分</strong>：
                  <ul class="list-circle list-inside ml-4 mt-1 space-y-1">
                    <li>庄家方升级：<strong class="text-amber-300">(80-得分)÷10</strong>级（向上取整，但75分时庄家不升级）</li>
                    <li>闲家方不升级</li>
                    <li>下一局庄家：<strong class="text-amber-300">本轮庄家的对家</strong>（同一阵营的另一人）</li>
                  </ul>
                </li>
                <li>示例：闲家得90分，闲家方升(90-80)÷10=1级；闲家得60分，庄家方升(80-60)÷10=2级</li>
              </ul>
            </div>
            
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">九、胜负判定</h3>
              <ul class="list-disc list-inside space-y-1 ml-2">
                <li>必须<strong class="text-amber-300">自己方坐庄打A</strong>（级别为A）并<strong class="text-amber-300">获胜</strong>（升级），才算最终胜利</li>
                <li>如果某一方升级到A，但<strong class="text-amber-300">不是自己方坐庄</strong>，则不能判定为最终胜利</li>
                <li>如果某一方坐庄打A，但<strong class="text-amber-300">闲家得分≥80分</strong>（庄家未升级），则不能判定为最终胜利</li>
                <li>只有当<strong class="text-amber-300">自己方坐庄打A且闲家得分&lt;80分</strong>（庄家升级）时，该方才能获得最终胜利</li>
                <li>每一轮的闲家不可能最终胜利，必须自己方坐庄打A并胜利才算是最终胜利</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <main class="py-4">
        <RouterView />
      </main>
    </div>
  </div>
  
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoomStore } from '@/stores/room'

const roomStore = useRoomStore()
const hasActiveRoom = computed(() => !!roomStore.roomId)
const isDev = import.meta.env.MODE === 'development'
const showRules = ref(false)
</script>

<style scoped>
a.router-link-active {
  color: #fff;
}
</style>

