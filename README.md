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
- **Vérification des prérequis** : Docker, Python 3 et Nixpacks.
- **Isolation** : Création d'un environnement virtuel Python (venv).
- **Sécurité** : Déploiement d'un `docker-socket-proxy` pour isoler l'accès à l'API Docker.
- **Routage** : Initialisation de Traefik pour la gestion automatique des certificats SSL (Let's Encrypt).
- **Prêt pour l'IA** : Configuration des points de terminaison pour Ollama avec optimisation de la latence (`OLLAMA_KEEP_ALIVE`).

## 🛡️ Sécurité Systémique & Isolation

Khamal est conçu avec une approche "Security by Design" pour protéger l'hôte :
- **Hardened Docker Client** : Un wrapper sécurisé qui intercepte les appels API Docker pour interdire les conteneurs privilégiés ou les escalades de capacités (`cap_add`).
- **Docker Socket Proxy** : Khamal ne communique jamais directement avec `/var/run/docker.sock`. Il utilise un proxy agissant comme un pare-feu applicatif.
- **Isolation Réseau** : Chaque projet dispose de son propre réseau bridge isolé. Seul le trafic web est routé via Traefik.
- **Physical Ingestion Security** : L'importation via USB est protégée par **USBGuard** et des options de montage strictes (`noexec`, `nosuid`, `nodev`).

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
- **Isolation du Core** : Le dossier `core/` ne doit **jamais** importer de modules provenant de `pro/`. Utilisez l'injection de dépendances si nécessaire.
- **Security First** : Toute modification touchant à l'orchestration Docker doit passer par le `HardenedDockerClient`.
- **Tests** : Toute nouvelle fonctionnalité dans le core doit être accompagnée de tests unitaires et d'intégration. Couverture cible : 100% sur les modules critiques.
- **Documentation** : Documentez le "Pourquoi" derrière vos choix techniques dans les docstrings.

## 🤝 Participer à l'aventure

Nous croyons en une infrastructure souveraine et accessible. Que vous soyez expert Docker, développeur Python ou passionné d'IA, vos contributions sont les bienvenues. Consultez notre [Guide de Contribution](./CONTRIBUTING.md) (à venir) ou ouvrez une Issue pour discuter d'une amélioration.

## 📄 Licence
- `/core` est sous licence [Apache 2.0](./core/LICENSE).
- `/pro` est sous [licence commerciale propriétaire](./pro/LICENSE).
