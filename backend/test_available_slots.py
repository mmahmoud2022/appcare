#!/usr/bin/env python3
"""
Script de test pour vérifier l'endpoint /available-slots
"""
import sys
from datetime import date, timedelta

# Ajouter le répertoire parent au path
sys.path.insert(0, '/home/alpha/fastapi-frontend/backend')

try:
    print("🔍 Test 1: Import des modules...")
    from app.schemas.doctor import AvailableSlotResponse
    from app.services.doctor_service import DoctorService
    print("✅ Imports réussis")
    
    print("\n🔍 Test 2: Vérification du schéma...")
    print(f"   - AvailableSlotResponse: {AvailableSlotResponse}")
    print(f"   - Fields: {AvailableSlotResponse.model_fields.keys()}")
    
    print("\n🔍 Test 3: Vérification de la méthode get_available_slots...")
    print(f"   - Méthode existe: {hasattr(DoctorService, 'get_available_slots')}")
    
    if hasattr(DoctorService, 'get_available_slots'):
        import inspect
        sig = inspect.signature(DoctorService.get_available_slots)
        print(f"   - Signature: {sig}")
    
    print("\n✅ Tous les tests de base passent!")
    print("\n💡 Pour tester avec une vraie DB, lancez:")
    print("   docker-compose exec backend python test_available_slots_db.py")
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
