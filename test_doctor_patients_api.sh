#!/bin/bash

# Script pour tester l'API des patients du docteur

echo "🔍 Test de l'API Doctor Patients"
echo "================================="
echo ""

# Récupérer le token (simuler une connexion de docteur)
echo "1️⃣ Connexion en tant que docteur..."

# Vous devez remplacer ces identifiants par ceux d'un docteur valide dans votre système
# Pour le moment, testons sans auth
echo ""
echo "2️⃣ Test de l'endpoint /api/v1/doctors/patients"
echo "URL: http://localhost:8000/api/v1/doctors/patients"
echo ""

# Test sans authentification (devrait retourner 401)
echo "Test sans authentification:"
curl -s -X GET "http://localhost:8000/api/v1/doctors/patients?page=1&page_size=10" \
  -H "Content-Type: application/json" | jq '.' || echo "❌ Erreur ou pas de jq installé"

echo ""
echo "================================="
echo "Note: Vous devez être connecté en tant que docteur pour que cela fonctionne."
echo "Le frontend devrait gérer l'authentification automatiquement."
echo ""
echo "Pour tester avec authentification, connectez-vous d'abord via l'interface web,"
echo "puis vérifiez le token dans les outils de développement du navigateur (Application > Local Storage)"
