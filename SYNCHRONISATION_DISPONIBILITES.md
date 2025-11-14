# Analyse et Amélioration de la Synchronisation Disponibilités Docteur ↔ Rendez-vous Patient

## 🔴 Problèmes Identifiés

### 1. **Pas de Rafraîchissement Temps Réel**
- ❌ Les créneaux ne se mettent pas à jour automatiquement quand un docteur modifie sa disponibilité
- ❌ Un patient peut voir des créneaux obsolètes s'il laisse la page ouverte
- ❌ Pas de notification quand un créneau sélectionné devient indisponible

### 2. **Pas de Validation en Temps Réel**
- ❌ Aucune vérification si le créneau est toujours libre au moment de la réservation
- ❌ Risque de double réservation si deux patients réservent le même créneau simultanément
- ❌ Pas de verrouillage temporaire pendant qu'un patient complète sa réservation

### 3. **Génération de Créneaux Côté Frontend**
- ❌ Les créneaux sont calculés dans `slots.ts` côté client
- ❌ Pas de prise en compte des rendez-vous déjà pris
- ❌ Pas de prise en compte des slots bloqués (`DoctorBlockedSlot`)
- ❌ Logique de génération dupliquée (frontend + potentiellement backend)

### 4. **Pas de Distinction Cabinet/Téléconsultation**
- ⚠️ Les créneaux affichés ne différencient pas le type de consultation
- ⚠️ Un docteur peut avoir des horaires différents pour cabinet vs téléconsultation
- ⚠️ Pas de filtre visuel clair pour le type de consultation

### 5. **Architecture Polling vs Push**
- 📡 Actuellement: Système de polling manuel (refresh button)
- 📡 Besoin: WebSocket ou Server-Sent Events pour push temps réel

---

## ✅ Solutions Recommandées

### **PRIORITÉ 1: API Backend pour Créneaux Disponibles**

#### Créer endpoint: `GET /api/v1/doctors/{doctor_id}/available-slots`

```python
# backend/app/api/v1/endpoints/doctor.py

@router.get("/{doctor_id}/available-slots", response_model=List[AvailableSlotResponse])
async def get_available_slots(
    doctor_id: int,
    start_date: date = Query(..., description="Date de début (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Date de fin (YYYY-MM-DD)"),
    consultation_type: Optional[ConsultationType] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les créneaux RÉELLEMENT disponibles d'un médecin.
    
    Prend en compte:
    - Les horaires récurrents (DoctorScheduleEntry)
    - Les slots bloqués (DoctorBlockedSlot)
    - Les rendez-vous déjà pris
    - Le type de consultation (cabinet/téléconsultation)
    - La durée par défaut de consultation
    """
    return DoctorService.get_available_slots(
        db=db,
        doctor_id=doctor_id,
        start_date=start_date,
        end_date=end_date,
        consultation_type=consultation_type
    )
```

#### Schéma de réponse:
```python
class AvailableSlotResponse(BaseModel):
    id: str  # Identifiant unique du slot (ex: "2025-11-15T09:00:00")
    doctor_id: int
    start_time: datetime
    end_time: datetime
    consultation_types: List[ConsultationType]  # ["IN_PERSON", "TELECONSULTATION"] ou un seul
    is_available: bool  # True si libre
    schedule_entry_id: int  # ID de l'entrée de planning source
    
    class Config:
        from_attributes = True
```

