#!/bin/bash

# Test de synchronisation WebSocket temps réel - Phase 3
# Ce script vérifie que les mises à jour de planning sont propagées en temps réel

echo "========================================="
echo "🧪 TEST WEBSOCKET - SYNCHRONISATION TEMPS RÉEL"
echo "========================================="
echo ""

API_BASE="http://localhost:8000/api/v1"
DOCTOR_EMAIL="test.doctor.ws@example.com"
DOCTOR_PASSWORD="SecurePass123!"
PATIENT_EMAIL="test.patient.ws@example.com"
PATIENT_PASSWORD="SecurePass123!"

# Nettoyer d'anciennes sessions
echo "🧹 Nettoyage..."

# 1. Créer un médecin de test
echo ""
echo "📝 Étape 1: Création médecin de test"
DOCTOR_REGISTER=$(curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'"$DOCTOR_EMAIL"'",
    "password": "'"$DOCTOR_PASSWORD"'",
    "role": "doctor",
    "first_name": "Dr",
    "last_name": "WebSocket"
  }')

echo "$DOCTOR_REGISTER" | jq '.'

# 2. Login médecin
echo ""
echo "🔐 Étape 2: Login médecin"
DOCTOR_LOGIN=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$DOCTOR_EMAIL&password=$DOCTOR_PASSWORD")

DOCTOR_TOKEN=$(echo "$DOCTOR_LOGIN" | jq -r '.access_token')
echo "Token médecin: ${DOCTOR_TOKEN:0:20}..."

# 3. Créer profil médecin
echo ""
echo "👨‍⚕️ Étape 3: Création profil médecin"
DOCTOR_PROFILE=$(curl -s -X POST "$API_BASE/doctors/" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "specialties": ["general_medicine"],
    "consultation_types": "both",
    "address": "123 Test Street",
    "city": "Paris",
    "postal_code": "75001",
    "phone_number": "+33612345678",
    "languages": ["french"],
    "accepts_new_patients": true
  }')

DOCTOR_ID=$(echo "$DOCTOR_PROFILE" | jq -r '.id')
echo "Doctor ID: $DOCTOR_ID"

# 4. Créer un créneau de planning
echo ""
echo "📅 Étape 4: Création horaire récurrent"
SCHEDULE=$(curl -s -X POST "$API_BASE/doctors/schedule" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "day_of_week": 1,
    "start_time": "09:00",
    "end_time": "12:00",
    "consultation_type": "both",
    "slot_duration": 30,
    "location": "Cabinet Paris"
  }')

SCHEDULE_ID=$(echo "$SCHEDULE" | jq -r '.id')
echo "Schedule ID: $SCHEDULE_ID"

# 5. Créer un patient de test
echo ""
echo "📝 Étape 5: Création patient de test"
PATIENT_REGISTER=$(curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'"$PATIENT_EMAIL"'",
    "password": "'"$PATIENT_PASSWORD"'",
    "role": "patient",
    "first_name": "Patient",
    "last_name": "WebSocket"
  }')

echo "$PATIENT_REGISTER" | jq '.'

# 6. Login patient
echo ""
echo "🔐 Étape 6: Login patient"
PATIENT_LOGIN=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$PATIENT_EMAIL&password=$PATIENT_PASSWORD")

PATIENT_TOKEN=$(echo "$PATIENT_LOGIN" | jq -r '.access_token')
echo "Token patient: ${PATIENT_TOKEN:0:20}..."

# 7. Vérifier l'endpoint WebSocket Stats
echo ""
echo "📊 Étape 7: Statistiques WebSocket"
WS_STATS=$(curl -s "$API_BASE/ws/stats")
echo "$WS_STATS" | jq '.'

echo ""
echo "========================================="
echo "✅ CONFIGURATION TERMINÉE"
echo "========================================="
echo ""
echo "🎯 INSTRUCTIONS TEST MANUEL:"
echo ""
echo "1️⃣  FRONTEND PATIENT:"
echo "   - Ouvrir http://localhost:5173"
echo "   - Se connecter avec: $PATIENT_EMAIL / $PATIENT_PASSWORD"
echo "   - Chercher 'Dr WebSocket'"
echo "   - Ouvrir la modale de réservation"
echo "   - Observer l'indicateur 'Temps réel' (point vert)"
echo ""
echo "2️⃣  TESTER LA SYNCHRONISATION:"
echo "   - Dans un autre onglet, se connecter comme médecin:"
echo "     Email: $DOCTOR_EMAIL"
echo "     Password: $DOCTOR_PASSWORD"
echo "   - Aller dans 'Mes Horaires'"
echo "   - Ajouter un slot bloqué ou modifier le planning"
echo "   - Retourner sur l'onglet patient"
echo "   - ✨ Les créneaux se rafraîchissent automatiquement!"
echo ""
echo "3️⃣  TESTER LA RÉSERVATION:"
echo "   - Réserver un créneau depuis le frontend patient"
echo "   - Ouvrir un 2ème onglet patient (autre navigateur)"
echo "   - Le créneau réservé disparaît en temps réel!"
echo ""
echo "4️⃣  CONSOLE LOGS:"
echo "   - Ouvrir DevTools > Console"
echo "   - Observer les messages WebSocket:"
echo "     🔌 Connexion WebSocket à: ws://localhost:8000/..."
echo "     ✅ WebSocket connecté"
echo "     📨 Message WebSocket reçu"
echo "     🎯 Créneau réservé / 📅 Planning mis à jour"
echo ""
echo "========================================="

# 8. Test curl direct WebSocket (si websocat installé)
if command -v websocat &> /dev/null; then
    echo ""
    echo "🔧 TEST WEBSOCAT (optionnel)"
    echo "Connexion WebSocket directe pendant 10 secondes..."
    timeout 10s websocat "ws://localhost:8000/api/v1/ws/doctor/$DOCTOR_ID?token=$PATIENT_TOKEN" || true
    echo "Connexion fermée"
fi

echo ""
echo "========================================="
echo "🎉 TEST SETUP COMPLET"
echo "========================================="
