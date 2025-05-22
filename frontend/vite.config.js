import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

export default defineConfig({
  plugins: [vue({
    script: {
      defineModel: true,
      propsDestructure: true
    }
  })],
  
  resolve: {
    extensions: ['.js', '.vue', '.json'],
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@js': path.resolve(__dirname, './src/assets/js'),
      '@components': path.resolve(__dirname, './src/components')
    }
  },

  server: {
    host: 'localhost',
    port: 3000,
    strictPort: true,
    open: false,
    
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'ws://localhost:8080',
        ws: true,
        changeOrigin: true
      }
    }
  },

  build: {
    outDir: 'dist',
    assetsInlineLimit: 4096,
    chunkSizeWarningLimit: 1500,
    emptyOutDir: true,
    
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router']
        }
      }
    }
  },

  css: {
    devSourcemap: true,
    preprocessorOptions: {
      scss: {
        additionalData: `@import "@js/core/variables.scss";`
      }
    }
  }
})