# [ISSUE] Dashboard Monitoring - Télémétrie Live (CPU/RAM)

## Description
Le dashboard actuel est statique. Il doit afficher l'état de santé réel des conteneurs.

## Spécifications
- Créer un nouveau Consumer Channels (WebSocket) pour `docker stats`.
- Diffuser les métriques CPU et RAM en temps réel pour chaque projet affiché sur le dashboard.
- Mettre à jour les badges de statut (Running/Failed) via WebSocket sans rafraîchir la page.
- Ajouter un mini-graphique (Sparkline) de consommation sur les cartes de projet.

## Critères d'acceptation
- Les métriques de consommation sont visibles sur le dashboard.
- Les changements de statut des conteneurs sont reflétés instantanément.
