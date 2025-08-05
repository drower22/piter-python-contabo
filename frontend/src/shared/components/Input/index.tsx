/**
 * @file src/components/Input/index.tsx
 * @description Componente de input de texto reutilizável e estilizado.
 * Este componente encapsula a estilização padrão para campos de input, garantindo consistência visual em formulários.
 * - `InputHTMLAttributes`: O componente aceita todas as propriedades padrão de um elemento `<input>` do HTML (ex: `type`, `placeholder`, `onChange`).
 * - `className`: Permite a passagem de classes adicionais para customização.
 * Análise: O componente é bem construído, utilizando Tailwind CSS para definir um estilo base claro, incluindo um estado de foco que muda a cor da borda e adiciona um anel de foco, melhorando a acessibilidade e a experiência do usuário.
 */
import type { InputHTMLAttributes } from 'react';

type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...rest }: InputProps) {
  return (
    <input
      className={`
        w-full bg-white border border-gray-300 text-brand-black-charcoal 
        py-3 px-4 rounded-lg focus:outline-none focus:ring-2 
        focus:ring-brand-purple-light focus:border-transparent
        ${className}
      `}
      {...rest}
    />
  );
}
