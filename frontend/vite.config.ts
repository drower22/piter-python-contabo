/**
 * @file vite.config.ts
 * @description Arquivo de configuração para o Vite.
 * Define as configurações do servidor de desenvolvimento e do processo de build da aplicação.
 * - `@vitejs/plugin-react`: Essencial para habilitar o suporte ao React, incluindo Fast Refresh.
 * Análise: A configuração foi revertida para o padrão. O Vite detectará e usará automaticamente o `postcss.config.js` para o processamento do Tailwind CSS v3.
 */
import { fileURLToPath } from 'url';
import path from 'path';
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(path.dirname(fileURLToPath(import.meta.url)), "./src"),
    },
  },
})
