import { useState, useRef, useEffect } from 'react';
import { Check, ChevronDown } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { Badge } from './badge';

const BRAND_COLORS = ['#4B1F6F', '#FFD53D', '#BDA3E1', '#222222'];

interface Option {
  value: string;
  label: string;
}

interface SimpleMultiSelectProps {
  options: Option[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  className?: string;
  maxSelection?: number;
  useSingleColor?: boolean;
}

export function SimpleMultiSelect({ options, selected, onChange, placeholder, className, maxSelection, useSingleColor = false }: SimpleMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleSelect = (value: string) => {
    const isSelected = selected.includes(value);
    if (isSelected) {
      onChange(selected.filter(v => v !== value));
    } else {
      if (!maxSelection || selected.length < maxSelection) {
        onChange([...selected, value]);
      }
    }
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOptions = options.filter(opt => selected.includes(opt.value));

  return (
    <div className={cn("relative", className)} ref={containerRef}>
      <button
        type="button"
        className={cn(
          "w-full min-w-[220px] flex items-center justify-between rounded-md border bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-purple-dark gap-2",
          isOpen && "ring-2 ring-brand-purple-dark"
        )}
        onClick={() => setIsOpen(prev => !prev)}
      >
        <div className="flex flex-wrap gap-1 items-center">
          {selectedOptions.length === 0 ? (
            <span className="text-gray-400">{placeholder}</span>
          ) : (
            selectedOptions.map((opt, index) => (
              <Badge
                key={opt.value}
                style={{
                  backgroundColor: useSingleColor ? '#E9D5FF' : BRAND_COLORS[index % BRAND_COLORS.length],
                  color: useSingleColor ? '#5B21B6' : '#fff',
                }}
              >
                {opt.label}
              </Badge>
            ))
          )}
        </div>
        <ChevronDown className="w-4 h-4 text-gray-400" />
      </button>
      {isOpen && (
        <div className="absolute z-10 mt-2 w-full bg-white rounded-md shadow-lg border border-gray-200 max-h-60 overflow-auto">
          <ul>
            {options.map(opt => {
              const isSelected = selected.includes(opt.value);
              const isDisabled = !isSelected && maxSelection ? selected.length >= maxSelection : false;
              return (
                <li
                  key={opt.value}
                  className={cn(
                    "px-3 py-2 text-sm flex items-center cursor-pointer hover:bg-gray-100",
                    isDisabled && "cursor-not-allowed opacity-50"
                  )}
                  onClick={() => !isDisabled && handleSelect(opt.value)}
                >
                  {opt.label}
                  {isSelected && <Check className="ml-auto h-4 w-4 text-brand-purple-dark" />}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
