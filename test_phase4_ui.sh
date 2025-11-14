#!/bin/bash

# Test Phase 4: UI Cabinet/Téléconsultation
# Vérifie l'affichage des badges et filtres visuels

echo "========================================="
echo "🎨 TEST PHASE 4: UI CABINET/TÉLÉCONSULTATION"
echo "========================================="
echo ""

API_BASE="http://localhost:8000/api/v1"
DOCTOR_EMAIL="test.doctor.ui@example.com"
DOCTOR_PASSWORD="SecurePass123!"

# 1. Créer un médecin avec consultation mixte
echo "📝 Étape 1: Création médecin avec consultations mixtes"
DOCTOR_REGISTER=$(curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'"$DOCTOR_EMAIL"'",
    "password": "'"$DOCTOR_PASSWORD"'",
    "role": "doctor",
    "first_name": "Dr",
    "last_name": "Mixed"
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

# 3. Créer profil médecin avec "both"
echo ""
echo "👨‍⚕️ Étape 3: Création profil médecin (both)"
DOCTOR_PROFILE=$(curl -s -X POST "$API_BASE/doctors/" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "specialties": ["general_medicine"],
    "consultation_types": "both",
    "address": "456 UI Test Street",
    "city": "Lyon",
    "postal_code": "69001",
    "phone_number": "+33687654321",
    "languages": ["french"],
    "accepts_new_patients": true
  }')

DOCTOR_ID=$(echo "$DOCTOR_PROFILE" | jq -r '.id')
echo "Doctor ID: $DOCTOR_ID"

# 4. Créer horaires pour Cabinet uniquement (Lundi)
echo ""
echo "📅 Étape 4: Création horaire CABINET (Lundi 09:00-12:00)"
SCHEDULE_CABINET=$(curl -s -X POST "$API_BASE/doctors/schedule" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "day_of_week": 1,
    "start_time": "09:00",
    "end_time": "12:00",
    "consultation_type": "in_person",
    "slot_duration": 30,
    "location": "Cabinet Lyon"
  }')

echo "$SCHEDULE_CABINET" | jq '.'

# 5. Créer horaires pour Téléconsultation (Mardi)
echo ""
echo "📹 Étape 5: Création horaire TÉLÉCONSULTATION (Mardi 14:00-17:00)"
SCHEDULE_TELE=$(curl -s -X POST "$API_BASE/doctors/schedule" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "day_of_week": 2,
    "start_time": "14:00",
    "end_time": "17:00",
    "consultation_type": "teleconsultation",
    "slot_duration": 30,
    "location": "En ligne"
  }')

echo "$SCHEDULE_TELE" | jq '.'

# 6. Créer horaires mixtes (Mercredi)
echo ""
echo "🎯 Étape 6: Création horaire MIXTE (Mercredi 10:00-16:00)"
SCHEDULE_BOTH=$(curl -s -X POST "$API_BASE/doctors/schedule" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "day_of_week": 3,
    "start_time": "10:00",
    "end_time": "16:00",
    "consultation_type": "both",
    "slot_duration": 30,
    "location": "Cabinet ou Télé"
  }')

echo "$SCHEDULE_BOTH" | jq '.'

echo ""
echo "========================================="
echo "✅ CONFIGURATION TERMINÉE"
echo "========================================="
echo ""
echo "🎯 INSTRUCTIONS TEST MANUEL:"
echo ""
echo "1️⃣  FRONTEND TEST:"
echo "   - Ouvrir http://localhost:5173"
echo "   - Se connecter comme patient"
echo "   - Chercher 'Dr Mixed'"
echo "   - Ouvrir la modale de réservation"
echo ""
echo "2️⃣  VÉRIFIER LES BADGES:"
echo "   - Lundi (09:00-12:00): Badges BLEUS 🏥 'Cabinet'"
echo "   - Mardi (14:00-17:00): Badges VERTS 📹 'Téléconsultation'"
echo "   - Mercredi (10:00-16:00): Badges MIXTES 🎯 'Cabinet ou Télé'"
echo "   - Background avec dégradés selon le type"
echo ""
echo "3️⃣  TESTER LES FILTRES:"
echo "   - Cliquer 'Tous' → Voir tous les créneaux"
echo "   - Cliquer 'Cabinet' → Voir seulement Lundi + Mercredi"
echo "   - Cliquer 'Téléconsultation' → Voir seulement Mardi + Mercredi"
echo "   - Observer les boutons actifs (violet/bleu/vert)"
echo ""
echo "4️⃣  TESTER RESPONSIVE:"
echo "   - DevTools > Toggle device toolbar"
echo "   - iPhone SE (375px): Textes raccourcis, badges compacts"
echo "   - iPad (768px): Grille 2 colonnes"
echo "   - Desktop (1024px+): Full layout"
echo ""
echo "5️⃣  VÉRIFIER LÉGENDE:"
echo "   - Box grise en bas des filtres"
echo "   - Explique: Bleu=Cabinet, Vert=Télé, Mixte=Choix"
echo ""
echo "========================================="
echo "📊 CRITÈRES DE SUCCÈS:"
echo "========================================="
echo "✅ Badges colorés distincts par type"
echo "✅ Filtres fonctionnels avec highlight actif"
echo "✅ Dégradé bleu→vert pour slots 'both'"
echo "✅ Icônes SVG (🏥 bâtiment, 📹 caméra, 🎯 mixte)"
echo "✅ Responsive < 640px (textes courts, 1 col)"
echo "✅ Responsive > 640px (textes longs, 2 cols)"
echo "✅ Légende explicative visible"
echo "✅ Active:scale sur tap mobile"
echo ""
echo "========================================="
