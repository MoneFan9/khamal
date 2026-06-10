# [ISSUE] Intégration UI LogSage - Diagnostic IA & RCA

## Description
LogSage est actuellement implémenté en backend (preprocessor et prompt builder) mais inaccessible depuis l'interface utilisateur. Cette tâche vise à intégrer le diagnostic IA directement dans la vue des logs de déploiement.

## Spécifications
- Ajouter un bouton "Lancer le Diagnostic IA" sur la page `deployment_logs.html`.
- Créer une vue Django/API qui récupère les logs, les passe par `LogSagePreprocessor` et interroge Ollama.
- Afficher le résultat du diagnostic (RCA) dans un modal ou un panneau dédié avec formatage Markdown.
- Gérer l'état de chargement (loading spinner) car l'inférence locale peut prendre du temps.

## Critères d'acceptation
- L'utilisateur peut déclencher une analyse sur un déploiement ayant échoué.
- Le diagnostic s'affiche clairement et contient une analyse de la cause racine et une résolution proposée.
