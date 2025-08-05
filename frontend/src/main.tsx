/**
 * @file main.tsx
 * @description Ponto de entrada principal da aplicação React.
 * Este arquivo é responsável por inicializar a aplicação.
 * - `import './index.css'`: Linha CRÍTICA que importa todos os estilos globais e as diretivas do Tailwind CSS.
 * - `createRoot`: Cria a raiz da aplicação React, ligando-a ao elemento `<div id="root">` no `index.html`.
 * - `<App />`: O componente principal que encapsula toda a aplicação.
 * Análise: O arquivo está configurado corretamente. A importação do `index.css` está presente, o que é um ponto de verificação crucial.
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
