<script setup lang="ts">
import { ref } from 'vue'
import NavBar from '@/components/NavBar.vue'
import HomeView from '@/views/HomeView.vue'
import SingleDetectionView from '@/views/SingleDetectionView.vue'
import FolderDetectionView from '@/views/FolderDetectionView.vue'
import VideoDetectionView from '@/views/VideoDetectionView.vue'
import CameraDetectionView from '@/views/CameraDetectionView.vue'

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
    <SingleDetectionView
      v-else-if="currentPath === '/single'"
    />
    <FolderDetectionView
      v-else-if="currentPath === '/folder'"
    />
    <VideoDetectionView
      v-else-if="currentPath === '/video'"
    />
    <CameraDetectionView
      v-else-if="currentPath === '/camera'"
    />

    <footer class="bg-slate-800/50 border-t border-slate-700/50 py-8 mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <p class="text-slate-400 text-sm">
          © 2024 PCB缺陷检测系统. All rights reserved.
        </p>
      </div>
    </footer>
  </div>
</template>