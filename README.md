# GitMove

[![PyPI version](https://img.shields.io/pypi/v/gitmove.svg)](https://pypi.org/project/gitmove/)
[![Python versions](https://img.shields.io/pypi/pyversions/gitmove.svg)](https://pypi.org/project/gitmove/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GitMove est un gestionnaire de branches Git intelligent conçu pour simplifier et automatiser la gestion des branches dans vos projets. Il offre des fonctionnalités avancées pour maintenir un workflow Git propre et efficace.

## Fonctionnalités principales

* **Nettoyage automatique des branches fusionnées** - Identifie et supprime les branches devenues obsolètes
* **Synchronisation intelligente avec la branche principale** - Garde vos branches à jour sans effort
* **Conseils de stratégie pour fusionner ou rebaser** - Recommande la meilleure approche selon le contexte
* **Détection précoce des conflits potentiels** - Anticipe les problèmes avant qu'ils ne surviennent

## Installation

```bash
pip install gitmove
```

GitMove nécessite Python 3.8 ou supérieur.

## Utilisation rapide

### Initialiser la configuration

Commencez par initialiser la configuration GitMove dans votre dépôt :

```bash
gitmove init
```

### Nettoyer les branches fusionnées

```bash
# Afficher les branches fusionnées qui peuvent être nettoyées
gitmove clean --dry-run

# Nettoyer les branches fusionnées (locales uniquement)
gitmove clean

# Nettoyer également les branches distantes
gitmove clean --remote
```

### Synchroniser avec la branche principale

```bash
# Synchroniser la branche courante avec la principale
gitmove sync

# Spécifier une stratégie
gitmove sync --strategy rebase  # ou --strategy merge
```

### Obtenir des conseils de stratégie

```bash
# Obtenir une recommandation pour la branche courante
gitmove advice

# Analyser une branche spécifique
gitmove advice --branch feature/123-ma-fonctionnalite
```

### Vérifier les conflits potentiels

```bash
# Détecter les conflits avant de fusionner
gitmove check-conflicts
```

### Afficher le statut général

```bash
# Afficher un résumé de l'état des branches
gitmove status

# Afficher des informations détaillées
gitmove status --detailed
```

## Configuration

GitMove peut être configuré à plusieurs niveaux :

1. **Niveau global** (`~/.config/gitmove/config.toml` ou `%APPDATA%\gitmove\config.toml`)
2. **Niveau projet** (`.gitmove.toml` à la racine du dépôt)

Exemple de configuration :

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

[advice]
rebase_threshold = 5  # nombre de commits
force_merge_patterns = ["feature/*", "release/*"]
force_rebase_patterns = ["fix/*", "chore/*"]

[conflict_detection]
pre_check_enabled = true
show_diff = true
```

## Options communes

Ces options sont disponibles pour toutes les commandes :

* `--verbose` ou `-v` : Affiche des informations détaillées
* `--quiet` ou `-q` : Minimise les sorties
* `--config=<path>` ou `-c <path>` : Spécifie un fichier de configuration alternatif
* `--help` ou `-h` : Affiche l'aide pour une commande
* `--version` : Affiche la version de l'outil

## Intégration dans les workflows

GitMove s'intègre parfaitement dans les workflows Git courants comme GitFlow ou GitHub Flow. Il est particulièrement utile dans les environnements de développement collaboratif avec de nombreuses branches.

### Automatisation

Vous pouvez facilement intégrer GitMove dans vos scripts de CI/CD ou hooks Git. Par exemple, pour nettoyer automatiquement les branches fusionnées après un pull :

```bash
# Dans .git/hooks/post-merge
#!/bin/sh
gitmove clean --force
```

## Développement

Pour contribuer au développement de GitMove :

```bash
# Cloner le dépôt
git clone https://github.com/thearchit3ct/gitmove.git
cd gitmove

# Installer en mode développement
pip install -e ".[dev]"

# Exécuter les tests
pytest
```

## Licence

GitMove est distribué sous licence MIT. Voir le fichier LICENSE pour plus de détails.

pip list | grep api-feature-coverage-analyzer