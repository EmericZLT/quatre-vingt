import { ref, computed, readonly, onMounted, onUnmounted } from 'vue'

export type DeviceType = 'mobile' | 'desktop'

export function useDeviceDetection() {
  const deviceType = ref<DeviceType>('desktop')
  const screenWidth = ref<number>(typeof window !== 'undefined' ? window.innerWidth : 1024)
  
  // 移动端断点：640px
  const MOBILE_BREAKPOINT = 640

  function updateDeviceType() {
    if (typeof window === 'undefined') return
    
    screenWidth.value = window.innerWidth
    deviceType.value = screenWidth.value < MOBILE_BREAKPOINT ? 'mobile' : 'desktop'
  }

  onMounted(() => {
    updateDeviceType()
    window.addEventListener('resize', updateDeviceType)
    // 监听屏幕方向变化（移动端）
    window.addEventListener('orientationchange', updateDeviceType)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateDeviceType)
    window.removeEventListener('orientationchange', updateDeviceType)
  })

  const isMobile = computed(() => deviceType.value === 'mobile')
  const isDesktop = computed(() => deviceType.value === 'desktop')

  return {
    deviceType: readonly(deviceType),
    screenWidth: readonly(screenWidth),
    isMobile,
    isDesktop
  }
}

