# Celery Beat - Configuration des Rappels Automatiques

## 📋 Vue d'ensemble

Celery Beat est maintenant configuré et opérationnel pour les **rappels automatiques de rendez-vous** et les tâches de maintenance.

## 🎯 Tâches Planifiées

### 1. Rappels de rendez-vous (24h avant)
- **Tâche** : `send_daily_appointment_reminders`
- **Planification** : Tous les jours à 9h00 du matin
- **Fonctionnement** :
  - Recherche tous les rendez-vous confirmés dans les prochaines 24 heures
  - Envoie un email de rappel à chaque patient
  - Inclut : nom du médecin, date, heure du rendez-vous
  - Exclut les rendez-vous soft-deleted (`is_deleted=True`)

### 2. Nettoyage des tokens expirés
- **Tâche** : `cleanup_expired_tokens`
- **Planification** : Tous les jours à 2h00 du matin
- **Fonctionnement** :
  - Supprime les tokens de réinitialisation de mot de passe expirés
  - Supprime les tokens de vérification d'email expirés

### 3. Nettoyage des anciens rendez-vous (soft-deleted)
- **Tâche** : `cleanup_old_appointments`
- **Planification** : Tous les dimanches à 3h00 du matin
- **Fonctionnement** :
  - Supprime définitivement les rendez-vous soft-deleted depuis plus de 90 jours
  - Libère de l'espace dans la base de données

## 🚀 Démarrage des Services

```bash
# Démarrer tous les services Celery
docker compose up -d celery_worker celery_beat

# Vérifier le statut
docker ps | grep celery

# Voir les logs en temps réel
docker logs -f sante_celery_beat
docker logs -f sante_celery_worker
```

## 🔍 Monitoring et Debug

### Vérifier les tâches planifiées
```bash
# Lister les tâches planifiées
docker exec sante_celery_beat celery -A app.core.celery_app inspect scheduled

# Vérifier les tâches actives
docker exec sante_celery_beat celery -A app.core.celery_app inspect active

# Vérifier les workers enregistrés
docker exec sante_celery_beat celery -A app.core.celery_app inspect registered
```

### Logs de débogage
```bash
# Logs du scheduler (Beat)
docker logs sante_celery_beat --tail 100

# Logs du worker (exécution des tâches)
docker logs sante_celery_worker --tail 100 --follow

# Filtrer les logs de rappels
docker logs sante_celery_worker 2>&1 | grep REMINDER
```

## 📧 Template Email de Rappel

Le template se trouve dans `backend/app/templates/email_templates.py` :

```python
def appointment_reminder(
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str
) -> str
```

**Contenu de l'email** :
- Salutation personnalisée
- Informations du rendez-vous (médecin, date, heure)
- Rappel d'apporter les documents médicaux
- Design responsive avec le thème médical vert/bleu

## ⚙️ Configuration Technique

### Fichier : `backend/app/core/celery_app.py`

```python
# Instance Celery
celery_app = Celery(
    "sante_medical",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Timezone : Europe/Paris
timezone="Europe/Paris"
enable_utc=False

# Beat schedule (crontab)
beat_schedule={
    "send-daily-appointment-reminders": {
        "task": "app.tasks.send_daily_appointment_reminders",
        "schedule": crontab(hour=9, minute=0),
    },
    # ... autres tâches
}
```

### Variables d'environnement Docker

```yaml
# docker-compose.yml
celery_worker:
  environment:
    REDIS_URL: redis://redis:6379/0
    PYTHONPATH: /app
  working_dir: /app

celery_beat:
  environment:
    REDIS_URL: redis://redis:6379/0
    PYTHONPATH: /app
  working_dir: /app
```

## 🧪 Test Manuel

### Créer un rendez-vous de test (dans les 24h)

```bash
# Via l'API ou directement en base de données
# Créer un rendez-vous confirmé pour demain à cette heure
```

### Tester immédiatement (sans attendre 9h00)

