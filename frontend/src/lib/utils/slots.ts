// Slot Utilities
import type { ConsultationType } from '../api-doctor';

export interface SlotSuggestion {
  schedule_entry_id: number;
  start: Date;
  end: Date;
  consultation_type: ConsultationType;
  location?: string;
}

export interface SlotSuggestionGroup {
  date: Date;
  dateLabel: string;
  slots: SlotSuggestion[];
}

export const generateSlotSuggestions = (
  scheduleEntries: any[],
  startDate: Date,
  endDate: Date
): SlotSuggestion[] => {
  // Simple implementation - returns empty for now
  return [];
};

export const groupSlotsByDay = (slots: SlotSuggestion[]): SlotSuggestionGroup[] => {
  const groups: Map<string, SlotSuggestionGroup> = new Map();
  
  slots.forEach(slot => {
    const dateKey = slot.start.toISOString().split('T')[0];
    if (!groups.has(dateKey)) {
      groups.set(dateKey, {
        date: new Date(slot.start),
        dateLabel: slot.start.toLocaleDateString('fr-FR', {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
        }),
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
  return slotDateStr === selectedDate && slot.schedule_entry_id === selectedEntryId;
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
