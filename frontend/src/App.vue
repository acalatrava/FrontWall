<template>
  <div class="min-h-screen bg-gray-950">
    <template v-if="isPublicRoute">
      <router-view />
    </template>
    <template v-else>
      <!-- Mobile top bar -->
      <div class="md:hidden fixed top-0 inset-x-0 z-40 bg-gray-900/95 backdrop-blur-lg border-b border-gray-800 px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <svg class="w-7 h-7 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="m9 12 2 2 4-4" stroke="#22c55e"/>
          </svg>
          <span class="text-base font-bold text-white">FrontWall</span>
        </div>
        <button @click="sidebarOpen = !sidebarOpen" class="p-2 text-gray-400 hover:text-white rounded-lg transition-colors">
          <svg v-if="!sidebarOpen" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
          <svg v-else class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <!-- Overlay -->
      <div v-if="sidebarOpen" class="md:hidden fixed inset-0 z-40 bg-black/50" @click="sidebarOpen = false"></div>

      <div class="flex h-screen">
        <Sidebar
          :mobile-open="sidebarOpen"
          @close="sidebarOpen = false"
        />
        <main class="flex-1 overflow-y-auto p-4 pt-18 md:p-6 md:pt-6">
          <router-view />
        </main>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'

const route = useRoute()
const isPublicRoute = computed(() => route.meta.public)
const sidebarOpen = ref(false)

watch(() => route.path, () => { sidebarOpen.value = false })
</script>
