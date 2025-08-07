import { Command, CommandList, CommandGroup, CommandItem } from "./command";
import { Badge } from "./badge";
import { cn } from "../../../lib/utils";
import { Check, ChevronDown } from "lucide-react";

const BRAND_COLORS = [
  "#4B1F6F", // brand-purple-dark
  "#FFD53D", // brand-yellow-solar
  "#BDA3E1", // brand-purple-light
  "#222222", // brand-black-charcoal
];

interface Option {
  value: string;
  label: string;
}

interface MultiSelectDropdownProps {
  options: Option[];
  selected: string[];
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  maxSelection?: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MultiSelectDropdown({ options, selected, onChange, placeholder = "Selecione...", className, maxSelection, open, onOpenChange }: MultiSelectDropdownProps) {
  


  const selectedOptions = options.filter(opt => selected.includes(opt.value));

  return (
    <div className={cn("relative", className)}>
      <button
        type="button"
        className={cn(
          "w-full min-w-[220px] flex items-center justify-between rounded-md border bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-purple-dark gap-2",
          open && "ring-2 ring-brand-purple-dark"
        )}
        onClick={() => onOpenChange(!open)}
      >
        <div className="flex flex-wrap gap-1 items-center">
          {selectedOptions.length === 0 ? (
            <span className="text-gray-400">{placeholder}</span>
          ) : (
            selectedOptions.map((opt, index) => (
              <Badge 
                key={opt.value} 
                style={{ 
                  backgroundColor: BRAND_COLORS[index % BRAND_COLORS.length],
                  color: '#fff'
                }}
              >
                {opt.label}
              </Badge>
            ))
          )}
        </div>
        <ChevronDown className="w-4 h-4 text-gray-400" />
      </button>
      {open && (
        <div className="absolute z-10 mt-2 w-full bg-white rounded-md shadow-lg border border-gray-200">
          <Command>
            <CommandList>
              <CommandGroup>
                {options.map(opt => (
                  <CommandItem
                    key={opt.value}
                    onSelect={() => {
                      onChange(opt.value);
                      onOpenChange(false);
                    }}
                    disabled={maxSelection ? !selected.includes(opt.value) && selected.length >= maxSelection : false}

                  >
                    <span className="flex items-center gap-2">
                      <span 
                        className="w-2 h-2 rounded-full" 
                        style={{ 
                          backgroundColor: BRAND_COLORS[options.findIndex(o => o.value === opt.value) % BRAND_COLORS.length]
                        }}
                      />
                      {opt.label}
                    </span>
                    {selected.includes(opt.value) && (
                      <Check className="ml-auto h-4 w-4 text-brand-purple-dark" />
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </div>
      )}
    </div>
  );
}
