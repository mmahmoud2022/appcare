# Guide de Migration - PatientAppointments.svelte

## 📋 Vue d'ensemble

Ce guide explique comment migrer le composant `PatientAppointments.svelte` vers une architecture modulaire et optimisée.

## 🎯 Améliorations apportées

### ✅ Complétées

#### 1. **Utilitaires séparés** (`/lib/utils/`)

**Fichiers créés :**
- `dates.ts` - Manipulation et formatage des dates
- `slots.ts` - Génération et gestion des créneaux
- `formatting.ts` - Labels et formatage des données médicales

**Bénéfices :**
- ✅ Code réutilisable dans toute l'application
- ✅ Tests unitaires plus faciles
- ✅ Réduction de la taille du composant principal
- ✅ Meilleure maintenabilité

**Exemple d'utilisation :**
```typescript
import { formatAppointmentDate, formatTime } from '$lib/utils/dates';
import { generateSlotSuggestions, groupSlotsByDay } from '$lib/utils/slots';
import { formatSpecialty, CONSULTATION_LABELS } from '$lib/utils/formatting';

// Au lieu de :
const date = new Date(appointment.appointment_date).toLocaleString('fr-FR', {...});

// Utiliser :
const date = formatAppointmentDate(appointment.appointment_date);
```

#### 2. **Composants modulaires** (`/components/`)

**Composants créés :**
- `AppointmentCard.svelte` - Carte de rendez-vous à venir
- `PastAppointmentCard.svelte` - Carte de rendez-vous passé
- `Toast.svelte` - Système de notifications

**Bénéfices :**
- ✅ Composants réutilisables
- ✅ Logique isolée et testable
- ✅ Props typées avec TypeScript
- ✅ Meilleure performance (re-render ciblé)

**Exemple d'utilisation :**
```svelte
<script>
  import AppointmentCard from '$components/appointments/AppointmentCard.svelte';
  import { toast } from '$components/ui/Toast.svelte';
</script>

{#each upcoming as appointment}
  <AppointmentCard 
    {appointment}
    on:reschedule={handleReschedule}
    on:cancel={handleCancel}
  />
{/each}
```

#### 3. **Store Svelte pour l'état global** (`/stores/appointments.ts`)

**Stores créés :**
- `appointments` - Liste complète des rendez-vous
- `upcomingAppointments` - Rendez-vous à venir (dérivé)
- `pastAppointments` - Rendez-vous passés (dérivé)
- `appointmentStats` - Statistiques (dérivé)
- `loading` - État de chargement
- `error` - Gestion des erreurs

**Bénéfices :**
- ✅ État centralisé
- ✅ Calculs automatiques avec `derived`
- ✅ Évite le prop drilling
- ✅ Réactivité optimisée

**Exemple d'utilisation :**
```svelte
<script>
  import { upcomingAppointments, pastAppointments, loading } from '$stores/appointments';
</script>

{#if $loading}
  <Loader />
{:else}
  {#each $upcomingAppointments as appointment}
    <AppointmentCard {appointment} />
  {/each}
{/if}
```

#### 4. **Système de notifications Toast**

**Remplacement de `alert()` :**
```typescript
// Avant
alert("Impossible de créer ce rendez-vous");

// Après
import { toast } from '$components/ui/Toast.svelte';
toast.error("Impossible de créer ce rendez-vous");
toast.success("Rendez-vous confirmé !");
toast.warning("Attention : créneau bientôt complet");
toast.info("Nouvelle disponibilité ajoutée");
```

## 📊 Comparaison Avant/Après

### Taille du fichier
- **Avant :** 1200+ lignes
- **Après :** ~300 lignes (composant principal)

### Complexité
- **Avant :** Tout dans un seul fichier
- **Après :** 
  - 3 fichiers utilitaires
  - 3 composants réutilisables
  - 1 store centralisé

### Performance
- **Avant :** Re-calcul systématique des créneaux
- **Après :** Mémoïsation avec `derived` stores

### Testabilité
- **Avant :** Difficile à tester (tout couplé)
- **Après :** Tests unitaires par module

## 🔧 Plan de migration étape par étape

### Étape 1 : Installer le système de Toast (5 min)

```svelte
<!-- Dans App.svelte ou layout principal -->
<script>
  import Toast from './components/ui/Toast.svelte';
</script>

<Toast />
<!-- Reste de l'app -->
```

### Étape 2 : Remplacer les imports (10 min)

```typescript
// Ancien code
const formatSpecialty = (specialty) => { ... };
const toInputDateTime = (date) => { ... };

// Nouveau code
import { formatSpecialty } from '$lib/utils/formatting';
import { toInputDateTime } from '$lib/utils/dates';
```

### Étape 3 : Utiliser les composants (20 min)

Remplacer les grandes sections HTML par les composants :

```svelte
<!-- Ancien -->
<div class="group relative perspective-1000">
  <!-- 100+ lignes de HTML -->
</div>

<!-- Nouveau -->
<AppointmentCard {appointment} on:reschedule on:cancel />
```

### Étape 4 : Migrer vers le store (15 min)

