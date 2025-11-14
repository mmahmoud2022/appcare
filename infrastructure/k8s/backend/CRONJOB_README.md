# CronJob - Mise à jour des statistiques des docteurs

## Description

Ce CronJob Kubernetes exécute automatiquement le script `update_doctor_statistics.py` qui recalcule les statistiques des docteurs (note moyenne et nombre total d'avis) à partir des données de la base de données.

## Configuration

### Planification
- **Fréquence** : Tous les jours à 2h00 du matin (UTC)
- **Cron expression** : `0 2 * * *`

### Ressources
- **Mémoire** : 256Mi (request) / 512Mi (limit)
- **CPU** : 100m (request) / 500m (limit)
- **Timeout** : 1 heure maximum

### Politique d'exécution
- **concurrencyPolicy** : `Forbid` - empêche l'exécution simultanée de plusieurs jobs
- **successfulJobsHistoryLimit** : 3 - conserve les 3 derniers jobs réussis
- **failedJobsHistoryLimit** : 3 - conserve les 3 derniers jobs échoués
- **backoffLimit** : 3 - nombre maximum de tentatives en cas d'échec

## Déploiement

### Déploiement automatique
Le CronJob est déployé automatiquement via le script `deploy.sh` :

```bash
./infrastructure/scripts/deploy.sh
```

### Déploiement manuel
```bash
kubectl apply -f infrastructure/k8s/backend/cronjob-update-stats.yaml
```

## Gestion du CronJob

### Vérifier le statut
```bash
# Lister les CronJobs
kubectl get cronjobs -n sante

# Voir les détails du CronJob
kubectl describe cronjob update-doctor-statistics -n sante

# Lister les jobs créés par le CronJob
kubectl get jobs -n sante -l job=update-doctor-statistics

# Voir l'historique des exécutions
kubectl get pods -n sante -l job=update-doctor-statistics
```

### Voir les logs
```bash
# Logs du dernier job exécuté
kubectl logs -n sante -l job=update-doctor-statistics --tail=100

# Logs d'un job spécifique
kubectl logs -n sante job/update-doctor-statistics-<timestamp>
```

### Exécution manuelle (test)
Pour tester le CronJob sans attendre la prochaine exécution planifiée :

```bash
# Créer un job immédiat depuis le CronJob
kubectl create job --from=cronjob/update-doctor-statistics test-update-stats -n sante

# Voir les logs du job de test
kubectl logs -n sante job/test-update-stats -f

# Supprimer le job de test après vérification
kubectl delete job test-update-stats -n sante
```

### Suspendre le CronJob
Pour suspendre temporairement les exécutions automatiques :

```bash
kubectl patch cronjob update-doctor-statistics -n sante -p '{"spec":{"suspend":true}}'
```

### Réactiver le CronJob
```bash
kubectl patch cronjob update-doctor-statistics -n sante -p '{"spec":{"suspend":false}}'
```

### Modifier la planification
Pour changer la fréquence d'exécution, éditez le fichier `cronjob-update-stats.yaml` et modifiez la ligne `schedule` :

```yaml
# Exemples de planifications :
# Toutes les heures : "0 * * * *"
# Tous les jours à minuit : "0 0 * * *"
# Toutes les 6 heures : "0 */6 * * *"
# Tous les lundis à 3h : "0 3 * * 1"
# Le 1er de chaque mois : "0 0 1 * *"
```

Puis appliquez les changements :
```bash
kubectl apply -f infrastructure/k8s/backend/cronjob-update-stats.yaml
```

## Monitoring

### Alertes recommandées
- Job échoué 3 fois consécutives
- Job dépasse 30 minutes d'exécution
- Aucune exécution depuis 25 heures

### Métriques
Utilisez Prometheus/Grafana pour monitorer :
- `kube_cronjob_status_active` - Nombre de jobs actifs
- `kube_cronjob_status_last_schedule_time` - Timestamp de la dernière exécution
- `kube_job_status_succeeded` - Nombre de jobs réussis
- `kube_job_status_failed` - Nombre de jobs échoués

## Troubleshooting

### Le CronJob ne s'exécute pas
1. Vérifier que le CronJob n'est pas suspendu :
   ```bash
   kubectl get cronjob update-doctor-statistics -n sante -o yaml | grep suspend
   ```

2. Vérifier les events :
   ```bash
   kubectl get events -n sante --sort-by='.lastTimestamp' | grep update-doctor-statistics
   ```

### Le job échoue
1. Consulter les logs :
   ```bash
   kubectl logs -n sante -l job=update-doctor-statistics --tail=200
   ```

2. Vérifier les secrets et configmaps :
   ```bash
   kubectl get secrets backend-secrets -n sante
   kubectl get configmap backend-config -n sante
   ```

3. Vérifier la connexion à la base de données :
   ```bash
   kubectl exec -it deployment/backend -n sante -- python -c "from app.core.database import get_db; next(get_db()); print('✅ DB connection OK')"
   ```

### Tester localement
Pour tester le script en local avant déploiement :

```bash
# Via Docker Compose
docker compose exec backend python update_doctor_statistics.py

# Via Kubernetes (dans le pod backend)
kubectl exec -it deployment/backend -n sante -- python update_doctor_statistics.py
```

## Maintenance

### Nettoyage de l'historique
Pour supprimer tous les anciens jobs :

```bash
# Supprimer les jobs terminés depuis plus de 7 jours
kubectl delete job -n sante -l job=update-doctor-statistics --field-selector=status.successful=1

# Supprimer manuellement un job spécifique
kubectl delete job update-doctor-statistics-<timestamp> -n sante
```

### Mise à jour du script Python
1. Modifier le fichier `backend/update_doctor_statistics.py`
2. Reconstruire l'image Docker backend
3. Redéployer le backend :
   ```bash
   kubectl rollout restart deployment/backend -n sante
   ```
4. Le CronJob utilisera automatiquement la nouvelle version lors de la prochaine exécution

## Sécurité

### Permissions
Le CronJob utilise un ServiceAccount dédié avec des permissions minimales :
- Lecture des ConfigMaps
- Lecture des Secrets
- Aucun accès aux autres ressources du cluster

### Variables sensibles
Les mots de passe et secrets sont injectés via Kubernetes Secrets et ne sont jamais stockés en clair dans le code.

## Performance

### Optimisation
- Le job utilise une connexion poolée à la base de données
- Les requêtes sont optimisées avec des index sur les colonnes utilisées
- La durée d'exécution devrait être < 5 minutes pour 10 000 docteurs

### Dimensionnement
Si vous avez plus de 100 000 docteurs, considérez :
- Augmenter les limites de ressources (mémoire/CPU)
- Augmenter le timeout (`activeDeadlineSeconds`)
- Paralléliser le traitement par batch

## Références

- [Kubernetes CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Cron syntax](https://crontab.guru/)
- Script source : `backend/update_doctor_statistics.py`
