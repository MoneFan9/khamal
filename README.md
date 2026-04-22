# 🦁 Khamal : Self-Hosted PaaS & AI Diagnostic Orchestrator

> **"Khamal : Vos serveurs, votre intelligence, votre liberté."**

Khamal est un orchestrateur intelligent de déploiement (Self-Hosted PaaS) conçu pour transformer n'importe quelle machine physique ou VPS en une infrastructure de production complète. À l'intersection de l'orchestration Docker, de la détection de build automatique et de l'intelligence artificielle locale, Khamal élimine la friction entre le code et la mise en ligne, tout en garantissant une souveraineté totale des données.

## 🎯 Vision du Projet
Contrairement aux solutions cloud propriétaires, Khamal rapatrie le pouvoir sur le matériel de l'utilisateur :
- **Intelligence de Diagnostic (LogSage) :** Utilise des modèles LLM locaux (via Ollama) pour analyser les logs de crash et proposer des correctifs applicables automatiquement.
- **Zéro-Configuration :** S'appuie sur Nixpacks pour analyser le code source et générer des images OCI hautement optimisées sans nécessiter de `Dockerfile`.
- **Ancrage Physique :** Permet le déploiement depuis des dépôts Git, mais aussi via des montages de dossiers locaux (Hot-Reload) et l'ingestion sécurisée depuis des supports USB.

## 🏗️ Architecture Technique (Contexte pour les contributeurs & Agents IA)

La pile technologique de Khamal est délibérément modulaire, orchestrée par un backend robuste :

- **Backend & API :** Python / Django. Gère la logique métier, les modèles de données (Projets, Déploiements, Serveurs) et l'interface d'administration.
- **Orchestrateur :** Docker Engine piloté via le `docker-py` (Docker SDK for Python). Les appels sont contraints par le principe du moindre privilège via un proxy socket.
- **Moteur de Build :** Nixpacks. Gère la détection des langages, la mise en cache agressive et le provisionnement implicite de bases de données associées (PostgreSQL, Redis).
- **Routage & SSL :** Traefik (ou Caddy). Attachement dynamique des labels pour les noms de domaine et génération automatique des certificats Let's Encrypt.
- **Moteur d'IA :** Ollama. Exécute des modèles quantifiés (Llama 3.2 3B ou Qwen 2.5 Coder 3B) pour l'analyse causale (RCA) des erreurs de build et d'exécution.

## 🚀 Modèle Open-Core
Khamal est propulsé par la communauté sous licence Apache 2.0. Des fonctionnalités étendues, telles que le pilotage Multi-Nœuds centralisé et la personnalisation en Marque Blanche pour les agences, sont disponibles sous licence commerciale dans l'écosystème Pro.

## 🛠️ Installation (En cours de développement)
*Les scripts d'installation curl automatisés seront bientôt disponibles.*

## 📄 Licence
Ce projet est sous licence Apache 2.0 - voir le fichier LICENSE pour plus de détails.

## Le projet utilise le modèle "Open Core"