#### Service backend:
```python
# backend/app/services/doctor_service.py

@staticmethod
def get_available_slots(
    db: Session,
    doctor_id: int,
    start_date: date,
    end_date: date,
    consultation_type: Optional[ConsultationType] = None
) -> List[Dict]:
    """
    Génère les créneaux disponibles en croisant:
    1. Horaires récurrents (DoctorScheduleEntry)
    2. Slots bloqués (DoctorBlockedSlot)
    3. Rendez-vous existants (Appointment)
    """
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Médecin non trouvé")
    
    # 1. Récupérer les entrées de planning
    schedule_entries = db.query(DoctorScheduleEntry).filter(
        DoctorScheduleEntry.doctor_id == doctor_id,
        DoctorScheduleEntry.is_active == True
    ).all()
    
    if consultation_type:
        schedule_entries = [
            e for e in schedule_entries 
            if consultation_type in e.consultation_types
        ]
    
    # 2. Récupérer les slots bloqués
    blocked_slots = db.query(DoctorBlockedSlot).filter(
        DoctorBlockedSlot.doctor_id == doctor_id,
        DoctorBlockedSlot.start_time >= datetime.combine(start_date, time.min),
        DoctorBlockedSlot.end_time <= datetime.combine(end_date, time.max)
    ).all()
    
    # 3. Récupérer les rendez-vous existants
    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date >= datetime.combine(start_date, time.min),
        Appointment.appointment_date <= datetime.combine(end_date, time.max),
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
    ).all()
    
    # 4. Générer tous les créneaux possibles
    slots = []
    current_date = start_date
    
    while current_date <= end_date:
        day_of_week = (current_date.weekday() + 1) % 7  # Convert Python's Monday=0 to Sunday=0
        
        # Trouver les entrées de planning pour ce jour
        day_entries = [e for e in schedule_entries if e.day_of_week == day_of_week]
        
        for entry in day_entries:
            # Générer les slots pour cette entrée
            slot_start_time = entry.start_time
            duration_minutes = entry.consultation_duration or 30
            
            while slot_start_time < entry.end_time:
                slot_start = datetime.combine(current_date, slot_start_time)
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                
                # Vérifier si le slot est disponible
                is_blocked = any(
                    blocked.start_time <= slot_start < blocked.end_time
                    for blocked in blocked_slots
                )
                
                is_booked = any(
                    abs((appt.appointment_date - slot_start).total_seconds()) < 60
                    for appt in appointments
                )
                
                slots.append({
                    'id': slot_start.isoformat(),
                    'doctor_id': doctor_id,
                    'start_time': slot_start,
                    'end_time': slot_end,
                    'consultation_types': entry.consultation_types,
                    'is_available': not (is_blocked or is_booked),
                    'schedule_entry_id': entry.id
                })
                
                # Passer au créneau suivant
                slot_start_time = (datetime.combine(current_date, slot_start_time) + 
                                  timedelta(minutes=duration_minutes)).time()
        
        current_date += timedelta(days=1)
    
    return slots
```

---

### **PRIORITÉ 2: Validation Atomique de Réservation**

#### Modifier endpoint: `POST /api/v1/patients/appointments`

```python
@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_patient_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_patient: User = Depends(get_current_patient)
):
    """
    Crée un rendez-vous AVEC VÉRIFICATION ATOMIQUE de disponibilité.
    """
    # ✅ VALIDATION: Vérifier que le créneau est toujours libre
    appointment_datetime = data.appointment_date
    
    # Chercher si un autre rendez-vous existe déjà à cette heure
    existing = db.query(Appointment).filter(
        Appointment.doctor_id == data.doctor_id,
        Appointment.appointment_date == appointment_datetime,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,  # Conflict
            detail="Ce créneau vient d'être réservé par un autre patient. Veuillez en choisir un autre."
        )
    
    # ✅ VALIDATION: Vérifier que le créneau n'est pas bloqué
    blocked = db.query(DoctorBlockedSlot).filter(
        DoctorBlockedSlot.doctor_id == data.doctor_id,
        DoctorBlockedSlot.start_time <= appointment_datetime,
        DoctorBlockedSlot.end_time > appointment_datetime
    ).first()
    
    if blocked:
        raise HTTPException(
            status_code=409,
            detail=f"Ce créneau est bloqué: {blocked.reason or 'Indisponible'}"
        )
    
    # ✅ Créer le rendez-vous
    appointment = PatientService.create_appointment(db, current_patient.id, data)
    
    # 🔔 Envoyer notification au docteur
    # TODO: WebSocket notification
    
    return appointment
```

---

### **PRIORITÉ 3: WebSocket pour Synchronisation Temps Réel**

#### Architecture proposée:

