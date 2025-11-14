#!/usr/bin/env python3
"""
Script pour recalculer les statistiques des docteurs (average_rating et total_reviews)
à partir des avis existants dans la base de données.

Usage:
    python update_doctor_statistics.py
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_db
from app.models.doctor import DoctorProfile, DoctorReview
from sqlalchemy import func


def update_all_doctor_statistics():
    """Recalculer les statistiques pour tous les docteurs"""
    db = next(get_db())
    
    try:
        # Récupérer tous les profils de docteurs
        doctors = db.query(DoctorProfile).all()
        
        print(f"🔍 Trouvé {len(doctors)} docteurs")
        updated_count = 0
        
        for doctor in doctors:
            # Récupérer tous les avis pour ce docteur
            reviews = db.query(DoctorReview).filter(
                DoctorReview.doctor_id == doctor.id
            ).all()
            
            if reviews:
                total_reviews = len(reviews)
                average_rating = sum(r.rating for r in reviews) / total_reviews
                
                # Mettre à jour les statistiques
                doctor.total_reviews = total_reviews
                doctor.average_rating = round(average_rating, 2)
                
                print(f"✅ Dr {doctor.user.first_name} {doctor.user.last_name}: "
                      f"{total_reviews} avis, moyenne {average_rating:.2f}/5")
                updated_count += 1
            else:
                # Pas d'avis, mettre à 0
                if doctor.total_reviews != 0 or doctor.average_rating != 0.0:
                    doctor.total_reviews = 0
                    doctor.average_rating = 0.0
                    print(f"ℹ️  Dr {doctor.user.first_name} {doctor.user.last_name}: "
                          f"Aucun avis (réinitialisé à 0)")
                    updated_count += 1
        
        db.commit()
        print(f"\n🎉 Mise à jour terminée ! {updated_count} profils mis à jour.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("📊 Recalcul des statistiques des docteurs...")
    update_all_doctor_statistics()
