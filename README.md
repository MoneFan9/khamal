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
bash scripts/install.sh
```

### Ce que fait l'installateur pour vous :
- **Vérification des prérequis** : Docker, Python 3, Nixpacks et USBGuard.
- **Isolation** : Création d'un environnement virtuel Python (venv).
- **Sécurité** : Déploiement d'un `docker-socket-proxy` pour isoler l'accès à l'API Docker.
- **Routage** : Initialisation de Traefik pour la gestion automatique des certificats SSL (Let's Encrypt).
- **Prêt pour l'IA** : Configuration des points de terminaison pour Ollama.

## 📂 Structure du Projet (Open-Core)

Khamal suit un modèle **Open-Core** strict pour garantir une base saine et extensible :

- **[/core](./core) :** Le moteur open-source. Gestion des cycles de vie des conteneurs, orchestration réseau isolée, intégration Nixpacks, et moteur LogSage. **Licence Apache 2.0**.
- **[/pro](./pro) :** Extensions professionnelles. Gestion multi-nœuds (cluster), Marque Blanche (White-labeling), et intégrations SSO. **Licence Propriétaire**.

## 🛡️ Sécurité par Design (Hardened)

Khamal n'est pas seulement un PaaS, c'est une forteresse pour vos déploiements :

- **Hardened Docker Client** : Chaque appel à l'API Docker est filtré par un proxy interne qui interdit les paramètres dangereux (`privileged`, `cap_add`, etc.).
- **Isolation Réseau** : Chaque projet dispose de son propre réseau `bridge` isolé. La communication inter-projet est bloquée par défaut.
- **Physical Guard** : L'ingestion via USB est protégée par **USBGuard** et un protocole de montage en 4 étapes (noexec, nosuid, nodev).
- **Socket Proxy** : Khamal ne manipule jamais directement `/var/run/docker.sock`. Il communique via un proxy applicatif sécurisé.

## 🧠 Intelligence de Diagnostic : LogSage

L'une des innovations majeures de Khamal est **LogSage**, un moteur de diagnostic basé sur l'IA locale (Llama 3.2 / Qwen 2.5 Coder via Ollama).

- **Réduction de Bruit** : Filtre intelligemment les logs non pertinents pour ne garder que le contexte critique.
- **Analyse de Crash** : Identifie la cause racine d'un échec de déploiement.
- **Correctifs Applicables** : Génère des suggestions de code directement applicables pour corriger les erreurs de configuration ou de dépendances.

## 🏗️ Architecture Technique

La pile technologique est choisie pour sa robustesse et sa facilité de contribution :

- **Backend** : Python 3.12+ / Django 6.0.
- **Build Engine** : Nixpacks (détection automatique de langage, pas de Dockerfile requis).
- **Proxy/Ingress** : Traefik v3 avec support SSL automatique.
- **Sécurité** : Hardened Docker Client, Isolation `bridge` par projet, et USBGuard.

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
- **Isolation du Core (Open-Core)** : Le dossier `core/` ne doit **jamais** importer de modules provenant de `pro/`. Utilisez le chargement dynamique si nécessaire.
- **Sécurité First** : Ne contournez jamais le `HardenedDockerClient`. Toute modification touchant à l'orchestration doit respecter la politique "No-Escalation".
- **Tests** : Toute nouvelle fonctionnalité dans le core doit être accompagnée de tests unitaires et d'intégration.
- **Documentation** : Documentez le "Pourquoi" derrière vos choix techniques dans les docstrings (Architectural Notes).

## 📄 Licence
- `/core` est sous licence [Apache 2.0](./core/LICENSE).
- `/pro` est sous [licence commerciale propriétaire](./pro/LICENSE).
