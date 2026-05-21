<script setup lang="ts">
import { ref } from 'vue'
import NavBar from '@/components/NavBar.vue'
import HomeView from '@/views/HomeView.vue'
import DetectionView from '@/views/DetectionView.vue'
import HistoryView from '@/views/HistoryView.vue'
import ModelView from '@/views/ModelView.vue'

const currentPath = ref('/')

const handleNavigate = (path: string) => {
  currentPath.value = path
}
</script>

<template>
  <div class="min-h-screen">
    <NavBar @navigate="handleNavigate" />
    
    <HomeView
      v-if="currentPath === '/'"
      @navigate="handleNavigate"
    />
    <DetectionView
      v-else-if="currentPath === '/detection'"
    />
    <HistoryView
      v-else-if="currentPath === '/history'"
    />
    <ModelView
      v-else-if="currentPath === '/model'"
    />
    
    <footer class="bg-slate-800/50 border-t border-slate-700/50 py-8 mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <p class="text-slate-400 text-sm">
          © 2024 RSOD Detection Platform. All rights reserved.
        </p>
      </div>
    </footer>
  </div>
</template>