Temporairement, modifiez le schedule dans `celery_app.py` :

```python
"test-send-reminders-every-minute": {
    "task": "app.tasks.send_daily_appointment_reminders",
    "schedule": 60.0,  # Toutes les 60 secondes
}
```

Puis redémarrez Beat :
```bash
docker restart sante_celery_beat
```

**N'oubliez pas de supprimer la tâche de test en production !**

## 📊 Statistiques et Métriques

La tâche retourne des métriques détaillées :

```python
{
    "success": True,
    "message": "Daily reminders processed",
    "reminders_sent": 5,
    "errors": 0,
    "total_appointments": 5
}
```

Logs structurés :
```
[REMINDER] Checking appointments between 2025-11-10 09:00:00 and 2025-11-11 09:00:00
[REMINDER] Found 5 appointments to remind
[REMINDER] Sending reminder for appointment 123 | patient=patient@example.com | doctor=Dr. Smith | datetime=11/11/2025 14:30
[REMINDER] Completed | sent=5 | errors=0 | total=5
```

## 🔒 Sécurité

- ✅ Les rendez-vous soft-deleted sont exclus des rappels
- ✅ Vérification de l'email du patient avant envoi
- ✅ Gestion des erreurs par rendez-vous (continue même si un échoue)
- ✅ Expiration des tâches configurée (1h pour les rappels)
- ✅ Retry automatique pour les emails échoués (max 3 tentatives)

## 📝 Logs Importants

Les logs utilisent le préfixe `[REMINDER]` pour faciliter le filtrage :

```bash
# Voir uniquement les logs de rappels
docker logs sante_celery_worker 2>&1 | grep "\[REMINDER\]"

# Exemple de sortie
[REMINDER] Checking appointments between ...
[REMINDER] Found 3 appointments to remind
[REMINDER] Sending reminder for appointment 42 | patient=john@example.com | doctor=Dr. Martin | datetime=11/11/2025 10:30
[REMINDER] Completed | sent=3 | errors=0 | total=3
```

## 🚨 Dépannage

### Beat ne démarre pas
```bash
# Vérifier le PYTHONPATH
docker exec sante_celery_beat env | grep PYTHON

# Tester l'import du module
docker exec sante_celery_beat python -c "from app.core.celery_app import celery_app; print(celery_app)"
```

### Worker ne reçoit pas les tâches
```bash
# Vérifier Redis
docker exec sante_redis redis-cli ping

# Vérifier la connexion Beat <-> Worker
docker exec sante_celery_beat celery -A app.core.celery_app inspect active
```

### Tâches ne s'exécutent pas
```bash
# Vérifier la queue dans Redis
docker exec sante_redis redis-cli llen celery

# Inspecter les tâches planifiées
docker exec sante_celery_beat celery -A app.core.celery_app inspect scheduled
```

## 📚 Références

- **Configuration Celery** : `backend/app/core/celery_app.py`
- **Tâches** : `backend/app/tasks.py`
- **Templates Email** : `backend/app/templates/email_templates.py`
- **Service Email** : `backend/app/services/email_service.py`
- **Docker Compose** : `docker-compose.yml`

## ✅ Checklist de Validation

- [x] Celery Worker actif et connecté à Redis
- [x] Celery Beat actif et planification configurée
- [x] Tâche `send_daily_appointment_reminders` fonctionne
- [x] Tâche `cleanup_expired_tokens` fonctionne
- [x] Tâche `cleanup_old_appointments` fonctionne
- [x] Template email de rappel personnalisé
- [x] Logs structurés avec préfixe `[REMINDER]`
- [x] Gestion des erreurs et retry configurés
- [x] Timezone Europe/Paris configurée
- [x] Exclusion des rendez-vous soft-deleted

---

**Status** : ✅ **Opérationnel**  
**Date de mise en production** : 10 novembre 2025  
**Prochaine exécution** : Demain à 9h00 (rappels de rendez-vous)
