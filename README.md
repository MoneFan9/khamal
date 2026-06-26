# 🦁 Khamal : Self-Hosted PaaS & AI Diagnostic Orchestrator

> **"Khamal : Vos serveurs, votre intelligence, votre liberté."**

Khamal est un orchestrateur intelligent de déploiement (Self-Hosted PaaS) conçu pour transformer n'importe quelle machine physique ou VPS en une infrastructure de production complète. À l'intersection de l'orchestration Docker, de la détection de build automatique et de l'intelligence artificielle locale, Khamal élimine la friction entre le code et la mise en ligne, tout en garantissant une souveraineté totale des données.

## 🚀 Installation "Plug & Play"

Khamal est conçu pour être opérationnel immédiatement. Notre script d'installation automatise la configuration de l'environnement, la gestion des dépendances et la sécurisation du socket Docker.

### Installation Rapide (One-liner)

Vous pouvez installer Khamal directement sur une machine vierge (Ubuntu/Debian recommandé) avec cette commande :

```bash
curl -sSL https://raw.githubusercontent.com/your-repo/khamal/main/scripts/install.sh | bash
```
*Le script clonera automatiquement le dépôt et configurera tout pour vous.*

### Installation Manuelle

```bash
# Clonez le dépôt
git clone https://github.com/your-repo/khamal.git
cd khamal

# Lancez l'installation automatique (Zero-Config)
bash scripts/install.sh
```

## 📂 Structure du Projet (Open-Core)

Khamal suit un modèle **Open-Core** strict pour garantir une base saine et extensible :

- **[/core](./core) :** Le moteur open-source. Gestion des cycles de vie des conteneurs, orchestration réseau isolée, intégration Nixpacks, et moteur LogSage. **Licence Apache 2.0**.
- **[/pro](./pro) :** Extensions professionnelles. Gestion multi-nœuds (cluster), Marque Blanche (White-labeling), et intégrations SSO. **Licence Propriétaire**.

## 🧠 Intelligence de Diagnostic : LogSage (MPPS)

L'une des innovations majeures de Khamal est **LogSage**, un moteur de diagnostic basé sur l'IA locale (Llama 3.2 / Qwen 2.5 Coder via Ollama).

- **Multi-Phase Prioritization Strategy (MPPS)** : LogSage utilise une stratégie en trois phases (Anchors, Proximity, Recency) pour compresser des logs massifs dans le contexte limité d'un LLM local sans perte de densité sémantique.
- **Réduction de Bruit** : Filtre intelligemment les logs non pertinents (heartbeats, healthchecks).
- **Analyse de Crash** : Identifie la cause racine d'un échec de déploiement.
- **Correctifs Applicables** : Génère des suggestions de code directement applicables.

## 🛡️ "Security by Design" Architecture

Khamal intègre la sécurité au plus profond de son architecture pour protéger votre hôte :

- **Hardened Docker Client** : Un wrapper sécurisé qui interdit les paramètres dangereux comme `--privileged`, `cap_add` ou l'accès direct aux périphériques hôtes ("No-Escalation Policy").
- **Application Level Firewall (Docker Proxy)** : Khamal ne communique **jamais** directement avec le socket Docker (`/var/run/docker.sock`). Toute l'orchestration passe par un proxy sécurisé (`docker-socket-proxy`) qui filtre les requêtes API et bloque les tentatives d'escalade au niveau réseau.
- **Isolation Réseau** : Chaque projet dispose de son propre réseau bridge isolé. Le trafic externe est strictement géré par un Traefik centralisé qui communique lui aussi uniquement via le proxy sécurisé.
- **Sécurité Physique (USBGuard)** : Les déploiements via USB sont protégés par une intégration stricte avec USBGuard, imposant des options de montage sécurisées (`noexec`, `nosuid`, `nodev`) et une autorisation préalable du matériel.

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
