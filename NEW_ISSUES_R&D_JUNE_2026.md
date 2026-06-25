# Tickets R&D - Khamal (Session Juin 2026)

## [ISSUE-001] LogSage : Implémentation de la Boucle de Vérification (Verification Loop)
**Type** : Feature / Intelligence
**Priorité** : Haute
**Description** :
Actuellement, LogSage propose des correctifs mais ne suit pas leur efficacité. Ce ticket vise à créer un mécanisme de "Feedback Loop".
**Sous-tâches** :
- [ ] Créer un modèle `FixApplication` pour suivre quel correctif a été appliqué à quel déploiement.
- [ ] Modifier `LogSagePreprocessor` pour comparer les motifs d'erreurs avant et après application.
- [ ] Ajouter une notification UI confirmant : "LogSage : Correctif validé avec succès".

---

## [ISSUE-002] UX : Dashboard Temps-Réel via WebSockets
**Type** : Amélioration UX
**Priorité** : Haute
**Description** :
Le dashboard principal est statique. Il doit refléter les changements de statut des conteneurs en temps réel.
**Sous-tâches** :
- [ ] Étendre `core/projects/consumers.py` pour gérer un `DashboardConsumer`.
- [ ] Utiliser les signaux Django (post_save sur Deployment) pour envoyer des mises à jour au groupe WebSocket.
- [ ] Mettre à jour `core/templates/dashboard.html` pour écouter les messages et modifier le DOM (badges de statut).

---

## [ISSUE-003] Nixpacks : Extension de l'Auto-Provisioning
**Type** : Feature
**Priorité** : Moyenne
**Description** :
Étendre la détection de `NixpacksPlan` au-delà de Postgres/Redis.
**Sous-tâches** :
- [ ] Ajouter la détection de MongoDB, S3 (Minio), et RabbitMQ dans `core/projects/nixpacks.py`.
- [ ] Mettre à jour `core/projects/services.py` pour supporter le provisionnement de ces nouveaux services.

---

## [ISSUE-004] Sécurité : Isolation Réseau "Internal" par défaut
**Type** : Sécurité
**Priorité** : Moyenne
**Description** :
Les réseaux de projet doivent être configurés en `internal: true` par défaut pour empêcher l'exfiltration de données, sauf si un accès sortant est requis.
**Sous-tâches** :
- [ ] Modifier `ensure_project_network` dans `core/projects/services.py`.
- [ ] Ajouter une option dans le modèle `Project` pour autoriser l'accès internet sortant.

---

## [ISSUE-005] Refactor : Nettoyage final des redondances Traefik
**Type** : Dette Technique
**Priorité** : Basse
**Description** :
S'assurer qu'aucune autre version de `_get_traefik_config` ne traîne dans d'autres modules (ex: tests ou utilitaires pro).
**Note** : Partiellement réalisé lors de l'audit de juin.
