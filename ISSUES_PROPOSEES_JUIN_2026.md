# Tickets Proposés - Juin 2026

## [CORE] #001 - Unification de la configuration Traefik
**Type :** Refactor / Bug (Potential)
**Priorité :** Haute
**Description :**
Le fichier `core/projects/services.py` contient deux définitions de la fonction `_get_traefik_config` (aux lignes 21 et 89). Cela viole le principe DRY (Don't Repeat Yourself) et peut causer des comportements imprévisibles.
**Tâches :**
- Supprimer la définition redondante à la ligne 89.
- Vérifier que la définition à la ligne 21 gère correctement les volumes et les certificats SSL.
- S'assurer que tous les appels dans `ensure_global_proxy` et `create_deployment_container` utilisent la fonction unifiée.

---

## [SECURITY] #002 - Correction des régressions et validation USB
**Type :** Bug / Security
**Priorité :** Critique
**Description :**
Le `USBMountManager` souffre de régressions bloquantes (NameError) et d'une absence de validation des types de périphériques.
**Tâches :**
- Corriger la `NameError` dans `core/security/usb_mount.py` (remplacer `normalized_mount` par `mount_point` dans les blocs de création de répertoire et de montage, ou inversement harmoniser les variables).
- Implémenter une méthode `is_block_device(device_path)` dans `core/security/usb_mount.py` (via `pathlib.Path.is_block_device`).
- Ajouter cet appel au début de `mount_volume`.
- Lever une erreur explicite si le fichier n'est pas un périphérique de stockage.

---

## [AI/UX] #003 - Application des correctifs LogSage en un clic
**Type :** Feature
**Priorité :** Moyenne
**Description :**
Le moteur LogSage peut générer des correctifs via `apply_fix`. Cette intelligence n'est pas accessible via l'interface web.
**Tâches :**
- Ajouter un endpoint API pour exposer la fonctionnalité `apply_fix`.
- Modifier `dashboard.html` pour afficher un bouton "Appliquer le correctif suggéré" lorsqu'un diagnostic LogSage est disponible.
- Intégrer un feedback visuel lors de l'application réussie d'un correctif.

---

## [MONITORING] #004 - Flux de métriques temps réel Docker
**Type :** Feature / Performance
**Priorité :** Moyenne
**Description :**
Les utilisateurs ont besoin de voir la consommation de leurs conteneurs en temps réel sans utiliser `docker stats` en ligne de commande.
**Tâches :**
- Créer un `MetricConsumer` (sur le modèle de `LogConsumer`) utilisant `container.stats(stream=True)`.
- Diffuser les données (CPU %, RAM MB, Network) via WebSocket.
- Préparer l'interface Dashboard pour afficher ces graphiques légers.
