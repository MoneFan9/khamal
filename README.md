# 🦁 Khamal : Self-Hosted PaaS & AI Diagnostic Orchestrator

> **"Khamal : Vos serveurs, votre intelligence, votre liberté."**

Khamal est un orchestrateur intelligent de déploiement (Self-Hosted PaaS) conçu pour transformer n'importe quelle machine physique ou VPS en une infrastructure de production complète. À l'intersection de l'orchestration Docker, de la détection de build automatique et de l'intelligence artificielle locale, Khamal élimine la friction entre le code et la mise en ligne, tout en garantissant une souveraineté totale des données.

## 🚀 Installation "Plug & Play"

Khamal est conçu pour être opérationnel immédiatement. Notre script d'installation automatise la configuration de l'environnement, la gestion des dépendances et la sécurisation du socket Docker.

```bash
# Clonez le dépôt
git clone https://github.com/your-repo/khamal.git
cd khamal

# Lancez l'installation automatique (Zero-Config)
# Ce script installe Nixpacks, configure venv, sécurise Docker et initialise Traefik.
bash scripts/install.sh
```

### Ce que fait l'installateur pour vous :
- **Vérification & Installation des prérequis** : Docker, Python 3 et installation automatique de **Nixpacks**.
- **Isolation** : Création d'un environnement virtuel Python (venv).
- **Sécurité par Design** : Déploiement automatique de `docker-socket-proxy` pour isoler l'API Docker du moteur d'orchestration.
- **Routage Intelligent** : Initialisation de Traefik v3 pour la gestion automatique des certificats SSL et du routage par projet.
- **Auto-Configuration** : Génération de clés secrètes et de chemins d'administration sécurisés (Hidden Admin).

## 📂 Structure du Projet (Open-Core)

Khamal suit un modèle **Open-Core** strict pour garantir une base saine et extensible :

- **[/core](./core) :** Le moteur open-source. Gestion des cycles de vie des conteneurs (Hardened Docker), orchestration réseau isolée, intégration Nixpacks avec auto-provisioning de DB, et moteur LogSage. **Licence Apache 2.0**.
- **[/pro](./pro) :** Extensions professionnelles. Gestion multi-nœuds (cluster), Marque Blanche (White-labeling), et intégrations SSO. **Licence Propriétaire**.

## 🧠 Intelligence de Diagnostic : LogSage

Khamal intègre **LogSage**, un moteur de diagnostic utilisant la stratégie **MPPS (Multi-Phase Prioritization Strategy)** pour l'analyse de crash via IA locale.

- **Filtrage Intelligent** : Élimine le bruit (heartbeats, healthchecks) pour maximiser la densité sémantique.
- **Analyse MPPS** : Priorise les "Anchors" (erreurs critiques) et leur contexte immédiat pour une précision accrue avec des modèles locaux (Llama 3.2, Qwen 2.5 Coder).
- **Auto-Provisioning** : Détecte et déploie automatiquement les dépendances (PostgreSQL, Redis, etc.) via Nixpacks.
- **Correctifs Actionnables** : Propose des solutions concrètes aux échecs de build ou de runtime.

## 🏗️ Architecture Technique

La pile technologique est choisie pour sa robustesse et sa facilité de contribution :

- **Backend** : Python 3.12+ / Django 6.0.
- **Build Engine** : Nixpacks (détection automatique de langage, pas de Dockerfile requis).
- **Proxy/Ingress** : Traefik v3 avec support SSL automatique.
- **Sécurité** : Isolation par réseau Docker (`bridge` par projet) et USBGuard pour les imports physiques.

## 🤝 Contribuer & Développer

Nous encourageons la communauté à enrichir le cœur de Khamal.

### Quick Start Développeur
1. Installez les dépendances : `pip install -r core/requirements.txt`
2. Configurez votre `.env` à partir de `core/.env.example`.
3. Lancez les tests pour vérifier votre environnement :
   ```bash
   export PYTHONPATH=core:.
   pytest
   ```

### Règles d'Or
- **Isolation du Core** : Le dossier `core/` ne doit **jamais** importer de modules provenant de `pro/`.
- **Tests** : Toute nouvelle fonctionnalité dans le core doit être accompagnée de tests unitaires et d'intégration.
- **Documentation** : Documentez le "Pourquoi" derrière vos choix techniques dans les docstrings.

## 📄 Licence
- `/core` est sous licence [Apache 2.0](./core/LICENSE).
- `/pro` est sous [licence commerciale propriétaire](./pro/LICENSE).
