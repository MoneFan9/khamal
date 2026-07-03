# 🦁 Khamal : Self-Hosted PaaS & AI Diagnostic Orchestrator

> **"Khamal : Vos serveurs, votre intelligence, votre liberté."**

Khamal est un orchestrateur intelligent de déploiement (Self-Hosted PaaS) conçu pour transformer n'importe quelle machine physique ou VPS en une infrastructure de production complète. À l'intersection de l'orchestration Docker, de la détection de build automatique et de l'intelligence artificielle locale, Khamal élimine la friction entre le code et la mise en ligne, tout en garantissant une souveraineté totale des données.

## 🚀 Installation "Plug & Play"

Khamal est conçu pour être opérationnel immédiatement. Notre script d'installation automatise la configuration de l'environnement, la gestion des dépendances et la sécurisation du socket Docker.

```bash
# Installation "One-Liner" (Zero-Config)
curl -sSL https://raw.githubusercontent.com/khamal-paas/khamal/main/scripts/install.sh | bash
```

### Ce que fait l'installateur pour vous :
- **Vérification des prérequis** : Docker, Python 3 et Nixpacks.
- **Isolation** : Création d'un environnement virtuel Python (venv).
- **Sécurité** : Déploiement d'un `docker-socket-proxy` pour isoler l'accès à l'API Docker.
- **Routage** : Initialisation de Traefik pour la gestion automatique des certificats SSL (Let's Encrypt).
- **Prêt pour l'IA** : Configuration des points de terminaison pour Ollama.

## 📂 Structure du Projet (Open-Core)

Khamal suit un modèle **Open-Core** strict pour garantir une base saine et extensible :

- **[/core](./core) :** Le moteur open-source. Gestion des cycles de vie des conteneurs, orchestration réseau isolée, intégration Nixpacks, et moteur LogSage. **Licence Apache 2.0**.
- **[/pro](./pro) :** Extensions professionnelles. Gestion multi-nœuds (cluster), Marque Blanche (White-labeling), et intégrations SSO. **Licence Propriétaire**.

## 🧠 Intelligence de Diagnostic : LogSage

L'une des innovations majeures de Khamal est **LogSage**, un moteur de diagnostic basé sur l'IA locale (Llama 3.2 / Qwen 2.5 Coder via Ollama).

- **Réduction de Bruit** : Filtre intelligemment les logs non pertinents pour ne garder que le contexte critique.
- **Analyse de Crash** : Identifie la cause racine d'un échec de déploiement.
- **Correctifs Applicables** : Génère des suggestions de code directement applicables pour corriger les erreurs de configuration ou de dépendances.

## 🏗️ Architecture Technique

Khamal repose sur une architecture modulaire et sécurisée, conçue pour la haute disponibilité et la simplicité de gestion.

### 🛣️ Routage & Ingress (Traefik)
Khamal utilise un conteneur **Traefik v3** global comme point d'entrée unique. Il gère dynamiquement le routage vers les conteneurs applicatifs via des labels Docker et automatise l'obtention de certificats SSL via Let's Encrypt.

### 🛡️ Isolation Réseau
Chaque projet Khamal est déployé dans son propre **réseau bridge Docker isolé**. Les conteneurs d'un projet peuvent communiquer entre eux (ex: App <-> DB) mais sont isolés des autres projets. Seul le proxy Traefik a accès aux réseaux applicatifs pour le routage externe.

### 🧠 LogSage : Diagnostic par IA
Le moteur **LogSage** traite les flux de logs en trois phases (Anchors, Context, Quota) pour extraire la substance critique d'un crash. Ces informations sont ensuite injectées dans un modèle de langage local via **Ollama** pour générer une Analyse de Cause Racine (RCA) et des correctifs de code.

### 📦 Build Engine (Nixpacks)
Nous utilisons **Nixpacks** pour transformer le code source en images Docker optimisées sans nécessiter de Dockerfile. Il détecte automatiquement le langage, installe les dépendances et configure le processus de démarrage.

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
- **Technical Docstrings** : Nous exigeons une documentation rigoureuse. Chaque classe et fonction complexe doit avoir une docstring expliquant non seulement **comment** elle fonctionne, mais surtout **pourquoi** cette approche a été choisie (contexte architectural, contraintes de sécurité).

## 📄 Licence
- `/core` est sous licence [Apache 2.0](./core/LICENSE).
- `/pro` est sous [licence commerciale propriétaire](./pro/LICENSE).
