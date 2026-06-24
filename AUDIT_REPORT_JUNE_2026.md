# Rapport d'Audit Technique - Projet Khamal (Juin 2026)

## 1. Violations de l'Architecture Open-Core
- **Fichier :** `core/khamal/tests_ui.py`
- **Problème :** Importation directe de `pro.white_label.models.WhiteLabelConfiguration`. Le code dans `/core` ne doit jamais dépendre du code dans `/pro`.
- **Action corrective :** Déplacer les tests d'intégration dépendants de Pro vers `/pro`.

## 2. Risques de Sécurité Systémique
- **Fichier :** `core/projects/services.py`
- **Problème :** Montage direct du socket Docker (`/var/run/docker.sock`) dans le conteneur Traefik. Cela expose l'hôte et contourne le `HardenedDockerClient`.
- **Action corrective :** Utiliser le proxy Docker sécurisé (`tcp://docker-socket-proxy:2375`) et supprimer le montage du volume.

## 3. Erreurs Logiques et Redondance
- **Fichier :** `core/projects/services.py`
- **Problème :** Double définition de la fonction `_get_traefik_config`.
- **Action corrective :** Consolider en une seule implémentation robuste.
- **Fichier :** `core/security/usb_mount.py`
- **Problème :** Utilisation de la variable non définie `normalized_mount` au lieu de `mount_point` dans la méthode `mount_volume` (NameError).
- **Action corrective :** Corriger le nom de la variable.

## 4. Régressions d'Interface
- **Fichier :** `core/ai/rag.py`
- **Problème :** La méthode `get_system_prompt()` est absente de la classe `RCAPromptBuilder`, cassant la compatibilité avec certains composants.
- **Action corrective :** Restaurer la méthode `get_system_prompt()`.

## 5. Renforcement de la Sécurité USB
- **Fichier :** `core/security/usb_mount.py`
- **Problème :** Absence de vérification que le chemin du périphérique est bien un "block device".
- **Action corrective :** Ajouter `Path(device_path).is_block_device()`.
