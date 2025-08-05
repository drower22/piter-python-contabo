/**
 * @file postcss.config.js
 * @description Arquivo de configuração para o PostCSS.
 * Define os plugins que serão usados para processar o CSS.
 * - `tailwindcss`: Processa as diretivas do Tailwind (@tailwind) e aplica as classes de utilitário.
 * - `autoprefixer`: Adiciona prefixos de fornecedores (ex: -webkit-, -moz-) para garantir compatibilidade com navegadores mais antigos.
 * Esta é a configuração padrão e recomendada para usar o Tailwind CSS v3 com o Vite.
 */
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
