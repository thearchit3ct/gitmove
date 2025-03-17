# Documentation GitMove

## Table des matières

- [Introduction](#introduction)
- [Installation](#installation)
- [Configuration](#configuration)
- [Commandes](#commandes)
  - [gitmove init](#gitmove-init)
  - [gitmove clean](#gitmove-clean)
  - [gitmove sync](#gitmove-sync)
  - [gitmove advice](#gitmove-advice)
  - [gitmove check-conflicts](#gitmove-check-conflicts)
  - [gitmove status](#gitmove-status)
- [Options globales](#options-globales)
- [Cas d'utilisation avancés](#cas-dutilisation-avancés)
- [FAQ et dépannage](#faq-et-dépannage)

## Introduction

GitMove est un gestionnaire de branches Git intelligent qui simplifie le workflow Git en offrant quatre fonctionnalités principales :

- **Nettoyage automatique des branches fusionnées**
- **Synchronisation intelligente avec la branche principale**
- **Suggestions de stratégie pour fusionner ou rebaser**
- **Détection précoce des conflits potentiels**

Ces fonctionnalités vous aident à maintenir un historique Git propre et à éviter les erreurs courantes lors de la gestion des branches.

## Installation

Vous pouvez installer GitMove à l'aide de pip :

```bash
pip install gitmove
```

Vérifiez l'installation :

```bash
gitmove --version
```

## Configuration

GitMove utilise un fichier de configuration au format TOML qui peut exister à plusieurs niveaux :

- **Niveau global** : `~/.config/gitmove/config.toml` (Linux/macOS) ou `%APPDATA%\gitmove\config.toml` (Windows)
- **Niveau projet** : `.gitmove.toml` à la racine du dépôt Git

### Configuration automatique

L'initialisation crée une configuration de base adaptée à votre dépôt :

```bash
gitmove init
```

### Configuration manuelle

Vous pouvez modifier manuellement le fichier de configuration avec la structure suivante :

```toml
[general]
main_branch = "main"  # Branche principale (main ou master)
verbose = false       # Mode verbeux par défaut

[clean]
auto_clean = false            # Nettoyage automatique
exclude_branches = [          # Branches à ne jamais nettoyer
    "develop", 
    "staging"
]
age_threshold = 30            # Âge minimum en jours pour le nettoyage

[sync]
default_strategy = "rebase"   # Stratégie par défaut (rebase ou merge)
auto_sync = true              # Synchronisation automatique
sync_frequency = "daily"      # Fréquence de vérification

[advice]
rebase_threshold = 5          # Nombre de commits pour préférer rebase
consider_branch_age = true    # Prendre en compte l'âge de la branche
force_merge_patterns = [      # Patterns de branches pour forcer le merge
    "feature/*", 
    "release/*"
]
force_rebase_patterns = [     # Patterns de branches pour forcer le rebase
    "fix/*", 
    "chore/*"
]

[conflict_detection]
pre_check_enabled = true      # Activer la vérification avant merge/rebase
show_diff = true              # Afficher les différences dans les conflits
```

## Commandes

### gitmove init

Initialise la configuration de GitMove pour le dépôt courant.

#### Usage

```bash
gitmove init [options]
```

#### Options

- `--config=<path>` : Chemin vers un fichier de configuration à utiliser comme base

#### Exemples

```bash
# Initialisation simple
gitmove init

# Utiliser une configuration existante comme base
gitmove init --config=~/my-git-configs/gitmove-team.toml
```

### gitmove clean

Détecte et supprime les branches qui ont déjà été fusionnées dans la branche principale.

#### Usage

```bash
gitmove clean [options]
```

#### Options

- `--remote` : Nettoie également les branches distantes
- `--dry-run` : Simule l'opération sans effectuer de suppressions
- `--force`, `-f` : Supprime sans demander de confirmation
- `--exclude=<branch>` : Branche à exclure du nettoyage (peut être utilisé plusieurs fois)

#### Exemples

```bash
# Simuler le nettoyage
gitmove clean --dry-run

# Nettoyer les branches locales
gitmove clean

# Nettoyer les branches locales et distantes
gitmove clean --remote

# Nettoyer en excluant certaines branches
gitmove clean --exclude=feature/important --exclude=fix/keep-this

# Nettoyer sans confirmation
gitmove clean --force
```

### gitmove sync

Synchronise la branche courante avec la branche principale.

#### Usage

```bash
gitmove sync [options]
```

#### Options

- `--strategy=<strategy>` : Stratégie à utiliser (`merge`, `rebase` ou `auto`)
- `--branch=<branch>` : Branche à synchroniser (par défaut : branche courante)

#### Exemples

```bash
# Synchroniser la branche courante (stratégie automatique)
gitmove sync

# Synchroniser avec rebase
gitmove sync --strategy=rebase

# Synchroniser une branche spécifique
gitmove sync --branch=feature/my-feature

# Synchroniser une branche spécifique avec merge
gitmove sync --branch=feature/complex-feature --strategy=merge
```

### gitmove advice

Analyse une branche et recommande une stratégie pour la fusion ou le rebase.

#### Usage

```bash
gitmove advice [options]
```

#### Options

- `--branch=<branch>` : Branche à analyser (par défaut : branche courante)
- `--target=<target>` : Branche cible (par défaut : branche principale)

#### Exemples

```bash
# Obtenir un conseil pour la branche courante
gitmove advice

# Obtenir un conseil pour une branche spécifique
gitmove advice --branch=feature/new-login

# Obtenir un conseil pour une cible spécifique
gitmove advice --branch=feature/new-login --target=develop
```

### gitmove check-conflicts

Détecte les conflits potentiels avant une fusion ou un rebase.

#### Usage

```bash
gitmove check-conflicts [options]
```

#### Options

- `--branch=<branch>` : Branche à vérifier (par défaut : branche courante)
- `--target=<target>` : Branche cible (par défaut : branche principale)

#### Exemples

```bash
# Vérifier les conflits pour la branche courante
gitmove check-conflicts

# Vérifier les conflits pour une branche spécifique
gitmove check-conflicts --branch=feature/navbar

# Vérifier les conflits avec une cible spécifique
gitmove check-conflicts --branch=feature/navbar --target=develop
```

### gitmove status

Affiche l'état actuel des branches et des recommandations.

#### Usage

```bash
gitmove status [options]
```

#### Options

- `--detailed` : Affiche des informations détaillées

#### Exemples

```bash
# Afficher un résumé de l'état
gitmove status

# Afficher des informations détaillées
gitmove status --detailed
```

## Options globales

Ces options peuvent être utilisées avec n'importe quelle commande :

- `--verbose`, `-v` : Affiche des informations détaillées
- `--quiet`, `-q` : Minimise les sorties
- `--config=<path>`, `-c <path>` : Spécifie un fichier de configuration alternatif
- `--help`, `-h` : Affiche l'aide pour une commande
- `--version` : Affiche la version de l'outil

## Cas d'utilisation avancés

### Intégration avec les hooks Git

Vous pouvez automatiser GitMove en l'intégrant dans les hooks Git :

#### Post-merge hook

```bash
# .git/hooks/post-merge
#!/bin/sh
gitmove clean --force
```

#### Pre-push hook

```bash
# .git/hooks/pre-push
#!/bin/sh
gitmove check-conflicts
if [ $? -ne 0 ]; then
  echo "Des conflits potentiels ont été détectés. Utilisez 'gitmove sync' avant de pousser."
  exit 1
fi
```

### Intégration CI/CD

Exemple d'intégration dans un pipeline CI/CD (GitHub Actions) :

```yaml
name: GitMove Branch Maintenance

on:
  schedule:
    - cron: '0 0 * * 0'  # Exécution hebdomadaire le dimanche à minuit

jobs:
  cleanup-branches:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install GitMove
        run: pip install gitmove
      - name: Clean merged branches
        run: gitmove clean --remote --force
```

### Workflows Git courants

#### GitFlow avec GitMove

```bash
# Créer une nouvelle fonctionnalité
git flow feature start my-feature

# Développer et commiter...

# Avant de finaliser la fonctionnalité
gitmove check-conflicts
gitmove sync

# Terminer la fonctionnalité
git flow feature finish my-feature

# Nettoyer les branches fusionnées
gitmove clean
```

#### GitHub Flow avec GitMove

```bash
# Créer une branche de fonctionnalité
git checkout -b feature/new-feature

# Développer et commiter...

# Avant de créer une Pull Request
gitmove sync
gitmove status --detailed

# Après fusion de la PR
git checkout main
git pull
gitmove clean
```

## FAQ et dépannage

### Problèmes courants

#### Q: J'obtiens "fatal: not a git repository" lorsque j'exécute les commandes GitMove.
**R:** Assurez-vous d'exécuter GitMove à l'intérieur d'un dépôt Git valide. Vérifiez que le répertoire courant est bien un dépôt Git initialisé avec `git init` ou cloné.

#### Q: Comment puis-je empêcher GitMove de nettoyer certaines branches ?
**R:** Vous pouvez exclure des branches spécifiques de trois façons :
1. Utiliser l'option `--exclude` avec la commande `clean`
2. Configurer les branches à exclure dans le fichier de configuration sous `[clean]exclude_branches`
3. Suivre une convention de nommage spécifique pour les branches à préserver

#### Q: La synchronisation échoue avec des conflits. Que dois-je faire ?
**R:** Si `gitmove sync` échoue avec des conflits :
1. Exécutez `gitmove check-conflicts` pour identifier précisément les fichiers problématiques
2. Résolvez manuellement les conflits dans ces fichiers
3. Terminez le processus de merge/rebase avec `git merge --continue` ou `git rebase --continue`
4. Relancez `gitmove sync` pour vérifier que tout est synchronisé

#### Q: Comment puis-je personnaliser les règles pour les suggestions "merge vs. rebase" ?
**R:** Modifiez les paramètres dans la section `[advice]` du fichier de configuration :
- `rebase_threshold` : Nombre de commits au-delà duquel merge est préféré
- `force_merge_patterns` et `force_rebase_patterns` : Patterns de noms de branches pour forcer une stratégie

### Astuces d'utilisation efficace

1. **Initialisez GitMove au début d'un projet** pour établir une configuration cohérente
2. **Utilisez `gitmove status` régulièrement** pour avoir une vision d'ensemble
3. **Exécutez `gitmove sync` avant de commencer à travailler** sur une branche existante
4. **Vérifiez les conflits potentiels avec `gitmove check-conflicts`** avant de créer des Pull Requests
5. **Configurez des hooks Git** pour automatiser les tâches répétitives