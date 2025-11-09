import type { RouteRecordRaw } from 'vue-router'
import TableHome from '@/features/table/TableHome.vue'
import DealingDemo from '@/features/dealing/DealingDemo.vue'
import GameTable from '@/features/table/GameTable.vue'
import RoomList from '@/features/room/RoomList.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', component: TableHome },
  { path: '/dealing', component: DealingDemo },
  { path: '/rooms', component: RoomList },
  { path: '/game/:roomId', component: GameTable },
  { path: '/game', component: GameTable }, // 兼容旧路由
]

export default routes

