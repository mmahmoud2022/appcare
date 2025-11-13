# Teleconsultation Feature Documentation

## Overview
The teleconsultation feature enables patients to have remote video consultations with doctors through an integrated Jitsi Meet video conferencing solution.

## How It Works

### Backend
1. **Appointment Creation**: When a patient creates an appointment with `consultation_type: "teleconsultation"`, the system automatically generates a unique Jitsi Meet room link.

2. **Meet Link Generation**: 
   - Uses SHA-256 hashing to create secure, unique room identifiers
   - Format: `https://meet.jit.si/sante-consult-{hash}`
   - Hash is based on: appointment ID + doctor ID + patient ID + appointment date
   - Links are deterministic (same appointment = same link) but unique across appointments

3. **Database Storage**: The `meet_link` is stored in the `appointments` table for persistence

4. **Lifecycle Management**:
   - Created automatically when appointment type is "teleconsultation"
   - Regenerated if consultation type changes to teleconsultation
   - Removed if consultation type changes away from teleconsultation

### Frontend
1. **Appointment Card Display**: Teleconsultation appointments show a special section with:
   - Video icon indicator
   - Green-themed design for easy identification
   - "Join Meeting" button
   - Link opens in new tab with security attributes

2. **User Experience**:
   - Clear visual distinction between in-person and teleconsultation appointments
   - One-click access to video consultation
   - No additional authentication required (link-based access)

## Database Schema

### Migration: `g1h2i3j4k5l6_add_meet_link_to_appointments.py`
```sql
ALTER TABLE appointments ADD COLUMN meet_link VARCHAR(500) NULL;
```

### Appointment Model Update
```python
class Appointment(Base):
    # ... other fields ...
    meet_link = Column(String(500), nullable=True)  # Jitsi Meet link
```

## API Response Example

```json
{
  "id": 123,
  "doctor_id": 456,
  "patient_id": 789,
  "appointment_date": "2025-11-15T10:30:00Z",
  "consultation_type": "teleconsultation",
  "meet_link": "https://meet.jit.si/sante-consult-a1b2c3d4e5f6g7h8",
  "status": "confirmed",
  "reason": "Follow-up consultation",
  "is_teleconsultation": true,
  // ... other fields ...
}
```

## Security Considerations

1. **Hashed Room IDs**: Room identifiers are hashed to prevent enumeration attacks
2. **No Raw IDs Exposed**: Patient/doctor IDs are not visible in the room URL
3. **Deterministic Links**: Same appointment always gets same link (for consistency)
4. **Link Security Attributes**: 
   - `target="_blank"` - Opens in new tab
   - `rel="noopener noreferrer"` - Prevents window.opener exploits

## Testing

### Unit Tests (8 tests, all passing)
- ✅ Link generation for teleconsultation type
- ✅ No link for in-person appointments
- ✅ Valid Jitsi URL format
- ✅ Deterministic link generation
- ✅ Unique links per appointment
- ✅ Secure hashing (no ID exposure)

### Test Coverage
```bash
cd backend
python -m pytest tests/test_teleconsultation_service.py -v
```

## Usage Examples

### Creating a Teleconsultation Appointment

**Request:**
```http
POST /api/v1/patient/appointments
Content-Type: application/json
Authorization: Bearer {token}

{
  "doctor_id": 456,
  "appointment_date": "2025-11-15T10:30:00Z",
  "consultation_type": "teleconsultation",
  "reason": "Follow-up consultation",
  "patient_notes": "Experiencing some improvement"
}
```

**Response:**
```json
{
  "id": 123,
  "doctor_id": 456,
  "patient_id": 789,
  "appointment_date": "2025-11-15T10:30:00Z",
  "consultation_type": "teleconsultation",
  "meet_link": "https://meet.jit.si/sante-consult-a1b2c3d4e5f6g7h8",
  "status": "pending",
  "reason": "Follow-up consultation",
  "patient_notes": "Experiencing some improvement",
  "is_teleconsultation": true,
  "duration": 30,
  "price": 50.0
}
```

## Configuration

### Jitsi Meet Domain
The default configuration uses the public Jitsi Meet instance (`meet.jit.si`). For production, you can:

1. **Use Public Instance**: Current default (meet.jit.si)
2. **Self-Host Jitsi**: Update `JITSI_DOMAIN` in `TeleconsultationService`

To change the domain:
```python
# app/services/teleconsultation_service.py
class TeleconsultationService:
    JITSI_DOMAIN = "your-domain.com"  # Replace with your Jitsi server
```

## Future Enhancements

1. **Email Notifications**: Send meet link in appointment confirmation emails
2. **Calendar Integration**: Add meet link to calendar invites
3. **Pre-meeting Reminders**: Send link reminder 15 minutes before appointment
4. **Recording Options**: Optional session recording (with consent)
5. **Custom Branding**: White-label Jitsi interface with clinic branding
6. **Waiting Room**: Virtual waiting room before doctor joins
7. **Screen Sharing**: Enable screen sharing for medical images/reports

## Troubleshooting

### Link Not Generated
- Verify `consultation_type` is set to "teleconsultation"
- Check that appointment has a valid ID (must be saved to DB first)
- Review logs for any errors during link generation

### Link Not Displayed
- Ensure `meet_link` field is included in API response schema
- Verify frontend `PatientAppointment` type includes `meet_link`
- Check that `is_teleconsultation` flag is true

### Security Concerns
- All links use HTTPS protocol
- Room IDs are cryptographically hashed
- Links can only be accessed by those who have them
- Consider adding password protection for extra security (future enhancement)
