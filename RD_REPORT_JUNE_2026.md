# 🔬 Rapport de R&D Stratégique - Projet Khamal - Juin 2026

## À l'attention du Superviseur Unique
**Objet : Analyse des fonctionnalités incomplètes et propositions d'évolutions majeures.**

Monsieur,

En tant que Chef de la R&D, j'ai procédé à une analyse exhaustive de la base de code de Khamal. Voici mon constat stratégique et mes recommandations pour le cycle de développement à venir.

---

## 1. Analyse des fonctionnalités "bloquées à 90%"

Plusieurs piliers du projet sont techniquement matures en backend mais restent invisibles ou inutilisables pour l'utilisateur final.

### 🧠 LogSage : Le cerveau sans visage
Le moteur de diagnostic **LogSage** est une prouesse technique (prétraitement intelligent, RCA assisté par IA), mais il est actuellement orphelin d'interface.
- **Le problème :** L'utilisateur voit un déploiement échouer mais doit analyser les logs manuellement.
- **L'opportunité :** Intégrer un bouton "Diagnostic IA" dans la vue des logs qui déclenche l'analyse LogSage et affiche une solution structurée.

### 🏗️ Gestion de Projet : Le dashboard incomplet
Le tableau de bord actuel est une superbe coquille.
- **Le problème :** Les boutons "Nouveau Projet" et "Gérer" ne sont pas reliés à des interfaces utilisateur. Seule l'API permet ces actions.
- **L'opportunité :** Finaliser le workflow "No-Code" de création de projet (Source Git -> Détection Nixpacks -> Provisionnement DB -> Déploiement).

### 🛡️ Sécurité Hardened : Appliquée mais silencieuse
La sécurité Docker est excellente (`HardenedDockerClient`), mais aucune alerte de sécurité n'est remontée dans l'interface si une tentative de violation est bloquée.

---

## 2. Propositions d'Évolutions Majeures (R&D)

### 🛠️ LogSage Auto-fix (Actionable AI)
Ne plus se contenter de diagnostiquer. L'IA peut proposer un correctif (ex: correction d'une variable d'environnement ou d'un fichier de configuration).
- **Innovation :** Utiliser l'`Executor` déjà présent pour appliquer des modifications de fichiers validées par l'utilisateur directement depuis le dashboard.

### 📊 Monitoring Temps Réel & Télémétrie
Khamal manque de visibilité sur l'état de santé des serveurs.
- **Innovation :** Intégration d'un flux WebSocket remontant l'usage CPU/RAM des conteneurs via l'API Docker Stats.

### 🚀 Extension Nixpacks Frameworks
Actuellement, Khamal détecte bien Postgres et Redis.
- **Innovation :** Étendre le `NixpacksPlan` pour supporter nativement des frameworks comme **SvelteKit**, **Go**, et **Rust** avec des optimisations de build spécifiques et un provisionnement automatique de volumes persistants.

---

## 3. Recommandations Stratégiques

Pour transformer Khamal en leader du Self-Hosted PaaS, je recommande de prioriser les trois axes suivants dans l'ordre :

1.  **Visibilité LogSage :** Rendre l'IA tangible. C'est notre principal différenciateur.
2.  **Workflow End-to-End :** Permettre à un utilisateur de déployer une app Git sans ouvrir un terminal ou un outil API.
3.  **Observabilité :** Un dashboard qui vit. Sans métriques, l'utilisateur se sent aveugle.

J'ai préparé les tickets (Issues) correspondants dans le répertoire `core/proposed_issues/` pour validation.

**Directeur R&D, Khamal**