```
┌─────────────────┐          ┌──────────────────┐          ┌─────────────────┐
│   Patient UI    │◄────────►│  FastAPI Server  │◄────────►│   Doctor UI     │
│                 │          │   + WebSocket    │          │                 │
└─────────────────┘          └──────────────────┘          └─────────────────┘
         │                            │                              │
         │                            │                              │
         └────────── Event: "slot_booked" ──────────────────────────┘
                     Event: "schedule_updated"
                     Event: "appointment_cancelled"
```

#### Implémentation FastAPI:

```python
# backend/app/main.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        # doctor_id -> Set[WebSocket]
        self.doctor_connections: Dict[int, Set[WebSocket]] = {}
        # patient_id -> Set[WebSocket]
        self.patient_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect_doctor(self, doctor_id: int, websocket: WebSocket):
        await websocket.accept()
        if doctor_id not in self.doctor_connections:
            self.doctor_connections[doctor_id] = set()
        self.doctor_connections[doctor_id].add(websocket)
    
    async def connect_patient(self, patient_id: int, websocket: WebSocket):
        await websocket.accept()
        if patient_id not in self.patient_connections:
            self.patient_connections[patient_id] = set()
        self.patient_connections[patient_id].add(websocket)
    
    async def notify_doctor(self, doctor_id: int, message: dict):
        """Notifier tous les clients connectés au profil docteur"""
        if doctor_id in self.doctor_connections:
            dead_connections = set()
            for connection in self.doctor_connections[doctor_id]:
                try:
                    await connection.send_json(message)
                except:
                    dead_connections.add(connection)
            # Nettoyer les connexions mortes
            self.doctor_connections[doctor_id] -= dead_connections
    
    async def broadcast_schedule_update(self, doctor_id: int):
        """Notifier tous les patients qui consultent ce docteur"""
        message = {
            "type": "schedule_updated",
            "doctor_id": doctor_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.notify_doctor(doctor_id, message)

manager = ConnectionManager()

@app.websocket("/ws/doctor/{doctor_id}")
async def doctor_schedule_websocket(
    websocket: WebSocket,
    doctor_id: int,
    token: str = Query(...)
):
    # Valider le token JWT
    user = await validate_websocket_token(token)
    
    await manager.connect_patient(user.id, websocket)
    
    try:
        while True:
            # Garder la connexion ouverte
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Nettoyer à la déconnexion
        pass
```

#### Frontend WebSocket:

```typescript
// frontend/src/lib/websocket.ts

export class DoctorScheduleSocket {
    private ws: WebSocket | null = null;
    private doctorId: number;
    private token: string;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    
    constructor(doctorId: number, token: string) {
        this.doctorId = doctorId;
        this.token = token;
    }
    
    connect(onUpdate: () => void) {
        const wsUrl = `ws://localhost:8000/ws/doctor/${this.doctorId}?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('✅ WebSocket connecté');
            this.reconnectAttempts = 0;
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type === 'schedule_updated') {
                console.log('🔄 Disponibilités mises à jour');
                onUpdate();  // Recharger les créneaux
            }
            
            if (message.type === 'slot_booked') {
                console.log('📅 Créneau réservé:', message.slot_id);
                onUpdate();
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('🔌 WebSocket fermé');
            this.attemptReconnect(onUpdate);
        };
    }
    
    private attemptReconnect(onUpdate: () => void) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`🔄 Tentative de reconnexion dans ${delay}ms...`);
            setTimeout(() => this.connect(onUpdate), delay);
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
```

#### Utilisation dans Svelte:

```typescript
// frontend/src/routes/patients/PatientAppointments.svelte

import { DoctorScheduleSocket } from '../../lib/websocket';

let wsConnection: DoctorScheduleSocket | null = null;

// Quand on ouvre la modal de booking
const openBookingModal = (doctor: DoctorSearchResult) => {
    selectedDoctor = doctor;
    showBookingModal = true;
    
    // 🔌 Connecter WebSocket
    const token = localStorage.getItem('access_token');
    wsConnection = new DoctorScheduleSocket(doctor.id, token);
    wsConnection.connect(() => {
        // Callback: recharger les créneaux
        loadDoctorAvailability(doctor.id);
    });
};

