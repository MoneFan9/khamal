# [ISSUE] Finalisation du workflow "Nouveau Projet"

## Description
Rendre Khamal utilisable sans API externe en finalisant les formulaires de création de projet dans le Dashboard.

## Spécifications
- Créer la vue HTML `project_create.html`.
- Implémenter le formulaire : Nom du projet, URL Git, Branche, Domaine.
- Intégrer l'appel au service de détection Nixpacks pour suggérer les dépendances (Postgres/Redis).
- Lancer le premier déploiement immédiatement après la création.

## Critères d'acceptation
- Un utilisateur peut créer un projet complet depuis son navigateur.
- Le projet est automatiquement provisionné et déployé.
