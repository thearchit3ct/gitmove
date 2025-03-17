# Wiki du projet GitMove

## Introduction

GitMove est un outil de gestion avancée pour les dépôts Git, conçu pour faciliter la maintenance des branches, la synchronisation et la gestion de la configuration. Cet outil apporte des fonctionnalités étendues qui simplifient le flux de travail des équipes de développement travaillant avec Git.

## Table des matières

1. [Installation](#installation)
2. [Concepts de base](#concepts-de-base)
3. [Configuration](#configuration)
   - [Fichier de configuration](#fichier-de-configuration)
   - [Variables d'environnement](#variables-denvironnement)
   - [Validation de configuration](#validation-de-configuration)
4. [Commandes](#commandes)
   - [Gestion des branches](#gestion-des-branches)
   - [Synchronisation](#synchronisation)
   - [Nettoyage](#nettoyage)
   - [Configuration](#commandes-de-configuration)
5. [Cas d'utilisation](#cas-dutilisation)
6. [FAQ](#faq)
7. [Dépannage](#dépannage)
8. [Contribuer](#contribuer)

## Installation

### Prérequis

- Python 3.6 ou supérieur
- Git 2.20 ou supérieur

### Via pip

```bash
pip install gitmove
```

### À partir des sources

```bash
git clone https://github.com/gitmove/gitmove.git
cd gitmove
pip install -e .
```

### Vérification de l'installation

```bash
gitmove --version
```

## Concepts de base

GitMove s'articule autour de trois fonctionnalités principales :

1. **Branch Management** - Gestion simplifiée des branches avec création, suppression et navigation
2. **Sync** - Synchronisation intelligente des branches avec la branche principale
3. **Clean** - Nettoyage automatisé des branches obsolètes

## Configuration

GitMove offre un système de configuration flexible, avec validation intégrée et support des variables d'environnement.

### Fichier de configuration

GitMove utilise le format TOML pour ses fichiers de configuration. L'emplacement par défaut est :

- **Linux/macOS** : `~/.config/gitmove/config.toml`
- **Windows** : `~\.gitmove\config.toml`

Exemple de configuration :

```toml
[general]
main_branch = "main"
verbose = false

[clean]
auto_clean = false
exclude_branches = ["develop", "staging"]
age_threshold = 30

[sync]
default_strategy = "rebase"
auto_sync = true
```

### Variables d'environnement

Toutes les options peuvent également être configurées via des variables d'environnement avec le préfixe `GITMOVE_`. Les variables d'environnement ont priorité sur le fichier de configuration.

Exemples :

```bash
export GITMOVE_GENERAL_MAIN_BRANCH="main"
export GITMOVE_CLEAN_AGE_THRESHOLD=45
export GITMOVE_SYNC_DEFAULT_STRATEGY="merge"
```

Pour les valeurs complexes comme les listes, utilisez le format JSON :

```bash
export GITMOVE_CLEAN_EXCLUDE_BRANCHES='["develop", "staging", "production"]'
```

### Validation de configuration

GitMove dispose d'un système de validation robuste qui vérifie l'intégrité de votre configuration et fournit des messages d'erreur détaillés.

Le schéma de configuration complet est le suivant :

| Section | Option | Type | Requis | Valeur par défaut | Description |
|---------|--------|------|--------|------------------|-------------|
| general | main_branch | string | Oui | "main" | Nom de la branche principale du dépôt |
| general | verbose | boolean | Non | false | Active le mode verbeux pour plus de détails |
| clean | auto_clean | boolean | Non | false | Active le nettoyage automatique des branches |
| clean | exclude_branches | liste de strings | Non | ["develop", "staging"] | Branches à exclure du nettoyage |
| clean | age_threshold | entier (1-365) | Non | 30 | Âge minimum (en jours) pour qu'une branche soit éligible au nettoyage |
| sync | default_strategy | string | Non | "rebase" | Stratégie par défaut pour la synchronisation (merge, rebase, auto) |
| sync | auto_sync | boolean | Non | true | Active la synchronisation automatique des branches |

Pour générer un fichier de configuration par défaut :

```bash
gitmove config generate --output ~/.config/gitmove/config.toml
```

Pour valider votre configuration existante :

```bash
gitmove config validate --config ~/.config/gitmove/config.toml
```

## Commandes

### Gestion des branches

```bash
# Créer une nouvelle branche et basculer dessus
gitmove branch create feature/nouvelle-fonctionnalite

# Lister toutes les branches et leur statut
gitmove branch list

# Basculer sur une branche existante
gitmove branch switch feature/ma-branche

# Supprimer une branche locale et distante
gitmove branch delete feature/terminee
```

### Synchronisation

```bash
# Synchroniser la branche courante avec la branche principale
gitmove sync

# Spécifier une stratégie de synchronisation
gitmove sync --strategy merge

# Synchroniser toutes les branches de fonctionnalité
gitmove sync --all
```

### Nettoyage

```bash
# Afficher les branches qui seraient nettoyées
gitmove clean --dry-run

# Nettoyer les branches obsolètes (selon le critère d'âge)
gitmove clean

# Forcer le nettoyage sans confirmation
gitmove clean --force
```

### Commandes de configuration

```bash
# Afficher la configuration actuelle
gitmove config show

# Générer un fichier de configuration d'exemple
gitmove config generate

# Valider un fichier de configuration
gitmove config validate

# Obtenir des recommandations pour optimiser votre configuration
gitmove config recommend
```

## Cas d'utilisation

### Flux de travail GitFlow

GitMove s'intègre parfaitement avec le flux GitFlow :

```bash
# Configuration pour GitFlow
gitmove config generate --output ~/.config/gitmove/config.toml
```

Ensuite, modifiez le fichier pour définir :

```toml
[general]
main_branch = "master"

[clean]
exclude_branches = ["develop", "master", "release/*"]
```

### Intégration continue

Pour les environnements CI/CD, utilisez les variables d'environnement :

```bash
export GITMOVE_GENERAL_VERBOSE=true
export GITMOVE_SYNC_AUTO_SYNC=true
gitmove sync --all
```

## FAQ

### Quelle est la différence entre les stratégies "merge" et "rebase" ?

- **merge** - Préserve l'historique complet des commits mais crée un commit de fusion
- **rebase** - Réécrit l'historique pour créer une ligne de développement linéaire
- **auto** - Choisit automatiquement la meilleure stratégie selon le contexte

### Comment gérer les conflits de fusion ?

Si un conflit se produit pendant la synchronisation, GitMove vous guidera à travers les étapes de résolution :

1. Résolvez les conflits dans les fichiers concernés
2. Exécutez `git add` pour marquer les conflits comme résolus
3. Continuez avec `gitmove sync --continue`

### Est-ce que GitMove fonctionne avec des dépôts distants ?

Oui, GitMove est compatible avec tous les dépôts distants supportés par Git (GitHub, GitLab, Bitbucket, etc.).

## Dépannage

### Messages d'erreur courants

#### Erreur : "Configuration invalide"

Vérifiez votre fichier de configuration avec :

```bash
gitmove config validate
```

#### Erreur : "Impossible de synchroniser la branche"

Assurez-vous que :
1. Vous avez les permissions nécessaires
2. Vos modifications locales sont commitées ou stashées
3. Votre connexion réseau fonctionne correctement

### Logs de débogage

Activez le mode verbeux pour obtenir plus d'informations :

```bash
gitmove --verbose sync
```

Ou via la configuration :

```toml
[general]
verbose = true
```

## Contribuer

Nous accueillons les contributions au projet GitMove !

1. Forkez le dépôt GitHub
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Commitez vos changements (`git commit -m 'Add some amazing feature'`)
4. Poussez vers votre branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

### Directives de développement

- Suivez le style de code PEP 8
- Ajoutez des tests unitaires pour les nouvelles fonctionnalités
- Mettez à jour la documentation au besoin
- Assurez-vous que tous les tests passent avant de soumettre votre PR

### Construire la documentation

```bash
cd docs
pip install -r requirements.txt
make html
```