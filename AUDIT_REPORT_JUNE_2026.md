# Rapport d'Audit Technique - Juin 2026 - Projet Khamal

## 1. Analyse de la PR : `feat/onboarding-revitalization-and-security-hardening`

**Statut : Corrections exigées**

### Problèmes identifiés :

1.  **Violation de l'architecture Open-Core (Bloquant)** :
    *   Le fichier `core/khamal/tests_ui.py` contient un import direct de `pro.white_label.models.WhiteLabelConfiguration`.
    *   *Rappel* : Le dossier `/core` ne doit jamais dépendre de `/pro`. Les tests UI qui vérifient des fonctionnalités propriétaires doivent être déplacés dans le dossier `/pro` correspondant ou utiliser une vérification dynamique de la présence de l'application.

2.  **Régression de la sécurité Docker (Bloquant)** :
    *   La classe `HardenedContainerCollection` dans `core/projects/docker_client.py` ne bloque pas tous les paramètres critiques identifiés dans les audits précédents.
    *   *Correction requise* : Ajouter `network_mode`, `ipc_mode`, `uts_mode` et `sysctls` à l'ensemble `forbidden_params`.

3.  **Observation sur Traefik** :
    *   La PR mentionne une migration vers Traefik v3 dans le README, mais la logique de configuration `_get_traefik_config` a été curieusement modifiée ou simplifiée dans `core/projects/services.py` sans tests de non-régression explicites sur le routage SSL.

### Points Positifs :
*   Le renforcement de `core/security/usb_mount.py` est excellent : l'utilisation de `realpath` pour résoudre les liens symboliques et la validation `is_block_device()` via `pathlib` comblent des failles critiques de l'ingestion physique.
*   L'automatisation de l'installation de Nixpacks dans `scripts/install.sh` améliore grandement l'expérience "Plug & Play".

---

**Note au Chef de Projet** :
L'agent auteur doit impérativement isoler les tests UI du core et compléter la liste de blocage Docker avant toute fusion. Le reste des modifications sur la sécurité USB et l'onboarding est validé techniquement.
