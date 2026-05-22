# 🦁 Khamal : Self-Hosted PaaS & AI Diagnostic Orchestrator

> **"Khamal : Vos serveurs, votre intelligence, votre liberté."**

Khamal est un orchestrateur intelligent de déploiement (Self-Hosted PaaS) conçu pour transformer n'importe quelle machine physique ou VPS en une infrastructure de production complète. À l'intersection de l'orchestration Docker, de la détection de build automatique et de l'intelligence artificielle locale, Khamal élimine la friction entre le code et la mise en ligne, tout en garantissant une souveraineté totale des données.

## 🚀 Installation "Plug & Play" (Zero-Config)

Khamal est conçu pour être opérationnel en quelques secondes. Notre script d'installation automatise la configuration de l'environnement, la gestion des dépendances et la sécurisation du système.

```bash
# Clonez le dépôt
git clone https://github.com/your-repo/khamal.git
cd khamal

# Lancez l'installation automatique
# Ce script gère le venv, les dépendances, le proxy Docker et Traefik.
bash scripts/install.sh
```

### Ce que fait l'installateur pour vous :
- **Vérification des prérequis** : Docker, Python 3, Git, Curl et Nixpacks.
- **Isolation** : Création d'un environnement virtuel Python (venv) et génération de clés secrètes.
- **Sécurité "Hardened"** : Déploiement d'un `docker-socket-proxy` pour isoler l'accès à l'API Docker et configuration d'URL d'administration masquées.
- **Routage Intelligent** : Initialisation de Traefik v3 pour la gestion automatique des certificats SSL (Let's Encrypt).
- **IA Ready** : Vérification de la connectivité avec Ollama pour activer LogSage.

## 📂 Structure du Projet (Open-Core)

Khamal suit un modèle **Open-Core** strict pour garantir une base saine et extensible :

- **[/core](./core) :** Le moteur open-source (Apache 2.0). Gestion des cycles de vie des conteneurs, orchestration réseau isolée, intégration Nixpacks, et moteur LogSage.
- **[/pro](./pro) :** Extensions professionnelles (Propriétaire). Gestion multi-nœuds, Marque Blanche, et intégrations SSO.

## 🧠 Intelligence de Diagnostic : LogSage

L'une des innovations majeures de Khamal est **LogSage**, un moteur de diagnostic basé sur l'IA locale (Llama 3.2 / Qwen 2.5 Coder via Ollama).

- **Multi-Phase Prioritization Strategy (MPPS)** : Réduit le bruit des logs en identifiant les "anchors" (erreurs critiques) et leur contexte immédiat.
- **Analyse de Crash** : Identifie la cause racine d'un échec de déploiement (dépendances manquantes, erreurs de syntaxe, conflits de ports).
- **Correctifs Applicables** : Génère des suggestions de code directement actionnables.

## 🏗️ Architecture & Sécurité

La sécurité n'est pas une option dans Khamal, elle est intégrée au cœur de l'architecture :

- **Isolation Réseau** : Chaque projet dispose de son propre réseau `bridge` isolé. Aucune communication inter-projet n'est possible par défaut.
- **Hardened Docker Client** : Un proxy interne bloque l'utilisation de paramètres dangereux comme `--privileged` ou `cap_add`.
- **Physical Ingestion** : Le montage de clés USB est sécurisé par **USBGuard** et des options de montage restrictives (`noexec`, `nosuid`, `nodev`).
- **Logique Stateless** : L'orchestrateur est conçu pour être résilient aux redémarrages, avec une persistance des configurations de base de données.

## 🤝 Contribuer & Développer

Nous encourageons la communauté à enrichir le cœur de Khamal.

### Quick Start Développeur
1. Installez les dépendances : `pip install -r core/requirements.txt`
2. Configurez votre `.env` à partir de `core/.env.example`.
3. Lancez la suite de tests complète :
   ```bash
   export PYTHONPATH=core:pro:.
   DJANGO_SETTINGS_MODULE=khamal.settings.development pytest
   ```

### Règles d'Or du Contributeur
- **Open-Core Strict** : Le dossier `core/` ne doit **jamais** importer de modules provenant de `pro/`.
- **Security First** : Toute modification touchant au déploiement doit respecter les contraintes du `HardenedDockerClient`.
- **Test-Driven** : Les nouvelles fonctionnalités doivent atteindre une couverture de tests proche de 100%.
- **Clarté** : Documentez le "Pourquoi" (le raisonnement architectural) autant que le "Comment".

## 📄 Licence
- `/core` est sous licence [Apache 2.0](./core/LICENSE).
- `/pro` est sous [licence commerciale propriétaire](./pro/LICENSE).
