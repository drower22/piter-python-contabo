/**
 * @file vite.config.ts
 * @description Arquivo de configuração para o Vite.
 * Define as configurações do servidor de desenvolvimento e do processo de build da aplicação.
 * - `@vitejs/plugin-react`: Essencial para habilitar o suporte ao React, incluindo Fast Refresh.
 * Análise: A configuração foi revertida para o padrão. O Vite detectará e usará automaticamente o `postcss.config.js` para o processamento do Tailwind CSS v3.
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