```svelte
<script>
  // Ancien
  let appointments = [];
  let upcoming = [];
  let past = [];
  
  const loadAppointments = async () => {
    // ...logique de chargement
    appointments = response.items;
    upcoming = appointments.filter(...);
    past = appointments.filter(...);
  };

  // Nouveau
  import { appointments, upcomingAppointments, pastAppointments } from '$stores/appointments';
  import { getPatientAppointments } from '$lib/api-patient';
  
  const loadAppointments = async () => {
    const response = await getPatientAppointments(1, 100);
    appointments.set(response.items); // Le reste se calcule automatiquement !
  };
</script>

{#each $upcomingAppointments as appointment}
  <!-- ... -->
{/each}
```

### Étape 5 : Remplacer les alert() (5 min)

```typescript
// Chercher tous les alert() dans le code
// Remplacer par toast.error(), toast.success(), etc.

try {
  await createAppointment(...);
  toast.success('Rendez-vous créé avec succès ! 🎉');
} catch (err) {
  toast.error(err?.response?.data?.detail ?? 'Erreur lors de la création');
}
```

## 🎨 Optimisations supplémentaires recommandées

### A. Lazy loading des modals (Performance)

```svelte
<script>
  import { onMount } from 'svelte';
  
  let BookingModal;
  let RescheduleModal;
  
  onMount(async () => {
    // Charger les modals uniquement quand nécessaire
    const modules = await Promise.all([
      import('./components/modals/BookingModal.svelte'),
      import('./components/modals/RescheduleModal.svelte')
    ]);
    BookingModal = modules[0].default;
    RescheduleModal = modules[1].default;
  });
</script>

{#if showBookingModal && BookingModal}
  <svelte:component this={BookingModal} ... />
{/if}
```

### B. Virtualisation des listes (Performance)

Pour les utilisateurs avec beaucoup de rendez-vous :

```bash
npm install svelte-virtual-list
```

```svelte
<script>
  import VirtualList from 'svelte-virtual-list';
</script>

<VirtualList items={$upcomingAppointments} let:item>
  <AppointmentCard appointment={item} />
</VirtualList>
```

### C. Debouncing des recherches

```typescript
import { debounce } from '$lib/utils/debounce';

const searchDoctors = debounce(async (query: string) => {
  // Recherche API
}, 300);
```

### D. Configuration des animations

Respecter les préférences utilisateur :

```svelte
<script>
  import { prefersReducedMotion } from '$lib/utils/accessibility';
</script>

<div 
  transition:fly={{ 
    duration: $prefersReducedMotion ? 0 : 300 
  }}
>
```

## 📦 Structure finale recommandée

```
frontend/src/
├── lib/
│   ├── api-patient.ts
│   ├── api-doctor.ts
│   └── utils/
│       ├── dates.ts           ✅ Créé
│       ├── slots.ts           ✅ Créé
│       ├── formatting.ts      ✅ Créé
│       ├── debounce.ts        ⏳ À créer
│       └── accessibility.ts   ⏳ À créer
├── stores/
│   └── appointments.ts        ✅ Créé
├── components/
│   ├── appointments/
│   │   ├── AppointmentCard.svelte        ✅ Créé
│   │   ├── PastAppointmentCard.svelte    ✅ Créé
│   │   ├── AppointmentList.svelte        ⏳ À créer
│   │   └── AppointmentStats.svelte       ⏳ À créer
│   ├── modals/
│   │   ├── BookingModal.svelte           ⏳ À créer
│   │   ├── RescheduleModal.svelte        ⏳ À créer
│   │   └── ConfirmationModal.svelte      ⏳ À créer
│   ├── slots/
│   │   ├── SlotPicker.svelte             ⏳ À créer
│   │   └── SlotGroup.svelte              ⏳ À créer
│   └── ui/
│       ├── Toast.svelte       ✅ Créé
│       ├── Loader.svelte      ⏳ À créer
│       └── EmptyState.svelte  ⏳ À créer
└── routes/
    └── patients/
        └── PatientAppointments.svelte (REFACTORÉ)
```

## ✅ Checklist de migration

- [x] Créer les utilitaires (dates, slots, formatting)
- [x] Créer le store appointments
- [x] Créer AppointmentCard
- [x] Créer PastAppointmentCard
- [x] Créer Toast
- [ ] Remplacer les imports dans PatientAppointments.svelte
- [ ] Utiliser les composants dans le template
- [ ] Migrer vers le store
- [ ] Remplacer tous les alert()
- [ ] Tester la migration
- [ ] Supprimer le code dupliqué

## 🧪 Tests recommandés

```typescript
// tests/utils/dates.test.ts
import { describe, it, expect } from 'vitest';
import { toInputDateTime, formatTime } from '$lib/utils/dates';

describe('Date utilities', () => {
  it('should format date to input datetime', () => {
    const date = new Date('2025-11-09T14:30:00');
    expect(toInputDateTime(date)).toBe('2025-11-09T14:30');
  });
  
  it('should format time correctly', () => {
    const date = new Date('2025-11-09T14:30:00');
    expect(formatTime(date)).toBe('14:30');
  });
});
```

## 📚 Ressources

- [Svelte Stores Documentation](https://svelte.dev/docs/svelte-store)
- [Svelte Component Best Practices](https://svelte.dev/docs/best-practices)
- [TypeScript with Svelte](https://svelte.dev/docs/typescript)

## 🎯 Résultat attendu

Après migration complète :
- ✅ Code 75% plus petit dans le composant principal
- ✅ Meilleure performance (moins de re-renders)
- ✅ Code réutilisable dans d'autres vues
- ✅ Tests unitaires possibles
- ✅ Maintenance simplifiée
- ✅ Meilleure expérience utilisateur (toasts au lieu d'alerts)
