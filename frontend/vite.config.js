import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, 
    allowedHosts: ['fast-solo-web.onrender.com']
  },
  preview: {
    host: true,
    allowedHosts: ['fast-solo-web.onrender.com']
  }
})