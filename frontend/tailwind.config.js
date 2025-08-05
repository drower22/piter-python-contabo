/**
 * @file tailwind.config.js
 * @description Arquivo de configuração para o Tailwind CSS.
 * - `content`: Define quais arquivos serão escaneados pelo Tailwind em busca de classes de utilitários. É crucial que este array inclua todos os arquivos que contêm JSX/HTML.
 * - `theme.extend`: Adiciona nossas cores e fontes personalizadas (design system) ao tema padrão do Tailwind.
 * - `plugins`: Permite adicionar plugins para estender as funcionalidades do Tailwind.
 * Análise: A configuração do `content` parece correta, cobrindo `./index.html` e todos os arquivos relevantes em `src`. O tema customizado está bem definido.
 */
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-purple-dark': '#4B1F6F',
        'brand-yellow-solar': '#FFD53D',
        'brand-purple-light': '#BDA3E1',
        'brand-gray-lilac': '#F4F1FA',
        'brand-black-charcoal': '#222222',
      },
      fontFamily: {
        sora: ['Sora', 'sans-serif'],
        inter: ['Inter', 'sans-serif'],
      },
      keyframes: {
        'fade-in': { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        'fade-in-up': { '0%': { opacity: '0', transform: 'translateY(10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-out',
        'fade-in-up': 'fade-in-up 0.3s ease-out',
      }
    },
  },
  plugins: [],
}
