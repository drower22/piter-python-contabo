import * as React from 'react';
import { ChevronDown } from 'lucide-react';

interface MinimalAccordionProps {
  label: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function MinimalAccordion({ label, children, className = '' }: MinimalAccordionProps) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className={className}>
      <button
        className="flex items-center gap-2 text-sm text-gray-700 font-medium hover:bg-gray-50 rounded px-2 py-1 focus:outline-none"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        {label}
        <ChevronDown size={18} className={`transition-transform ${open ? 'rotate-180' : ''} text-gray-400`} />
      </button>
      {open && (
        <div className="pl-7 py-2 animate-fade-in text-xs text-gray-600">
          {children}
        </div>
      )}
    </div>
  );
}
