<template>
  <div class="file-preview">
    <img v-if="isImage" :src="previewUrl" class="preview-image">
    <video v-else-if="isVideo" controls width="200">
      <source :src="fileUrl" :type="mimeType">
    </video>
    <div v-else class="file-icon">
      {{ fileExtension }}
    </div>
  </div>
</template>

<script>
export default {
  props: ['file'],
  computed: {
    isImage() {
      return ['jpg', 'jpeg', 'png'].includes(this.file.extension)
    },
    previewUrl() {
      return `/uploads/thumb_${this.file.name}`
    }
  }
}
</script>

<style>
.preview-image {
  max-width: 200px;
  max-height: 200px;
  object-fit: contain;
}
</style>