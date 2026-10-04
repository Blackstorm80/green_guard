import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { readFileSync } from 'node:fs'

const { version } = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf-8'))

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), react()],
  // Version affichée dans l'application (Paramètres), lue dans package.json au build
  define: { __APP_VERSION__: JSON.stringify(version) },
})
