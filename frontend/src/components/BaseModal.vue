<!-- Базовый компонент модального окна -->
<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    close() {
      this.$emit('close');
    }
  }
}
</script>