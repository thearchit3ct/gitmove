# Spécification du projet "gitmove"

## Aperçu du projet

GitMove est un outil de ligne de commande Python visant à simplifier et à automatiser la gestion des branches Git. Il offre des fonctionnalités intelligentes pour maintenir un workflow Git propre et efficace, en se concentrant sur quatre fonctionnalités principales :

1. **Nettoyage automatique des branches fusionnées**
2. **Synchronisation automatique avec la branche principale**
3. **Suggestions intelligentes pour fusionner ou rebaser**
4. **Détection précoce des conflits potentiels**

## Objectifs du projet

- Simplifier la gestion quotidienne des branches Git
- Réduire les problèmes liés aux conflits de fusion
- Maintenir un historique Git propre et cohérent
- Automatiser les tâches répétitives liées à la gestion des branches

## Architecture et structure du projet

```
gitmove/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── gitmove/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── branch_manager.py
│       │   ├── conflict_detector.py
│       │   ├── sync_manager.py
│       │   └── strategy_advisor.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── git_commands.py
│       │   └── logger.py
│       └── validators/
│           ├── __init__.py
│           └── git_repo_validator.py
└── tests/
    ├── __init__.py
    ├── test_branch_manager.py
    ├── test_conflict_detector.py
    ├── test_sync_manager.py
    └── test_strategy_advisor.py
```

## Fonctionnalités détaillées

### 1. Nettoyage automatique des branches fusionnées

- **Description** : Détecte et supprime les branches qui ont déjà été fusionnées dans la branche principale.
- **Comportement** :
  - Identifie les branches locales qui ont été fusionnées
  - Propose à l'utilisateur une liste des branches à nettoyer
  - Offre une option pour le nettoyage automatique ou manuel
  - Peut également nettoyer les branches distantes correspondantes (optionnel)
- **Options de configuration** :
  - Exclusion de branches spécifiques
  - Âge minimum des branches à nettoyer
  - Mode de nettoyage (interactif, automatique, dry-run)

### 2. Synchronisation automatique avec la branche principale

- **Description** : Maintient les branches de travail à jour avec la branche principale.
- **Comportement** :
  - Détecte quand la branche principale a de nouveaux commits
  - Propose de synchroniser la branche courante avec la principale
  - Utilise la stratégie optimale (merge ou rebase) selon la configuration
  - Gère les conflits éventuels pendant la synchronisation
- **Options de configuration** :
  - Fréquence de vérification des mises à jour
  - Stratégie de synchronisation par défaut
  - Branches à surveiller pour les mises à jour

### 3. Suggestions intelligentes pour fusionner ou rebaser

- **Description** : Analyse le contexte et suggère la meilleure stratégie (merge ou rebase).
- **Comportement** :
  - Analyse l'historique des branches et leur divergence
  - Considère le nombre de commits, la complexité des changements
  - Recommande une stratégie basée sur des règles prédéfinies
  - Explique le raisonnement derrière la suggestion
- **Règles prédéfinies** :
  - Rebaser pour les branches avec peu de commits locaux
  - Fusionner pour les branches de fonctionnalités complètes
  - Considérer la politique du projet (via configuration)
  - Adapter les règles selon l'historique des conflits précédents

### 4. Détection précoce des conflits potentiels

- **Description** : Identifie et alerte sur les conflits potentiels avant une fusion ou un rebase.
- **Comportement** :
  - Simule la fusion/rebase pour détecter les conflits
  - Identifie les fichiers problématiques
  - Suggère des actions pour minimiser les conflits
  - Offre un aperçu des changements conflictuels
- **Fonctionnalités avancées** :
  - Analyse de la complexité des conflits
  - Historique des conflits pour améliorer les prédictions futures
  - Suggestions de stratégies alternatives en cas de conflits majeurs

## Interface de ligne de commande

L'outil sera utilisable uniquement via des commandes CLI avec la structure suivante :

```bash
gitmove <commande> [options]
```

### Commandes principales

- **clean** : Nettoie les branches fusionnées
  ```bash
  gitmove clean [--remote] [--dry-run] [--force] [--exclude=<branches>]
  ```

- **sync** : Synchronise la branche courante avec la principale
  ```bash
  gitmove sync [--strategy=<merge|rebase>] [--branch=<branch_name>]
  ```

- **advice** : Suggère une stratégie pour fusionner/rebaser
  ```bash
  gitmove advice [--branch=<branch_name>] [--target=<target_branch>]
  ```

- **check-conflicts** : Détecte les conflits potentiels
  ```bash
  gitmove check-conflicts [--branch=<branch_name>] [--target=<target_branch>]
  ```

- **init** : Initialise la configuration de gitmove pour le dépôt
  ```bash
  gitmove init [--config=<path_to_config>]
  ```

- **status** : Affiche l'état actuel des branches et recommandations
  ```bash
  gitmove status [--detailed]
  ```

### Options globales

- **--verbose** : Affiche des informations détaillées
- **--quiet** : Minimise les sorties
- **--config=<path>** : Spécifie un fichier de configuration alternatif
- **--help** : Affiche l'aide pour une commande
- **--version** : Affiche la version de l'outil

## Configuration

GitMove utilisera un fichier de configuration au format TOML qui peut être défini à plusieurs niveaux :

1. **Niveau global** : Configuration par défaut pour tous les projets
2. **Niveau projet** : Configuration spécifique au dépôt Git
3. **Niveau utilisateur** : Préférences personnelles

Exemple de fichier de configuration :

```toml
[general]
main_branch = "main"
verbose = false

[clean]
auto_clean = false
exclude_branches = ["develop", "staging"]
age_threshold = 30  # jours

[sync]
default_strategy = "rebase"
auto_sync = true
sync_frequency = "daily"

[advice]
rebase_threshold = 5  # nombre de commits
consider_branch_age = true
force_merge_patterns = ["feature/*", "release/*"]
force_rebase_patterns = ["fix/*", "chore/*"]

[conflict_detection]
pre_check_enabled = true
show_diff = true
```

## Dépendances techniques

- **Python** : 3.8 ou supérieur
- **GitPython** : Pour interagir avec les dépôts Git
- **Click** : Pour créer l'interface de ligne de commande
- **Rich** : Pour améliorer l'affichage dans le terminal
- **TOML** : Pour la gestion de la configuration

## Installation (PEP 518)

Le projet suivra le standard PEP 518 avec un fichier `pyproject.toml` :

```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "gitmove"
version = "0.1.0"
description = "Gestionnaire de branches Git intelligent"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "thearchit3ct", email = "thearchit3ct@outlook.fr"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Version Control :: Git",
]
dependencies = [
    "gitpython>=3.1.0",
    "click>=8.0.0",
    "rich>=10.0.0",
    "toml>=0.10.0",
]

[project.scripts]
gitmove = "gitmove.cli:main"

[project.urls]
"Homepage" = "https://github.com/thearchit3ct/gitmove"
"Bug Tracker" = "https://github.com/thearchit3ct/gitmove/issues"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.black]
line-length = 88
target-version = ["py39"]


[tool.isort]
profile = "black"
multi_line_output = 3
```

Pour installer le projet :

```bash
pip install gitmove
```

Pour le développement :

```bash

git clone https://github.com/thearchit3ct/gitmove.git
cd gitmove
pip install -e ".[dev]"
```

## Extensions futures

- Intégration avec les systèmes CI/CD
- Support pour les hooks Git personnalisés
- Interface web minimaliste
- Rapports et statistiques sur l'utilisation des branches
- Support pour des workflows Git spécifiques (GitFlow, GitHub Flow, etc.)

## Licence

MIT
