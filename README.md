# 🦁 Khamal : Self-Hosted PaaS & AI Diagnostic Orchestrator

> **"Khamal : Vos serveurs, votre intelligence, votre liberté."**

Khamal est un orchestrateur intelligent de déploiement (Self-Hosted PaaS) conçu pour transformer n'importe quelle machine physique ou VPS en une infrastructure de production complète. À l'intersection de l'orchestration Docker, de la détection de build automatique et de l'intelligence artificielle locale, Khamal élimine la friction entre le code et la mise en ligne, tout en garantissant une souveraineté totale des données.

## 🚀 Installation "Plug & Play"

Khamal est conçu pour être opérationnel en quelques secondes.

```bash
# Clonez le dépôt
git clone https://github.com/your-repo/khamal.git
cd khamal

# Lancez l'installation automatique
bash scripts/install.sh
```

## 📂 Structure du Projet

Le projet suit une architecture **Open-Core** :

- **[/core](./core) :** Le cœur open-source. Gestion des déploiements, orchestration Docker, Nixpacks, et LogSage. Sous licence **Apache 2.0**.
- **[/pro](./pro) :** Extensions commerciales. Multi-nœuds, Marque Blanche, Support IA avancé. Sous **licence propriétaire**.

## 🎯 Vision du Projet
Contrairement aux solutions cloud propriétaires, Khamal rapatrie le pouvoir sur le matériel de l'utilisateur :
- **Intelligence de Diagnostic (LogSage) :** Utilise des modèles LLM locaux (via Ollama) pour analyser les logs de crash et proposer des correctifs applicables automatiquement.
- **Zéro-Configuration :** S'appuie sur Nixpacks pour analyser le code source et générer des images OCI hautement optimisées sans nécessiter de `Dockerfile`.
- **Ancrage Physique :** Permet le déploiement depuis des dépôts Git, mais aussi via des montages de dossiers locaux (Hot-Reload) et l'ingestion sécurisée depuis des supports USB.

## 🏗️ Architecture Technique (Contexte pour les contributeurs)

La pile technologique de Khamal est délibérément modulaire :

- **Backend :** Python 3.12+ / Django 6.0.
- **Orchestrateur :** Docker Engine via Docker SDK. Sécurisé par `docker-socket-proxy`.
- **Moteur de Build :** Nixpacks (Génère des images sans Dockerfile).
- **Routage :** Traefik avec SSL automatique (Let's Encrypt).
- **IA Locale :** Ollama (Llama 3.2, Qwen 2.5 Coder).

## 🤝 Contribuer

Nous accueillons les contributions avec enthousiasme ! Pour commencer :

1. **Explorez `/core`** : C'est là que réside toute la logique open-source.
2. **Lisez les commentaires** : Le code est documenté pour expliquer non seulement *ce qu'il fait*, mais surtout *pourquoi* il le fait ainsi (sécurité, isolation).
3. **Architecture Clean** : Respectez l'indépendance de `/core`. Le cœur ne doit jamais dépendre de `/pro`.

### Tests
Pour lancer la suite de tests :
```bash
export PYTHONPATH=core:.
pytest
```

## 📄 Licence
Ce projet utilise un modèle dual-licensing :
- Le dossier `/core` est sous licence [Apache 2.0](./core/LICENSE).
- Le dossier `/pro` est sous [licence commerciale propriétaire](./pro/LICENSE).
