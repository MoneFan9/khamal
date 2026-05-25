# Rapport de Recherche & Développement - Juin 2026
**Projet : Khamal (Self-Hosted PaaS)**
**Auteur : Directeur R&D / PM**

## 1. Audit Technique : Le Syndrome des "90%"

Après une analyse rigoureuse du noyau (`/core`), j'ai identifié plusieurs fonctionnalités critiques qui ont été implémentées mais non finalisées selon une logique de production robuste.

### A. Redondance de Configuration (Orchestration)
Le fichier `core/projects/services.py` présente une anomalie de structure : la fonction `_get_traefik_config` est définie deux fois (lignes 21 et 89). Bien que les définitions soient presque identiques, cette redondance est une source potentielle de régressions lors des mises à jour SSL ou de routing.
*   **Impact :** Dette technique, risque de comportement indéterminé selon l'ordre d'import.
*   **Statut :** Incomplet (Logic Cleanup requis).

### B. Sécurité USB (Physical Ingestion)
Le module `core/security/usb_mount.py` promet un durcissement en 4 étapes, mais l'implémentation actuelle est gravement défaillante :
1.  **Validation Absente :** La méthode `is_block_device` n'est pas implémentée, ce qui est confirmé par l'échec du test `test_mount_fails_if_not_block_device`.
2.  **Régression Critique (NameError) :** Une erreur de variable (`normalized_mount` au lieu de `mount_point`) paralyse totalement la fonctionnalité de montage, comme le démontrent les échecs des tests `test_mount_volume_success` et `test_mount_volume_failure`.
*   **Impact :** Fonctionnalité USB totalement inutilisable et faille de sécurité par manque de validation de type.
*   **Statut :** Régression majeure confirmée par la suite de tests.

### C. LogSage (IA Diagnostic)
Le moteur LogSage est fonctionnel et performant (MPPS implémenté), mais il présente des signes de divergence :
1.  **Isolation Contextuelle :** L'IA est "aveugle" aux spécificités de l'environnement de build Nixpacks.
2.  **Régression Prompt :** Le test `TestRCAPromptBuilder::test_get_system_prompt` est en échec, indiquant une modification non validée des instructions système de l'IA.
*   **Impact :** Baisse de la précision des diagnostics et risque accru d'hallucinations.
*   **Statut :** Instabilité du moteur de prompt confirmée.

---

## 2. Orientations Stratégiques et Évolutions R&D

Pour maintenir l'avance technologique de Khamal, je recommande les axes de développement suivants pour le second semestre 2026 :

### 1. LogSage "Environment-Aware" (RAG Contextuel)
L'évolution majeure consiste à injecter le plan Nixpacks (packages système, versions de langages) dans le contexte de l'IA avant l'analyse des logs.
*   **Objectif :** Zéro hallucination sur les correctifs de dépendances.

### 2. Monitoring Temps Réel & Auto-Healing
Actuellement, Khamal affiche un statut binaire (Running/Failed). Nous devons intégrer un collecteur de métriques passif (consommation CPU/RAM) et permettre à LogSage de déclencher des redémarrages automatiques avec des limites de ressources ajustées si un dépassement de quota est détecté.

### 3. mTLS Inter-Projets (Service Mesh Local)
Exploiter les capacités de Traefik v3 pour générer des certificats internes et permettre aux conteneurs de différents projets de communiquer de manière chiffrée sans exposition sur le réseau public.

### 4. Refonte UX : Dashboard Interactif
Le Dashboard actuel est une vue statique. Il doit devenir un terminal de contrôle permettant :
- Le streaming de logs en temps réel (via le `LogConsumer` existant).
- L'application des correctifs IA en un clic.
- La visualisation graphique de la topologie réseau du projet.

---

## 3. Conclusion
Le socle de Khamal est extrêmement sain et sécurisé par défaut (HardenedDockerClient). Cependant, la finalisation des détails techniques (Nettoyage Traefik, Sécurité USB) et l'intégration de l'IA dans le workflow utilisateur sont les étapes nécessaires pour passer d'un outil de déploiement à une plateforme d'orchestration intelligente de classe mondiale.

**Recommandation finale :** Validation immédiate des tickets de nettoyage pour assainir la branche `main` avant d'entamer les évolutions UX.
