# [ISSUE] Système d'Auto-fix interactif via Executor

## Description
Permettre à LogSage non seulement de diagnostiquer, mais aussi de proposer des changements de code/config applicables en un clic.

## Spécifications
- Étendre l'intégration LogSage pour détecter les blocs `propose_fix` générés par l'IA (via les tools Ollama).
- Afficher une "Diff" visuelle du changement proposé à l'utilisateur.
- Ajouter un bouton "Appliquer le correctif" qui appelle `core.ai.executor.apply_fix`.
- Redéclencher un déploiement automatiquement après l'application du fix.

## Critères d'acceptation
- L'application d'un correctif modifie réellement les fichiers sur le disque (dans l'environnement du projet).
- Un nouveau déploiement est lancé après modification.
