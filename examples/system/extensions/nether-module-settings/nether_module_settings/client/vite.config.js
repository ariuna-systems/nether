import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    outDir: 'dist',
    lib: {
      entry: 'src/components/settings-component.js',
      name: 'SettingsComponent',
      fileName: 'settings-component',
      formats: ['es']
    },
    rollupOptions: {
      output: {
        entryFileNames: 'settings-component.js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  },
  server: {
    port: 3000,
    host: true
  }
})
