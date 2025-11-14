#!/usr/bin/env python3
"""
Vérifier les données dans la base de données
"""
import psycopg2
from datetime import datetime

# Connexion à la DB
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="sante_db",
    user="sante_user",
    password="sante_password"
)

cur = conn.cursor()

print("=" * 60)
print("VÉRIFICATION DES DONNÉES POUR LE DEBUGGING")
print("=" * 60)

# 1. Compter les médecins
cur.execute("SELECT COUNT(*) FROM doctor_profiles")
doctor_count = cur.fetchone()[0]
print(f"\n📊 Nombre total de médecins: {doctor_count}")

# 2. Lister les 5 premiers médecins
cur.execute("""
    SELECT dp.id, u.first_name, u.last_name, dp.specialty
    FROM doctor_profiles dp
    JOIN users u ON dp.user_id = u.id
    LIMIT 5
""")
print("\n👨‍⚕️ Liste des médecins:")
for row in cur.fetchall():
    print(f"   ID: {row[0]} | {row[1]} {row[2]} | Spécialité: {row[3]}")

# 3. Vérifier les créneaux de planning
cur.execute("""
    SELECT doctor_id, COUNT(*) as nb_entries
    FROM doctor_schedule_entries
    GROUP BY doctor_id
    ORDER BY doctor_id
    LIMIT 5
""")
print("\n📅 Nombre d'entrées de planning par médecin:")
schedule_data = cur.fetchall()
if schedule_data:
    for row in schedule_data:
        print(f"   Médecin ID {row[0]}: {row[1]} créneaux configurés")
else:
    print("   ⚠️  AUCUN créneau configuré!")

# 4. Détails du premier médecin
if doctor_count > 0:
    cur.execute("""
        SELECT id, day_of_week, start_time, end_time, consultation_type, slot_duration, is_active
        FROM doctor_schedule_entries
        WHERE doctor_id = 1
        LIMIT 5
    """)
    print("\n🔍 Détails des créneaux du médecin ID=1:")
    entries = cur.fetchall()
    if entries:
        for row in entries:
            day_names = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
            print(f"   {day_names[row[1]]}: {row[2]}-{row[3]} | Type: {row[4]} | Durée: {row[5]}min | Actif: {row[6]}")
    else:
        print("   ⚠️  Aucun créneau pour ce médecin!")

# 5. Compter les rendez-vous
cur.execute("SELECT COUNT(*) FROM appointments")
appt_count = cur.fetchone()[0]
print(f"\n📆 Nombre total de rendez-vous: {appt_count}")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ Vérification terminée")
print("=" * 60)
