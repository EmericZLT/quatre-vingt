import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import routes from './routes'
import './styles/tailwind.css'

// 设置浏览器标题（确保覆盖缓存）
document.title = '八十分（升级） | Quatre-Vingt'

const app = createApp(App)
const pinia = createPinia()
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 确保预览模式下访问根路径直接进入房间列表
router.beforeEach((to, _from, next) => {
  if (to.path === '/') return next('/rooms')
  next()
})

app.use(pinia)

// 恢复房间上下文（断线重连）— 必须在安装 pinia 之后执行
import { useRoomStore } from './stores/room'
const preload = () => {
  const store = useRoomStore()
  store.loadFromStorage()
}
preload()

app.use(router)
app.mount('#app')

