# 🦁 Khamal : Self-Hosted PaaS & AI Diagnostic Orchestrator

> **"Khamal : Vos serveurs, votre intelligence, votre liberté."**

Khamal est un orchestrateur de déploiement (Self-Hosted PaaS) **Zero-Config** conçu pour transformer n'importe quelle machine Linux en une infrastructure de production complète et sécurisée. À l'intersection de l'orchestration Docker, de la détection de build automatique (via Nixpacks) et de l'intelligence artificielle locale, Khamal élimine la complexité entre l'écriture du code et sa mise en ligne.

## 🚀 Installation "Plug & Play"

Khamal est conçu pour être opérationnel en moins de 2 minutes. Notre script d'installation automatise tout, de la gestion des dépendances à la sécurisation du système.

```bash
# Téléchargez et lancez l'installation automatique
curl -sSL https://raw.githubusercontent.com/your-repo/khamal/main/scripts/install.sh | bash
```

### Ce que fait l'installateur "Zero-Config" :
- **Auto-détection** : Vérification de Docker, Python 3 et Nixpacks.
- **Isolation immédiate** : Création d'un environnement virtuel Python et d'un réseau Docker isolé.
- **Sécurisation par défaut** : Déploiement d'un `docker-socket-proxy` pour protéger l'API Docker du serveur.
- **Routage Intelligent** : Initialisation automatique de Traefik v3 avec support SSL (Let's Encrypt) prêt à l'emploi.
- **Optimisation IA** : Pré-configuration pour Ollama afin d'activer immédiatement LogSage.

## 📂 Architecture Open-Core

Khamal suit un modèle **Open-Core** strict pour garantir une base solide, transparente et extensible :

- **[/core](./core) (Apache 2.0) :** Le moteur open-source. Gestion des cycles de vie des conteneurs, orchestration réseau, intégration Nixpacks, et moteur de diagnostic LogSage.
- **[/pro](./pro) (Propriétaire) :** Extensions professionnelles. Gestion multi-nœuds (Clustering), Marque Blanche (White-labeling), et intégrations SSO avancées.

## 🛡️ Security by Design (Souveraineté Totale)

La sécurité n'est pas une option dans Khamal, elle est ancrée dans son architecture :

- **Hardened Docker Client** : Khamal ne parle jamais directement au socket Docker. Toutes les requêtes passent par un proxy de sécurité qui filtre les paramètres dangereux (ex: interdiction du mode `--privileged`).
- **Isolation Réseau** : Chaque projet dispose de son propre réseau bridge isolé. Aucun conteneur ne peut communiquer avec un autre projet par défaut.
- **Physical Ingestion Security** : Khamal supporte le déploiement via USB physique. Ce vecteur est protégé par **USBGuard** et des montages sécurisés (`noexec, nosuid, nodev`).
- **IA Locale** : Vos logs ne quittent jamais votre serveur. Le diagnostic est effectué localement via Ollama.

## 🧠 LogSage : Le Diagnostic Propulsé par l'IA

LogSage est le moteur de diagnostic de Khamal qui résout le problème du "bruit" dans les logs.

- **Stratégie MPPS** : LogSage utilise une *Multi-Phase Prioritization Strategy* pour identifier les "ancres" (erreurs critiques) et fournir le contexte exact nécessaire à l'IA, sans saturer sa fenêtre de contexte.
- **Analyse de Cause Racine (RCA)** : Identifie instantanément pourquoi un build ou un déploiement a échoué.
- **Fix Applicables** : Propose des correctifs de code directement applicables.

## 🤝 Contribuer au Projet

Nous accueillons avec enthousiasme les contributions à la version Open-Core.

### Guide du Développeur
1. **Initialisation** : `pip install -r core/requirements.txt`
2. **Configuration** : Utilisez `core/.env.example` comme base.
3. **Tests** :
   ```bash
   export PYTHONPATH=$(pwd)/core:$(pwd)/pro:.
   export DJANGO_SETTINGS_MODULE=khamal.settings.development
   pytest
   ```

### Règles d'Or de l'Architecture
- **Dépendance Unidirectionnelle** : Le dossier `/core` est le socle. Il ne doit **JAMAIS** importer de modules provenant de `/pro`.
- **Zéro Régression** : Chaque pull request doit maintenir une couverture de test proche de 100% sur les composants critiques.
- **Documentation technique** : Expliquez le "Pourquoi" dans vos docstrings pour faciliter la maintenance à long terme.

## 📄 Licence
- Le cœur du projet (`/core`) est sous licence **Apache 2.0**.
- Les modules professionnels (`/pro`) sont sous licence commerciale propriétaire.
