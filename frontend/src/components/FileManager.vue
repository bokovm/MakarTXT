<!-- Асинхронная загрузка списка файлов -->
<template>
  <Suspense>
    <template #default>
      <FileList />
    </template>
    <template #fallback>
      <div class="loading-state">
        <div class="spinner"></div>
      </div>
    </template>
  </Suspense>
</template>