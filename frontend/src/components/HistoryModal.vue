<template>
  <div id="history-modal" class="modal" :class="{ hidden: !isOpen }">
    <div class="modal-backdrop" @click="close"></div>
    
    <div class="modal-content">
      <div class="modal-header">
        <h2>История записей</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>

      <div class="history-list">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <span>Загрузка истории...</span>
        </div>
        
        <div v-else-if="!records.length" class="empty-state">
          <i class="fas fa-history"></i>
          <p>Нет сохраненных записей</p>
        </div>

        <div 
          v-else
          v-for="record in records"
          :key="record.id"
          class="history-item"
        >
          <div class="file-header">
            <div class="file-meta">
              <i class="fas fa-file-alt"></i>
              <div>
                <span class="filename">{{ record.filename }}</span>
                <span class="file-date">{{ formatDate(record.created_at) }}</span>
              </div>
            </div>
            <div class="item-actions">
              <button 
                class="action-btn copy-btn" 
                @click="copyText(record.content)"
                title="Копировать текст"
              >
                <i class="fas fa-copy"></i>
              </button>
              <button 
                class="action-btn download-btn"
                @click="downloadFile(record.filename)"
                title="Скачать файл"
              >
                <i class="fas fa-download"></i>
              </button>
            </div>
          </div>
          <pre class="item-text">{{ record.content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { 
  fetchGet, 
  copyToClipboard,
  showToast,
  showError,
  formatDate
} from '@js/core/utils.js';

const isOpen = ref(false);
const records = ref([]);
const loading = ref(false);
const theme = computed(() => 
  document.body.getAttribute('data-theme') || 'light'
);

const load = async () => {
  try {
    loading.value = true;
    const response = await fetchGet('/api/history');
    
    if (response?.error) throw new Error(response.error);
    
    records.value = Array.isArray(response) 
      ? response 
      : [];
  } catch (error) {
    showError('Ошибка загрузки: ' + error.message);
  } finally {
    loading.value = false;
  }
};

const open = async () => {
  document.body.classList.add('modal-open');
  document.documentElement.style.overflow = 'hidden';
  isOpen.value = true;
  await load();
};

const close = () => {
  document.body.classList.remove('modal-open');
  document.documentElement.style.overflow = '';
  isOpen.value = false;
};

const copyText = (text) => {
  copyToClipboard(text)
    .then(() => showToast('Текст скопирован!'))
    .catch(() => showError('Ошибка копирования'));
};

const downloadFile = (filename) => {
  try {
    const link = document.createElement('a');
    link.href = `/api/files/download/${encodeURIComponent(filename)}`;
    link.target = '_blank';
    link.click();
  } catch (error) {
    showError('Ошибка скачивания: ' + error.message);
  }
};

defineExpose({ open, close });
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}

.modal:not(.hidden) {
  opacity: 1;
  visibility: visible;
}

.modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  background: var(--color-surface);
  border-radius: 12px;
  width: 95%;
  max-width: 600px;
  max-height: 90vh;
  transform: translateY(20px);
  transition: transform 0.3s ease;
}

.modal:not(.hidden) .modal-content {
  transform: translateY(0);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  font-size: 1.25rem;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text);
  cursor: pointer;
  padding: 0.25rem;
  transition: opacity 0.2s;
}

.close-btn:hover {
  opacity: 0.8;
}

.history-list {
  padding: 1rem;
  max-height: 60vh;
  overflow-y: auto;
}

.history-list::-webkit-scrollbar {
  width: 6px;
}

.history-list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.history-item {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 0.75rem;
  transition: all 0.2s;
}

.history-item:hover {
  transform: translateX(2px);
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  gap: 1rem;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-grow: 1;
}

.file-meta i {
  color: var(--color-primary);
  font-size: 1.25rem;
}

.filename {
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-date {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-top: 0.25rem;
}

.item-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: var(--color-primary);
  color: white;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: opacity 0.2s;
}

.action-btn:hover {
  opacity: 0.9;
}

.item-text {
  padding: 1rem;
  margin: 0;
  background: rgba(0,0,0,0.03);
  border-radius: 0 0 8px 8px;
  font-family: 'Fira Code', monospace;
  font-size: 0.875rem;
  max-height: 150px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  gap: 1rem;
  color: var(--color-text-secondary);
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-secondary);
}

.empty-state i {
  font-size: 2rem;
  margin-bottom: 1rem;
  opacity: 0.6;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(0,0,0,0.1);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@media (max-width: 600px) {
  .modal-content {
    width: 95%;
  }
  
  .file-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .item-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>