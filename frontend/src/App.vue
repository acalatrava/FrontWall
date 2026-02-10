<template>
  <div class="min-h-screen bg-gray-950">
    <template v-if="isPublicRoute">
      <router-view />
    </template>
    <template v-else>
      <div class="flex h-screen">
        <Sidebar />
        <main class="flex-1 overflow-y-auto p-6">
          <router-view />
        </main>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'

const route = useRoute()
const isPublicRoute = computed(() => route.meta.public)
</script>
