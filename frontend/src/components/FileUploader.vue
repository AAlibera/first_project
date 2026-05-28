<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload, X, FileImage, AlertTriangle } from 'lucide-vue-next'

interface Props {
  multiple?: boolean
  accept?: string
  maxFiles?: number
  maxSize?: number // in MB
  label?: string
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  accept: 'image/*',
  maxFiles: 10,
  maxSize: 50, // 50MB default
  label: '上传文件',
  hint: '支持拖拽或点击上传'
})

const emit = defineEmits<{
  files: [files: File[]]
  clear: []
}>()

const selectedFiles = ref<File[]>([])
const isDragging = ref(false)
const errorMessage = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

const fileCount = computed(() => selectedFiles.value.length)
const totalSize = computed(() => selectedFiles.value.reduce((sum, f) => sum + f.size, 0) / (1024 * 1024))

const validateFiles = (files: File[]): boolean => {
  errorMessage.value = ''

  if (files.length === 0) {
    return false
  }

  const totalFiles = props.multiple ? files.length : Math.min(1, files.length)
  if (totalFiles > props.maxFiles) {
    errorMessage.value = `最多只能上传 ${props.maxFiles} 个文件`
    return false
  }

  const totalSize = files.reduce((sum, f) => sum + f.size, 0) / (1024 * 1024)
  if (totalSize > props.maxSize) {
    errorMessage.value = `文件总大小不能超过 ${props.maxSize}MB`
    return false
  }

  const invalidFiles = files.filter(f => !f.type.includes(props.accept.replace('/*', '')))
  if (invalidFiles.length > 0) {
    errorMessage.value = '请上传有效的文件类型'
    return false
  }

  return true
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  processFiles(files)
}

const processFiles = (files: File[]) => {
  if (validateFiles(files)) {
    selectedFiles.value = props.multiple ? files : [files[0]]
    emit('files', selectedFiles.value)
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  processFiles(files)
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
  if (selectedFiles.value.length === 0) {
    emit('clear')
  }
}

const clearAll = () => {
  selectedFiles.value = []
  errorMessage.value = ''
  emit('clear')
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}
</script>

<template>
  <div class="space-y-4">
    <div
      class="border-2 border-dashed border-slate-600 rounded-xl p-6 text-center transition-all duration-300 cursor-pointer"
      :class="isDragging ? 'border-emerald-500 bg-emerald-500/10' : 'hover:border-emerald-500 hover:bg-slate-700/30'"
      @click="triggerFileInput"
      @drop="handleDrop"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
    >
      <input
        ref="fileInputRef"
        type="file"
        :multiple="multiple"
        :accept="accept"
        class="hidden"
        @change="handleFileSelect"
      />
      <div class="w-16 h-16 mx-auto mb-4 bg-slate-700/50 rounded-xl flex items-center justify-center">
        <Upload class="w-8 h-8 text-emerald-400" />
      </div>
      <p class="text-white font-medium mb-1">{{ label }}</p>
      <p class="text-slate-400 text-sm">{{ hint }}</p>
      <p class="text-xs text-slate-500 mt-2">
        最多 {{ maxFiles }} 个文件，单个不超过 {{ maxSize }}MB
      </p>
    </div>

    <div v-if="errorMessage" class="p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 flex items-center space-x-2">
      <AlertTriangle class="w-5 h-5" />
      <span>{{ errorMessage }}</span>
    </div>

    <div v-if="fileCount > 0" class="space-y-2">
      <div class="flex items-center justify-between text-sm">
        <span class="text-slate-400">已选择 {{ fileCount }} 个文件 ({{ totalSize.toFixed(2) }}MB)</span>
        <button @click="clearAll" class="text-red-400 hover:text-red-300 flex items-center space-x-1">
          <X class="w-4 h-4" />
          <span>清空</span>
        </button>
      </div>
      <div class="space-y-2 max-h-64 overflow-y-auto">
        <div
          v-for="(file, index) in selectedFiles"
          :key="index"
          class="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg group"
        >
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-slate-700/50 rounded-lg flex items-center justify-center">
              <FileImage class="w-5 h-5 text-slate-400" />
            </div>
            <div class="min-w-0">
              <p class="text-white text-sm truncate">{{ file.name }}</p>
              <p class="text-slate-400 text-xs">{{ formatFileSize(file.size) }}</p>
            </div>
          </div>
          <button
            @click="removeFile(index)"
            class="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/20 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>