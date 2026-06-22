# Audit Technique Khamal - Juin 2026

## 1. Violations d'Architecture (Open-Core)
*   **Import Pro dans le Core** : Le fichier `core/khamal/tests_ui.py` importait directement `pro.white_label.models`.
    *   *Correction* : Le fichier de test a été déplacé vers `pro/white_label/tests_ui_integration.py` pour respecter l'isolation stricte entre le code public et propriétaire.

## 2. Régressions de Sécurité Systémique
*   **Exposition du Socket Docker** : La configuration de Traefik dans `core/projects/services.py` montait directement `/var/run/docker.sock`.
    *   *Correction* : Suppression du montage direct. Traefik communique désormais exclusivement via `docker-socket-proxy`.
*   **Contournement de la Politique de Sécurité Docker** : Le client `HardenedDockerClient` ne vérifiait pas les montages de volumes sensibles et était vulnérable aux contournements par chemins non-normalisés.
    *   *Correction* : Implémentation d'une vérification récursive et robuste des volumes dans `core/projects/docker_client.py`. Utilisation de `os.path.realpath` pour la normalisation et blocage strict des montages de répertoires parents ou sous-répertoires de chemins sensibles (ex: blocage de `/etc` car il contient `/etc/shadow`). Support ajouté pour les objets `docker.types.Mount`.
*   **Paramètres Docker Interdits** : Absence de blocage pour `network_mode`, `ipc_mode`, `uts_mode`, et `sysctls`.
    *   *Correction* : Ajout de ces paramètres à la liste `forbidden_params`.

## 3. Erreurs Logiques et Qualité de Code
*   **NameError dans `usb_mount.py`** : Utilisation d'une variable `normalized_mount` non définie dans `mount_volume`.
    *   *Correction* : Correction de la logique pour capturer et utiliser systématiquement `normalized_mount` retourné par `_validate_paths`.
*   **Vulnérabilité Symlink** : Utilisation de `os.path.normpath` au lieu de `os.path.realpath`.
    *   *Correction* : Remplacement par `os.path.realpath` pour garantir une résolution robuste des chemins physiques.
*   **Redondance de Code** : Double définition de `_get_traefik_config` dans `core/projects/services.py`.
    *   *Correction* : Consolidation en une seule implémentation sécurisée.
*   **Régression RCAPromptBuilder** : Suppression par erreur de la méthode `get_system_prompt`.
    *   *Correction* : Restauration de la méthode pour maintenir la compatibilité.

## 4. Gestion des Dépendances
*   **Versions non épinglées** : Les dépendances dans `core/requirements.txt` utilisaient des versions flottantes.
    *   *Correction* : Épinglage strict de toutes les dépendances selon les standards de Juin 2026 (ex: `Django==6.0.6`).

---
**Rapport établi par : Tech Lead Khamal (Jules)**
**Date : Juin 2026**
**Statut : VALIDÉ**
