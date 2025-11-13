# Teleconsultation UI Preview

## Appointment Card with Meet Link

When a patient views their teleconsultation appointments, they see:

```
┌─────────────────────────────────────────────────────────────────┐
│                                           [✓ Confirmé]          │
│                                                                 │
│   [Dr]  Dr. Marie Dupont                                      │
│         📅 Vendredi, 15 novembre 2025                          │
│         🕐 10:30                                               │
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐   │
│   │  📹 Téléconsultation                                   │   │
│   └───────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐   │
│   │  📹 LIEN DE TÉLÉCONSULTATION                          │   │
│   │                                                         │   │
│   │  ┌────────────────────────────────────────────┐       │   │
│   │  │ ▶ Rejoindre la consultation →              │       │   │
│   │  └────────────────────────────────────────────┘       │   │
│   │                                                         │   │
│   │  Cliquez pour ouvrir la visioconférence               │   │
│   └───────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐   │
│   │  📝 MOTIF                                              │   │
│   │  Consultation de suivi                                │   │
│   └───────────────────────────────────────────────────────┘   │
│                                                                 │
│   [📅 Replanifier]              [✖ Annuler]                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Color Scheme

- **Green Section**: Meet link section uses green gradient (from-green-50 to-emerald-50)
- **Join Button**: Prominent green button (from-green-500 to-emerald-600)
- **Video Icon**: Green video camera icon
- **Hover Effect**: Button scales up (1.05x) on hover with shadow enhancement

## Comparison: In-Person vs Teleconsultation

### In-Person Appointment
```
┌─────────────────────────────────────────┐
│  📅 Mercredi, 20 novembre 2025         │
│  🕐 14:00                              │
│  🏥 En présentiel                      │
│  📝 Consultation générale              │
│                                         │
│  [📅 Replanifier]  [✖ Annuler]        │
└─────────────────────────────────────────┘
```

### Teleconsultation Appointment (with Meet Link)
```
┌─────────────────────────────────────────┐
│  📅 Vendredi, 15 novembre 2025         │
│  🕐 10:30                              │
│  📹 Téléconsultation                   │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │ 📹 Lien de téléconsultation     │  │
│  │ [▶ Rejoindre la consultation]   │  │
│  └─────────────────────────────────┘  │
│                                         │
│  📝 Consultation de suivi              │
│                                         │
│  [📅 Replanifier]  [✖ Annuler]        │
└─────────────────────────────────────────┘
```

## User Flow

1. **Patient Creates Appointment**
   - Selects "Téléconsultation" as consultation type
   - System generates unique Jitsi Meet link
   - Link stored in database

2. **Patient Views Appointments**
   - Green section appears for teleconsultation
   - "Join Meeting" button visible
   - Clear visual distinction from in-person appointments

3. **Patient Joins Consultation**
   - Clicks "Rejoindre la consultation" button
   - Opens Jitsi Meet in new tab
   - No additional login required
   - Doctor can join same link

4. **Video Conference**
   - Patient and doctor meet in secure room
   - Video/audio controls available
   - Chat and screen sharing possible
   - Session automatically expires after appointment

## Mobile Responsive Design

On mobile devices, the layout adapts:
- Buttons stack vertically
- Meet link section remains prominent
- Touch-optimized button sizes
- Full-width for better visibility

## Accessibility Features

- ✅ Clear visual hierarchy
- ✅ Color contrast meets WCAG AA standards
- ✅ Icon + text labels for clarity
- ✅ Keyboard navigation support
- ✅ Screen reader friendly
- ✅ Focus indicators on interactive elements

## Technical Implementation

### Frontend Component
File: `frontend/src/components/appointments/AppointmentCard.svelte`

Key features:
- Conditional rendering based on `is_teleconsultation` flag
- Security attributes on link (noopener, noreferrer)
- Smooth hover animations
- Gradient backgrounds for visual appeal
- SVG icons for crisp rendering

### Styling
- Tailwind CSS utilities
- Gradient backgrounds (from-green-50 to-emerald-50)
- Shadow effects for depth
- Transform animations on hover
- Responsive design breakpoints

## Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

Note: Jitsi Meet requires WebRTC support (available in all modern browsers)
