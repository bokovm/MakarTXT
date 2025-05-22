import { createApp } from 'vue'
import App from '@/App.vue' 
import router from './router'
import { initTheme } from '@/assets/js/core/theme.js'
import { setupSocket } from '@/assets/js/core/socket.js'
import { showToast, showError } from '@/assets/js/core/utils.js'
const app = createApp(App)

// Инициализация плагинов
app.use(router)

// Глобальные свойства
app.config.globalProperties.$showToast = showToast
app.config.globalProperties.$showError = showError

// Инициализация темы
app.mixin({
  mounted() {
    initTheme()
  }
})

// Инициализация WebSocket
setupSocket(app)

app.mount('#app')