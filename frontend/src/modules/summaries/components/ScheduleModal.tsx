import { Button } from '@/shared/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select"
import { useState } from 'react';

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSchedule: (day: string, time: string) => void;
}

const weekdays = [
  { value: 'segunda', label: 'Segunda-feira' },
  { value: 'terca', label: 'Terça-feira' },
  { value: 'quarta', label: 'Quarta-feira' },
  { value: 'quinta', label: 'Quinta-feira' },
  { value: 'sexta', label: 'Sexta-feira' },
  { value: 'sabado', label: 'Sábado' },
  { value: 'domingo', label: 'Domingo' },
];

const generateTimeIntervals = () => {
  const intervals = [];
  for (let h = 0; h < 24; h++) {
    for (let m = 0; m < 60; m += 30) {
      const start = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
      const endM = (m + 29) % 60;
      const endH = h + Math.floor((m + 29) / 60);
      const end = `${String(endH % 24).padStart(2, '0')}:${String(endM).padStart(2, '0')}`;
      intervals.push({ value: `${start}-${end}`, label: `${start} - ${end}` });
    }
  }
  return intervals;
};

const timeIntervals = generateTimeIntervals();

export function ScheduleModal({ isOpen, onClose, onSchedule }: ScheduleModalProps) {
  const [selectedDay, setSelectedDay] = useState<string>('');
  const [selectedTime, setSelectedTime] = useState<string>('');

  if (!isOpen) {
    return null;
  }

  const handleSchedule = () => {
    if (selectedDay && selectedTime) {
      onSchedule(selectedDay, selectedTime);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md transform transition-all">
        <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold font-sora text-brand-black-charcoal">Agendar Envio</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dia da Semana</label>
            <Select onValueChange={setSelectedDay} value={selectedDay}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione um dia" />
              </SelectTrigger>
              <SelectContent>
                {weekdays.map(day => (
                  <SelectItem key={day.value} value={day.value}>{day.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Horário</label>
            <Select onValueChange={setSelectedTime} value={selectedTime}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione um intervalo" />
              </SelectTrigger>
              <SelectContent>
                {timeIntervals.map(time => (
                  <SelectItem key={time.value} value={time.value}>{time.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handleSchedule} disabled={!selectedDay || !selectedTime}>
            Confirmar Agendamento
          </Button>
        </div>
      </div>
    </div>
  );
}
