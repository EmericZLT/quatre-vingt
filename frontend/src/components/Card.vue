<template>
  <div
    class="w-12 h-16 rounded-md shadow bg-white text-black flex items-center justify-center border"
    :class="{
      'bg-yellow-100': isTrump,
    }"
  >
    <img v-if="imgSrc" :src="imgSrc" class="w-full h-full object-contain" alt="card"/>
    <span v-else class="text-xs font-semibold">{{ label }}</span>
  </div>
  
</template>

<script setup lang="ts">
interface Props {
  label?: string
  isTrump?: boolean
  imgSrc?: string
}
const props = defineProps<Props>()
</script>

