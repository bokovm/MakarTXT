<template>
  <div class="main-content">
    <div class="content-container">
      <div class="main-grid">
        <!-- Секция текстового редактора -->
        <section class="text-section">
          <textarea 
            v-model="message"
            class="modern-textarea"
            placeholder="Введите текст здесь..."
            rows="6"
            @input="autoResize"
          ></textarea>
          
          <div class="editor-actions">
            <button class="action-btn primary" @click="saveMessage">
              <i class="fas fa-save"></i>
              <span>Сохранить</span>
            </button>
            <button 
              class="action-btn" 
              @click="openModal('history')"
            >
              <i class="fas fa-history"></i>
              <span>История</span>
            </button>
            <button class="action-btn" @click="triggerFileUpload">
              <i class="fas fa-upload"></i>
              <span>Файлы</span>
            </button>
            <input 
              type="file" 
              id="file-input"
              multiple
              style="display: none;"
              @change="handleFileUpload"
            >
          </div>
        </section>

        <!-- Секция YouTube -->
        <section class="youtube-section">
          <input 
            v-model="youtubeUrl"
            class="yt-input"
            placeholder="Ссылка на YouTube видео"
            @input="handleYoutubeInput"
          >
          
          <div class="yt-preview" v-if="videoThumbnail">
            <img :src="videoThumbnail" class="yt-thumbnail">
            <div class="yt-meta">
              <h3>{{ videoTitle }}</h3>
              <p class="duration">{{ formattedDuration }}</p>
            </div>
            
            <select v-model="selectedFormat" class="yt-format-select">
              <option 
                v-for="format in formats" 
                :value="format.id"
                :key="format.id"
              >
                {{ format.resolution || format.ext.toUpperCase() }}
              </option>
            </select>
          </div>

          <button 
            class="action-btn danger" 
            @click="downloadVideo"
            :disabled="!youtubeUrl || isLoading"
          >
            <i class="fas fa-download"></i>
            <span>{{ isLoading ? 'Загрузка...' : 'Скачать' }}</span>
          </button>
        </section>
      </div>
    </div>

    <HistoryModal ref="historyModal"/>
    <FileManager />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showToast, showError } from '@/assets/js/core/utils.js'
import { Files } from '@/assets/js/modules/chat/files.js'
import HistoryModal from '@/components/HistoryModal.vue'
import FileManager from '@/components/FileManager.vue'

const historyModal = ref(null)

// Состояния
const message = ref('')
const youtubeUrl = ref('')
const videoThumbnail = ref('')
const videoTitle = ref('')
const videoDuration = ref(0)
const formats = ref([])
const selectedFormat = ref('')
const isLoading = ref(false)

// Инициализация модуля файлов
onMounted(() => {
  Files.init()
})

const openModal = (type) => {
  if (type === 'history') historyModal.value?.open()
}

const autoResize = (e) => {
  e.target.style.height = 'auto'
  e.target.style.height = `${e.target.scrollHeight}px`
}

const saveMessage = async () => {
  const text = message.value.trim()
  if (!text) return showError('Введите текст')

  try {
    const response = await fetch('/api/save_text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    showToast('Сохранено!')
    message.value = ''
    historyModal.value?.load()
  } catch (error) {
    showError('Ошибка: ' + error.message)
  }
}

const handleYoutubeInput = async () => {
  if (!youtubeUrl.value) return
  isLoading.value = true
  
  try {
    const response = await fetch(`/api/youtube/info?url=${encodeURIComponent(youtubeUrl.value)}`)
    if (!response.ok) throw new Error('Ошибка запроса')
    
    const data = await response.json()
    videoThumbnail.value = data.thumbnail
    videoTitle.value = data.title
    videoDuration.value = data.duration
    formats.value = data.formats
  } catch (error) {
    showError(error.message)
  } finally {
    isLoading.value = false
  }
}

const downloadVideo = async () => {
  try {
    const response = await fetch('/api/youtube/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: youtubeUrl.value,
        format: selectedFormat.value
      })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${videoTitle.value}.${selectedFormat.value.ext || 'mp4'}`
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    showError('Ошибка: ' + error.message)
  }
}

const handleFileUpload = async (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    try {
      await Promise.all(files.map(file => Files.uploadFile(file)))
      showToast(`Успешно загружено ${files.length} файлов`)
      Files.load() // Обновляем список файлов
    } catch (error) {
      showError('Ошибка загрузки: ' + error.message)
    }
  }
  event.target.value = ''
}

const triggerFileUpload = () => {
  document.getElementById('file-input')?.click()
}

const formattedDuration = computed(() => {
  const sec = videoDuration.value
  const hours = Math.floor(sec / 3600)
  const minutes = Math.floor((sec % 3600) / 60)
  const seconds = sec % 60
  return [hours, minutes, seconds]
    .map(v => v.toString().padStart(2, '0'))
    .join(':')
})
</script>

<style scoped>
/* Стили остаются без изменений */
.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.main-grid {
  display: grid;
  gap: 2rem;
}

.modern-textarea {
  width: 100%;
  min-height: 200px;
  padding: 1rem;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  font-size: 16px;
  background: var(--color-surface);
  color: var(--color-text);
  resize: vertical;
  transition: border-color 0.2s;
}

.modern-textarea:focus {
  border-color: var(--color-primary);
  outline: none;
}

.editor-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.yt-input {
  width: 100%;
  padding: 1rem;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-text);
  margin-bottom: 1rem;
}

.yt-thumbnail {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
  margin-top: 1rem;
}

.yt-format-select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  margin: 1rem 0;
  background: var(--color-surface);
  color: var(--color-text);
}

.action-btn {
  padding: 0.75rem 1.25rem;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-text);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.action-btn.primary {
  background: var(--color-primary);
  color: white;
  border-color: transparent;
}

.action-btn.danger {
  background: var(--color-danger);
  color: white;
  border-color: transparent;
}

@media (max-width: 768px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
  
  .editor-actions {
    flex-direction: column;
  }
  
  .action-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .modern-textarea {
    font-size: 14px;
    padding: 0.875rem;
  }
  
  .yt-thumbnail {
    height: 160px;
  }
}
</style>