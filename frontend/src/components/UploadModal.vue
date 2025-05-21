<template>
  <div id="upload-modal" class="modal" :class="{ hidden: !isOpen }">
    <!-- Реализация модального окна загрузки -->
  </div>
</template>

<script setup>
import { ref } from 'vue'
const isOpen = ref(false)
// Логика загрузки файлов
</script>