# Audit Disaster Recovery (DR) - Project Khamal

## 1. État des lieux de la persistance

L'audit de la logique de provisionnement des bases de données (`core/projects/services.py`) a révélé des lacunes critiques pour la reprise d'activité :

- **Éphémérité des identifiants** : La fonction `provision_database` génère des mots de passe aléatoires via `secrets.token_urlsafe(16)` mais ne les persiste dans aucun modèle Django. En cas de redémarrage ou de besoin de maintenance, les identifiants sont perdus pour l'orchestrateur.
- **Absence de mécanisme de sauvegarde** : Aucune routine de sauvegarde (automatisée ou manuelle) n'est implémentée pour PostgreSQL ou Redis.
- **Absence de logique de restauration** : Il n'existe aucun moyen de restaurer un volume de données ou un dump SQL dans une instance provisionnée.
- **Redondance architecturale** : La présence de deux définitions identiques de `_get_traefik_config` dans `core/projects/services.py` témoigne d'un besoin de nettoyage technique.

## 2. Plan d'amélioration proposé

Pour garantir l'intégrité des données utilisateur sur le PaaS Khamal, les évolutions suivantes sont nécessaires :

1.  **Persistance des instances** : Introduction du modèle `DatabaseInstance` pour stocker les types de moteurs, les noms de conteneurs et les identifiants de connexion.
2.  **Traçabilité des sauvegardes** : Introduction du modèle `Backup` pour suivre l'état, le chemin et la date des instantanés de données.
3.  **Automatisation DR** : Implémentation de fonctions `backup_database` et `restore_database` utilisant le streaming Docker pour éviter les saturations mémoire (OOM).
4.  **CLI de gestion** : Création de la commande `dr_manager` pour orchestrer les tests de restauration en isolation.

---
*Rapport généré par l'Ingénieur Infrastructure DR - Juin 2026*
