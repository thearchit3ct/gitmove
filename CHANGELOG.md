# Changelog

Tous les changements notables pour le projet GitMove seront documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Versionnage Sémantique](https://semver.org/lang/fr/).

## [0.1.0] - 2025-03-17

### Ajouté
- Système de gestion de configuration avancé
  - Validation de configuration avec schéma personnalisable
  - Support des variables d'environnement
  - Génération de modèles de configuration
- Système de plugins pour étendre les fonctionnalités
- Intégration CI/CD améliorée
  - Génération de workflows pour plusieurs plateformes
  - Validation des noms de branches
  - Détection automatique de l'environnement CI
- Commandes CLI enrichies
  - `gitmove config` pour la gestion de configuration
  - `gitmove cicd` pour les opérations CI/CD
  - `gitmove env` pour la gestion des variables d'environnement

### Modifié
- Refactorisation du système de gestion des branches
- Amélioration de la détection et de la résolution des conflits
- Optimisation des performances de synchronisation des branches

### Corrigé
- Corrections de bugs mineurs dans la gestion des branches
- Améliorations de la gestion des erreurs
- Correction de problèmes de compatibilité entre différents systèmes d'exploitation

## [0.0.1] - 2024-12-15

### Ajouté
- Version initiale du projet
- Fonctionnalités de base de gestion de branches Git
- Commandes de nettoyage et de synchronisation des branches
- Support de configuration de base
- Gestion élémentaire des conflits

### Limitations
- Support limité des plateformes CI/CD
- Fonctionnalités de configuration réduites
- Gestion des plugins non disponible

## Légende
- `Ajouté` pour les nouvelles fonctionnalités.
- `Modifié` pour les changements dans les fonctionnalités existantes.
- `Corrigé` pour les corrections de bugs.
- `Supprimé` pour les fonctionnalités retirées.
- `Sécurité` pour les mises à jour de sécurité.

## Contribuer
Si vous découvrez des bugs ou avez des suggestions d'amélioration, n'hésitez pas à ouvrir une issue ou une pull request sur le dépôt GitHub.