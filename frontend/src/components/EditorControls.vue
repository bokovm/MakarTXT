<!-- Компонент панели управления редактором -->
<template>
  <div class="editor-controls">
    <button 
      class="btn btn-primary"
      aria-label="Сохранить текст"
      @click="saveText"
    >
      <svg-icon name="save" />
      <span>Сохранить</span>
    </button>
  </div>
</template>