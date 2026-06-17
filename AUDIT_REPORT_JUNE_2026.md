# Rapport d'Audit Technique Khamal - Juin 2026
**Directeur Technique (Tech Lead)**

## Résumé Exécutif
L'audit du code actuel révèle plusieurs violations critiques des standards architecturaux et de sécurité du projet Khamal. Des régressions majeures ont été introduites dans les modules de déploiement Docker et de gestion USB, ainsi qu'une rupture de l'isolation Open-Core. De plus, une partie significative de la suite de tests de couverture a disparu.

**Statut : REJETÉ. Corrections obligatoires requises.**

---

## 1. Architecture Open-Core & Découplage
- **Violation Critique :** Le fichier `core/khamal/tests_ui.py` importe directement `pro.white_label.models.WhiteLabelConfiguration`.
- **Correction Requise :** Migrer tous les tests dépendant de modèles `/pro` vers le dossier correspondant dans `/pro` (ex: `pro/white_label/tests_ui.py`). Le `/core` ne doit avoir aucune connaissance du code propriétaire.

## 2. Sécurité Systémique & Durcissement Docker
- **Régressions Docker (`core/projects/docker_client.py`) :**
    - Les paramètres `network_mode`, `ipc_mode`, `uts_mode`, et `sysctls` sont absents de la liste `forbidden_params`, permettant un contournement potentiel de l'isolation du conteneur.
    - La classe `HardenedContainerCollection` utilise `__getattribute__` pour le proxying, ce qui est risqué. Elle doit utiliser `__getattr__` pour une interception propre.
- **Régressions USB (`core/security/usb_mount.py`) :**
    - Absence de `os.path.realpath` dans la validation des chemins, rendant le système vulnérable aux attaques par liens symboliques.
    - Absence de vérification de périphérique bloc (`is_block_device()`) avant les appels à USBGuard.
- **Corrections Requises :** Compléter la liste des paramètres interdits et sécuriser la résolution des chemins USB.

## 3. Intégrité Logique & Bugs
- **Bug USB :** Une erreur `NameError` est présente dans `mount_volume` (utilisation de `normalized_mount` avant sa définition ou hors scope en cas d'erreur).
- **Dette Technique :**
    - Le fichier `core/projects/services.py` contient deux définitions redondantes de `_get_traefik_config`. Elles doivent être consolidées.
    - Le modèle `Server` dans `pro/servers/models.py` manque de validateurs au niveau du modèle pour `ssh_port` (1-65535), déléguant cette responsabilité au sérialiseur uniquement.
- **Corrections Requises :** Supprimer le code redondant, corriger les variables et déplacer la validation des ports au niveau du modèle.

## 4. Assurance Qualité & Couverture
- **Fichiers Manquants :** Les fichiers de tests suivants, essentiels pour atteindre les 99% de couverture cibles, sont absents du dépôt :
    - `core/security/tests_coverage_boost.py`
    - `core/projects/tests_services_ssl.py`
    - `core/projects/tests_api_coverage.py`
    - `core/projects/tests_nixpacks_extra.py`
    - `core/ai/tests_client.py`
    - `core/ai/tests_executor.py`
    - `core/ai/tests_chaos_real.py`
- **Correction Requise :** Restaurer ou réimplémenter l'intégralité de la suite de tests de couverture et de sécurité.

---

## Conclusion
Le code ne peut pas être validé en l'état. Les agents auteurs doivent soumettre une nouvelle version corrigeant ces points de manière prioritaire pour maintenir la stabilité et la sécurité de l'orchestrateur.

**Directeur Technique Khamal**
