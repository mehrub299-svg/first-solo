import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Needed for Docker
    allowedHosts: ['fast-solo-web.onrender.com']
  },
  preview: {
    host: true, // Needed for Docker
    allowedHosts: ['fast-solo-web.onrender.com']
  }
})
