// Slot Utilities
import type { ConsultationType, DoctorScheduleEntry } from '../api-doctor';

export interface SlotSuggestion {
  entry: DoctorScheduleEntry;
  start: Date;
  end: Date;
  consultation_type: ConsultationType;
  location?: string;
  is_available?: boolean; // 🆕 Indique si le créneau est disponible ou bloqué
}

export interface SlotSuggestionGroup {
  key: string;
  date: Date;
  dateLabel: string;
  label: string;
  slots: SlotSuggestion[];
}

export const generateSlotSuggestions = (
  scheduleEntries: DoctorScheduleEntry[],
  consultation_type: ConsultationType,
  maxSlots = 20,
  weeks = 4
): SlotSuggestion[] => {
  const suggestions: SlotSuggestion[] = [];
  if (!scheduleEntries || !scheduleEntries.length) return suggestions;

  const now = new Date();
  const parseTime = (timeStr: string) => {
    const [hh, mm] = timeStr.split(':').map(Number);
    return { hh, mm };
  };

  for (const entry of scheduleEntries) {
    if (entry.consultation_type !== 'both' && consultation_type !== 'both' && entry.consultation_type !== consultation_type) {
      continue;
    }

    const { hh: startH, mm: startM } = parseTime(entry.start_time);
    const { hh: endH, mm: endM } = parseTime(entry.end_time);
    const slotDuration = entry.slot_duration || 30;
    const breakDuration = entry.break_duration || 0;

    for (let w = 0; w < weeks; w++) {
      const date = new Date(now);
      date.setHours(0, 0, 0, 0);

      const currentWeekday = date.getDay();
      const daysUntil = ((entry.day_of_week - currentWeekday) + 7) % 7 + (w * 7);
      date.setDate(date.getDate() + daysUntil);

      const baseStart = new Date(date);
      baseStart.setHours(startH, startM, 0, 0);
      const baseEnd = new Date(date);
      baseEnd.setHours(endH, endM, 0, 0);

      let slotStart = new Date(baseStart);
      while (slotStart.getTime() + slotDuration * 60000 <= baseEnd.getTime()) {
        if (slotStart.getTime() > now.getTime()) {
          const slotEnd = new Date(slotStart.getTime() + slotDuration * 60000);
          suggestions.push({
            entry,
            start: new Date(slotStart),
            end: slotEnd,
            consultation_type: entry.consultation_type,
            location: entry.location,
            // 🆕 Propager is_available depuis entry (si défini)
            is_available: (entry as any).is_available !== undefined ? (entry as any).is_available : true
          });
          if (suggestions.length >= maxSlots) return suggestions.sort((a, b) => a.start.getTime() - b.start.getTime());
        }
        slotStart = new Date(slotStart.getTime() + (slotDuration + breakDuration) * 60000);
      }
    }
  }

  return suggestions.sort((a, b) => a.start.getTime() - b.start.getTime()).slice(0, maxSlots);
};

export const groupSlotsByDay = (slots: SlotSuggestion[]): SlotSuggestionGroup[] => {
  const groups: Map<string, SlotSuggestionGroup> = new Map();
  
  slots.forEach(slot => {
    const dateKey = slot.start.toISOString().split('T')[0];
    if (!groups.has(dateKey)) {
      const dateLabel = slot.start.toLocaleDateString('fr-FR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
      });
      groups.set(dateKey, {
        key: dateKey,
        date: new Date(slot.start),
        dateLabel: dateLabel,
        label: dateLabel,
        slots: [],
      });
    }
    groups.get(dateKey)!.slots.push(slot);
  });
  
  return Array.from(groups.values());
};

export const isSlotSelected = (
  slot: SlotSuggestion,
  selectedDate: string,
  selectedEntryId?: number
): boolean => {
  const slotDateStr = slot.start.toISOString();
  return slotDateStr === selectedDate && slot.entry.id === selectedEntryId;
};

export const formatSlotLabel = (slot: SlotSuggestion): string => {
  const startTime = slot.start.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  });
  const endTime = slot.end.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  });
  return `${startTime} - ${endTime}`;
};

export const formatSlotChipLabel = (slot: SlotSuggestion): string => {
  return slot.start.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  });
};