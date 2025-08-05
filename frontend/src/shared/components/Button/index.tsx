/**
 * @file src/components/Button/index.tsx
 * @description Componente de botão reutilizável e estilizado.
 * Este componente encapsula a estilização padrão para botões, garantindo consistência visual em toda a aplicação.
 * - `ButtonHTMLAttributes`: O componente aceita todas as propriedades padrão de um elemento `<button>` do HTML (ex: `type`, `onClick`, `disabled`).
 * - `className`: Permite a passagem de classes adicionais para customização.
 * Análise: O componente é bem construído, utilizando Tailwind CSS para definir um estilo base rico, incluindo estados de hover, focus e disabled. O uso do `...rest` para passar atributos é uma ótima prática que torna o componente flexível.
 */
import type { ButtonHTMLAttributes } from 'react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({ children, className, ...rest }: ButtonProps) {
  return (
    <button
      className={`
        w-full bg-brand-purple-dark text-white font-semibold py-3 px-4 rounded-lg 
        hover:bg-opacity-90 transition-colors focus:outline-none focus:ring-2 
        focus:ring-brand-purple-light focus:ring-opacity-50 disabled:opacity-50 
        disabled:cursor-not-allowed
        ${className}
      `}
      {...rest}
    >
      {children}
    </button>
  );
}