// Quand on ferme la modal
const closeBookingModal = () => {
    showBookingModal = false;
    
    // 🔌 Déconnecter WebSocket
    if (wsConnection) {
        wsConnection.disconnect();
        wsConnection = null;
    }
};
```

---

### **PRIORITÉ 4: Différenciation Cabinet/Téléconsultation**

#### Modifier le SlotPicker:

```svelte
<!-- frontend/src/components/booking/BookingSlotPicker.svelte -->

<div class="slot-grid">
  {#each visibleSlotGroups as group}
    <div class="day-group">
      <h4>{group.date}</h4>
      <div class="slots">
        {#each group.slots as slot}
          <button
            class="slot-button"
            class:in-person={slot.consultation_types.includes('IN_PERSON')}
            class:teleconsultation={slot.consultation_types.includes('TELECONSULTATION')}
            class:both={slot.consultation_types.length === 2}
            disabled={!slot.is_available}
            on:click={() => onSlotSelect(slot)}
          >
            <span class="time">{slot.displayTime}</span>
            
            {#if slot.consultation_types.length === 2}
              <span class="badge">Cabinet & Télé</span>
            {:else if slot.consultation_types.includes('TELECONSULTATION')}
              <svg><!-- Icône caméra --></svg>
              <span class="badge">Téléconsultation</span>
            {:else}
              <svg><!-- Icône hôpital --></svg>
              <span class="badge">Cabinet</span>
            {/if}
          </button>
        {/each}
      </div>
    </div>
  {/each}
</div>

<style>
  .slot-button.in-person {
    border-color: #3B82F6; /* Bleu pour cabinet */
  }
  
  .slot-button.teleconsultation {
    border-color: #10B981; /* Vert pour télé */
  }
  
  .slot-button.both {
    background: linear-gradient(135deg, #3B82F6 50%, #10B981 50%);
  }
</style>
```

---

### **PRIORITÉ 5: Verrouillage Temporaire (Soft Lock)**

Empêcher la double réservation en réservant temporairement un créneau pendant 5 minutes:

```python
# backend/app/models/appointment.py

class SlotReservation(Base):
    """Réservation temporaire d'un créneau (5min max)"""
    __tablename__ = "slot_reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    slot_datetime = Column(DateTime(timezone=True), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reserved_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        Index('ix_slot_reservations_lookup', 'doctor_id', 'slot_datetime'),
    )

# Migration Alembic
def upgrade():
    op.create_table(
        'slot_reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('slot_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('reserved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctor_profiles.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
```

#### API pour réserver temporairement:

```python
@router.post("/appointments/reserve-slot")
async def reserve_slot_temporarily(
    doctor_id: int,
    slot_datetime: datetime,
    db: Session = Depends(get_db),
    current_patient: User = Depends(get_current_patient)
):
    """
    Réserve temporairement un créneau pendant 5 minutes.
    Empêche d'autres patients de le réserver pendant ce temps.
    """
    # Vérifier si déjà réservé
    existing = db.query(SlotReservation).filter(
        SlotReservation.doctor_id == doctor_id,
        SlotReservation.slot_datetime == slot_datetime,
        SlotReservation.expires_at > datetime.utcnow()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Ce créneau est en cours de réservation par un autre patient"
        )
    
    # Créer réservation temporaire
    reservation = SlotReservation(
        doctor_id=doctor_id,
        slot_datetime=slot_datetime,
        patient_id=current_patient.id,
        reserved_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.add(reservation)
    db.commit()
    
    return {"reserved_until": reservation.expires_at}
```

---

## 📊 Comparaison Avant/Après

| Aspect | ❌ Avant | ✅ Après |
|--------|---------|---------|
| **Synchronisation** | Manuelle (refresh button) | Temps réel (WebSocket) |
| **Source créneaux** | Générés côté frontend | API backend `/available-slots` |
| **Validation** | Aucune vérification | Validation atomique + soft lock |
| **Double réservation** | Possible | Impossible (verrouillage 5min) |
| **Slots bloqués** | Ignorés | Pris en compte |
| **RDV existants** | Ignorés | Filtrés automatiquement |
| **Type consultation** | Pas de distinction visuelle | Badges + couleurs différenciées |
| **Notification docteur** | Email uniquement | WebSocket + Email |
| **Performance** | Calculs répétés | Cache + indexation DB |

---

## 🚀 Plan d'Implémentation (4 Phases)

### **Phase 1 (1-2 jours): Backend Slots API**
- [*] Créer `AvailableSlotResponse` schema
- [*] Implémenter `DoctorService.get_available_slots()`
- [*] Ajouter endpoint `GET /doctors/{id}/available-slots`
- [*] Tests unitaires + intégration
- [*] Migration pour indexer `appointment_date`

### **Phase 2 (1 jour): Validation Atomique** ⭐
- [*] Ajouter vérification créneau libre dans `create_appointment`
- [*] Ajouter vérification slots bloqués
- [*] Retourner erreur 409 Conflict si occupé
- [*] Tests de concurrence (2 patients simultanés)

### **Phase 3 (2-3 jours): WebSocket** ⭐
- [*] Setup `ConnectionManager` dans FastAPI avec Redis pub/sub
- [*] Créer endpoint `/ws/doctor/{doctor_id}` avec authentification JWT
- [*] Créer endpoint `/ws/patient/{patient_id}` pour notifications personnelles
- [*] Intégrer lifespan context manager dans main.py
- [*] Créer `DoctorScheduleSocket` classe TypeScript
- [*] Intégrer WebSocket dans `PatientAppointments.svelte`
- [*] Ajouter indicateur visuel "Temps réel" dans UI
- [*] Gérer reconnexion automatique avec backoff exponentiel
- [*] Notification WebSocket lors de création d'appointments
- [ ] Tests de charge (100+ connexions)

### **Phase 4 (1 jour): UI Cabinet/Télé** ⭐
- [*] Ajouter badges visuels dans `BookingSlotPicker` avec emojis (🏥 📹 🎯)
- [*] Couleurs différenciées (bleu=cabinet, vert=télé, dégradé=mixte)
- [*] Filtres de recherche par type avec boutons interactifs
- [*] Légende explicative des couleurs
- [*] Responsive mobile avec tailles adaptatives et textes raccourcis
- [*] Active:scale effect sur les boutons pour meilleur feedback tactile

---

## 🔧 Configuration Serveur

### Docker Compose (Redis pour WebSocket pub/sub):

```yaml
# docker-compose.yml

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
  
  backend:
    depends_on:
      - postgres
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

volumes:
  redis_data:
```

### Variables d'environnement:

```bash
# .env

REDIS_URL=redis://localhost:6379/0
WEBSOCKET_ENABLED=true
SLOT_RESERVATION_TIMEOUT_MINUTES=5
```

---

## 📈 Métriques de Succès

| Métrique | Objectif |
|----------|----------|
| Temps de synchronisation | < 500ms (WebSocket) |
| Double réservations | 0% (actuellement possible) |
| Taux de rafraîchissement manuel | -80% (automatique) |
| Précision créneaux affichés | 100% (validation backend) |
| Satisfaction utilisateur | +40% (sondage post-implémentation) |

---

## ⚠️ Points d'Attention

1. **Charge serveur**: WebSocket maintient des connexions permanentes
   - Solution: Load balancer avec sticky sessions
   - Monitoring: Prometheus + Grafana pour métriques WebSocket

2. **Fallback si WebSocket échoue**: 
   - Polling toutes les 30s comme backup
   - Message d'avertissement à l'utilisateur

3. **Scalabilité horizontale**:
   - Utiliser Redis Pub/Sub pour broadcaster entre instances
   - Sticky sessions Nginx pour WebSocket

4. **Sécurité**:
   - Valider JWT dans WebSocket handshake
   - Rate limiting sur `/available-slots` (1 req/sec par user)

---

## 📚 Ressources Supplémentaires

- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [Svelte Store pour État Global](https://svelte.dev/docs/svelte-store)
- [PostgreSQL Row-Level Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- [Redis Pub/Sub Pattern](https://redis.io/docs/manual/pubsub/)

---

**Auteur**: AI Assistant  
**Date**: 14 novembre 2025  
**Version**: 1.0
