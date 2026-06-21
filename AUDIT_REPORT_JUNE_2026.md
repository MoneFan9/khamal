# Rapport d'Audit Technique - Juin 2026

## 1. Violations de l'Architecture Open-Core
- **Fichier** : `core/khamal/tests_ui.py`
- **Problème** : Le fichier de test contient un import de `pro.white_label.models`. Le code public (`/core`) ne doit jamais dépendre du code propriétaire (`/pro`).
- **Action requise** : Déplacer les tests liés à la marque blanche (White Label) vers `pro/white_label/tests_ui.py`.

## 2. Régressions de Sécurité Systémique
### 2.1. Durcissement Docker
- **Fichier** : `core/projects/docker_client.py`
- **Problème** : Plusieurs paramètres critiques permettant des évasions vers l'hôte ne sont pas bloqués dans `forbidden_params`.
- **Paramètres manquants** : `network_mode`, `ipc_mode`, `uts_mode`, `sysctls`.
- **Action requise** : Ajouter ces paramètres à la liste `forbidden_params` dans `HardenedContainerCollection`.

### 2.2. Montage USB (Physical Vector)
- **Fichier** : `core/security/usb_mount.py`
- **Problème 1 (Erreur Logique)** : Utilisation de la variable non définie `normalized_mount` dans la méthode `mount_volume`, provoquant une `NameError`.
- **Problème 2 (Sécurité)** : Absence de vérification fondamentale si le chemin est un périphérique bloc (`Path.is_block_device()`) avant l'appel à USBGuard.
- **Action requise** : Corriger la variable et ajouter la vérification du périphérique bloc.

## 3. Qualité du Code et Maintenance
### 3.1. Redondance (DRY)
- **Fichier** : `core/projects/services.py`
- **Problème** : La fonction `_get_traefik_config` est définie deux fois de manière identique.
- **Action requise** : Supprimer la définition redondante.

### 3.2. Gestion des Dépendances
- **Fichier** : `core/requirements.txt`
- **Problème** : Les versions sont épinglées de manière lâche (`>=`). Cela peut introduire des instabilités ou des vulnérabilités.
- **Action requise** : Utiliser un épinglage strict (`==`) pour toutes les dépendances (ex: `Django==6.0.6`).

## Conclusion
Le code actuel présente des risques de sécurité et des violations architecturales majeures. Une correction immédiate est exigée avant toute fusion.
