import { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
  noBorder?: boolean;
}

export default function Select({ value, onChange, options, placeholder = 'Выберите...', className = '', noBorder = false }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selectRef = useRef<HTMLDivElement>(null);
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 });

  const selectedOption = options.find(opt => opt.value === value);

  const updatePosition = useCallback(() => {
    if (selectRef.current && isOpen) {
      const rect = selectRef.current.getBoundingClientRect();
      setDropdownPos({
        top: rect.bottom + 4,
        left: rect.left,
        width: rect.width,
      });
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        // Also check if clicking on the portal dropdown
        const target = event.target as HTMLElement;
        if (target.closest?.('[data-select-dropdown]')) return;
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Recalculate position on open and scroll/resize
  useEffect(() => {
    if (isOpen) {
      updatePosition();
      window.addEventListener('scroll', updatePosition, true);
      window.addEventListener('resize', updatePosition);
      return () => {
        window.removeEventListener('scroll', updatePosition, true);
        window.removeEventListener('resize', updatePosition);
      };
    }
  }, [isOpen, updatePosition]);

  return (
    <div ref={selectRef} className={`relative ${className}`}>
      <motion.button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        style={noBorder ? undefined : { background: 'var(--card)', borderColor: 'var(--card-border)' }}
        className={`w-full px-4 py-2.5 text-sm font-medium text-left
                 focus:outline-none
                 transition-all duration-200 ease-in-out
                 flex items-center justify-between gap-2
                 ${noBorder
                   ? 'bg-transparent rounded-none'
                   : 'rounded-xl border backdrop-blur-xl shadow-lg'
                 }`}
        onMouseEnter={(e) => {
          if (!noBorder) (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)';
        }}
        onMouseLeave={(e) => {
          if (!noBorder) (e.currentTarget as HTMLElement).style.borderColor = 'var(--card-border)';
        }}
        onFocus={(e) => {
          if (!noBorder) {
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)';
            (e.currentTarget as HTMLElement).style.boxShadow = '0 0 0 2px rgba(37, 99, 235, 0.2)';
          }
        }}
        onBlur={(e) => {
          if (!noBorder) {
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--card-border)';
            (e.currentTarget as HTMLElement).style.boxShadow = '';
          }
        }}
      >
        <span className="truncate" style={{ color: 'var(--text)' }}>{selectedOption?.label || placeholder}</span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2, ease: 'easeInOut' }}
          className="flex-shrink-0"
        >
          <ChevronDown className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
        </motion.div>
      </motion.button>

      {/* Portal-based dropdown to avoid z-index/overflow issues */}
      {isOpen && createPortal(
        <AnimatePresence>
          <motion.div
            data-select-dropdown
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{
              position: 'fixed',
              top: dropdownPos.top,
              left: dropdownPos.left,
              width: Math.max(dropdownPos.width, 180),
              zIndex: 99999,
              background: 'var(--card)',
              borderColor: 'var(--card-border)',
            }}
            className="rounded-xl backdrop-blur-xl shadow-2xl border overflow-hidden"
          >
            <div className="py-1">
              {options.map((option, index) => (
                <motion.button
                  key={option.value}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03, duration: 0.15 }}
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                  }}
                  whileHover={{ backgroundColor: 'rgba(37, 99, 235, 0.1)' }}
                  style={
                    value === option.value
                      ? { background: 'var(--accent-subtle)', color: 'var(--accent)' }
                      : { color: 'var(--text)' }
                  }
                  className={`w-full px-4 py-2.5 text-left text-sm transition-all duration-150
                    ${value === option.value ? 'font-medium' : ''}`}
                >
                  <span className="block truncate">{option.label}</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>,
        document.body
      )}
    </div>
  );
}
