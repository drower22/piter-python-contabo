/**
 * @file src/components/Card/index.tsx
 * @description Componente de UI reutilizável que renderiza um contêiner no estilo "cartão".
 * Este componente encapsula a estilização padrão para cartões, como fundo branco, bordas arredondadas, sombra e preenchimento.
 * - `children`: O conteúdo a ser exibido dentro do cartão.
 * - `className`: Permite que classes CSS adicionais sejam passadas para customização.
 * Análise: É um componente simples e eficaz que promove a consistência visual e a reutilização de código. As classes do Tailwind (`bg-white`, `rounded-xl`, `shadow-md`, `p-6`) definem claramente sua aparência.
 */
import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-xl shadow-md p-6 ${className}`}>
      {children}
    </div>
  );
}
