import type { RouteRecordRaw } from 'vue-router'
import TableHome from '@/features/table/TableHome.vue'
import DealingDemo from '@/features/dealing/DealingDemo.vue'
import GameTable from '@/features/table/GameTable.vue'
import RoomList from '@/features/room/RoomList.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/rooms' }, // 默认进入房间列表
  { path: '/dealing', component: DealingDemo },
  { path: '/rooms', component: RoomList },
  { path: '/game/:roomId', component: GameTable },
  { path: '/game', component: GameTable }, // 兼容旧路由
  { path: '/home', component: TableHome }, // 保留一个调试入口（开发者用）
]

export default routes

