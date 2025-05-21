<template>
  <div class="app-container" :data-theme="theme">
    <!-- Шапка приложения -->
    <header class="main-header">
      <div class="header-brand">
        <img 
          src="./assets/images/logo.jpg"
          class="logo" 
          alt="Логотип"
          width="40"
          height="40"
        >
        <h1 class="app-title">Текстовый менеджер</h1>
      </div>
      
      <div class="header-controls">
        <button 
          class="theme-btn"
          @click="toggleTheme"
          :title="`${isDark ? 'Светлая' : 'Тёмная'} тема`"
        >
          <i :class="themeIcon"></i>
        </button>
      </div>
    </header>

    <!-- Основной контент -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Модальное окно истории -->
    <HistoryModal ref="historyModal"/>
  </div>
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import HistoryModal from './components/HistoryModal.vue'

// Логика темы
const isDark = ref(false)
const theme = computed(() => isDark.value ? 'dark' : 'light')
const themeIcon = computed(() => 
  isDark.value ? 'fas fa-sun' : 'fas fa-moon'
)

// Переключение темы
const toggleTheme = () => {
  isDark.value = !isDark.value
  document.body.setAttribute('data-theme', theme.value)
  localStorage.setItem('theme', theme.value)
}

// Восстановление темы из localStorage
const savedTheme = localStorage.getItem('theme') || 'light'
isDark.value = savedTheme === 'dark'
document.body.setAttribute('data-theme', savedTheme)

// Передача темы в дочерние компоненты
provide('appTheme', theme)
</script>

<style>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-header {
  background: var(--color-surface);
  padding: 1rem;
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(10px);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo {
  border-radius: 8px;
  object-fit: cover;
}

.app-title {
  font-size: 1.25rem;
  color: var(--color-text);
  font-weight: 600;
}

.theme-btn {
  background: rgba(var(--color-primary-rgb), 0.1);
  border: 2px solid var(--color-border);
  width: 44px;
  height: 44px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-btn:hover {
  background: rgba(var(--color-primary-rgb), 0.2);
}

.main-content {
  flex: 1;
  padding: 2rem 1rem;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

/* Анимации переходов */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .main-header {
    padding: 0.75rem;
  }
  
  .app-title {
    font-size: 1.1rem;
  }
  
  .theme-btn {
    width: 38px;
    height: 38px;
  }
}

.theme-btn i {
  color: var(--color-text);
  filter: invert(15%);
}

[data-theme="dark"] .theme-btn i {
  filter: invert(85%);
}

[data-theme="dark"] .theme-btn:hover {
  background: rgba(255,255,255,0.1);
}
</style>