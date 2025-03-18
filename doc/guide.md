# Guide d'utilisation complet de GitMove

## Sommaire

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Démarrage rapide](#démarrage-rapide)
4. [Concepts fondamentaux](#concepts-fondamentaux)
5. [Configuration](#configuration)
6. [Commandes en détail](#commandes-en-détail)
7. [Workflows courants](#workflows-courants)
8. [Meilleures pratiques](#meilleures-pratiques)
9. [Résolution des problèmes](#résolution-des-problèmes)
10. [Références](#références)

## Introduction

GitMove est un outil de ligne de commande conçu pour simplifier et optimiser la gestion des dépôts Git. Il étend les fonctionnalités natives de Git avec des commandes intuitives pour la maintenance des branches, la synchronisation et la gestion de configuration avancée.

### Pourquoi utiliser GitMove ?

- **Productivité améliorée** : Simplifiez les opérations Git courantes avec une interface intuitive
- **Maintenance simplifiée** : Gérez et nettoyez automatiquement les branches obsolètes
- **Synchronisation intelligente** : Gardez vos branches à jour avec des stratégies adaptatives
- **Configuration flexible** : Adaptez l'outil à vos besoins grâce à un système de configuration robuste

## Installation

### Prérequis

Avant d'installer GitMove, assurez-vous que votre système répond aux exigences suivantes :

- Python 3.6 ou version ultérieure
- Git 2.20 ou version ultérieure
- Accès en lecture/écriture aux dépôts Git concernés

### Installation via pip

La méthode la plus simple pour installer GitMove est d'utiliser pip, le gestionnaire de paquets Python :

```bash
pip install gitmove
```

Pour les utilisateurs qui préfèrent isoler les installations Python, nous recommandons l'utilisation d'un environnement virtuel :

```bash
python -m venv gitmove-env
source gitmove-env/bin/activate  # Pour Linux/macOS
gitmove-env\Scripts\activate.bat  # Pour Windows
pip install gitmove
```

### Installation depuis les sources

Pour les utilisateurs souhaitant accéder aux dernières fonctionnalités ou contribuer au développement :

```bash
git clone https://github.com/gitmove/gitmove.git
cd gitmove
pip install -e .
```

### Vérification de l'installation

Pour vérifier que GitMove est correctement installé, exécutez :

```bash
gitmove --version
```

## Démarrage rapide

Voici quelques commandes essentielles pour commencer rapidement avec GitMove :

```bash
# Générer un fichier de configuration par défaut
gitmove config generate --output ~/.config/gitmove/config.toml

# Créer et basculer sur une nouvelle branche de fonctionnalité
gitmove branch create feature/ma-fonctionnalite

# Synchroniser votre branche avec la branche principale
gitmove sync

# Afficher les branches qui peuvent être nettoyées
gitmove clean --dry-run
```

## Concepts fondamentaux

### Modèle de branches

GitMove s'adapte à différents modèles de branches (GitFlow, GitHub Flow, etc.) tout en apportant des fonctionnalités supplémentaires pour leur gestion :

- **Branche principale** : Définie dans la configuration, généralement `main` ou `master`
- **Branches de fonctionnalité** : Branches temporaires pour développer de nouvelles fonctionnalités
- **Branches protégées** : Branches qui ne seront jamais nettoyées automatiquement

### Cycle de vie des branches

1. **Création** : `gitmove branch create`
2. **Développement** : Commits et modifications habituels
3. **Synchronisation** : `gitmove sync` pour rester à jour avec la branche principale
4. **Finalisation** : Merge ou rebase dans la branche principale
5. **Nettoyage** : `gitmove clean` pour supprimer les branches obsolètes

## Configuration

GitMove propose un système de configuration flexible et puissant qui vous permet d'adapter l'outil à vos besoins spécifiques.

### Structure de la configuration

Le fichier de configuration utilise le format TOML, organisé en sections :

```toml
[general]
# Paramètres généraux

[clean]
# Paramètres de nettoyage

[sync]
# Paramètres de synchronisation
```

### Emplacements du fichier de configuration

GitMove recherche le fichier de configuration dans les emplacements suivants, par ordre de priorité :

1. Chemin spécifié par l'option `--config`
2. `.gitmove/config.toml` dans le répertoire du projet courant
3. `~/.config/gitmove/config.toml` (Linux/macOS) ou `~\.gitmove\config.toml` (Windows)

### Options de configuration principales

#### Section [general]

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| main_branch | string | "main" | Nom de la branche principale du dépôt |
| verbose | boolean | false | Active le mode verbeux pour plus de détails |

#### Section [clean]

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| auto_clean | boolean | false | Active le nettoyage automatique des branches |
| exclude_branches | liste de strings | ["develop", "staging"] | Branches à exclure du nettoyage |
| age_threshold | entier (1-365) | 30 | Âge minimum (en jours) pour qu'une branche soit éligible au nettoyage |

#### Section [sync]

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| default_strategy | string | "rebase" | Stratégie par défaut pour la synchronisation (merge, rebase, auto) |
| auto_sync | boolean | true | Active la synchronisation automatique des branches |

### Configuration via variables d'environnement

Toutes les options peuvent également être définies via des variables d'environnement, en utilisant le préfixe `GITMOVE_` suivi du nom de la section et de l'option, en majuscules et séparés par des underscores :

```bash
# Équivalent à main_branch dans la section [general]
export GITMOVE_GENERAL_MAIN_BRANCH="main"

# Équivalent à age_threshold dans la section [clean]
export GITMOVE_CLEAN_AGE_THRESHOLD=45

# Pour les listes, utilisez la syntaxe JSON
export GITMOVE_CLEAN_EXCLUDE_BRANCHES='["develop", "staging", "production"]'
```

Les variables d'environnement ont priorité sur les valeurs du fichier de configuration.

### Validation de la configuration

GitMove valide automatiquement votre configuration et affiche des messages d'erreur détaillés en cas de problèmes :

```bash
# Valider un fichier de configuration existant
gitmove config validate --config ~/.config/gitmove/config.toml
```

## Commandes en détail

### Gestion des branches

#### Créer une branche

```bash
gitmove branch create <nom-de-branche> [options]
```

Options principales :
- `--from <branche-source>` : Branche à partir de laquelle créer la nouvelle branche
- `--no-switch` : Créer la branche sans basculer dessus

Exemples :

```bash
# Créer une branche feature à partir de main et basculer dessus
gitmove branch create feature/nouvelle-fonctionnalite

# Créer une branche hotfix à partir de production sans basculer dessus
gitmove branch create hotfix/bug-critique --from production --no-switch
```

#### Lister les branches

```bash
gitmove branch list [options]
```

Options principales :
- `--all` : Afficher toutes les branches (locales et distantes)
- `--remote` : Afficher uniquement les branches distantes
- `--format <format>` : Format de sortie (text, json)

Exemples :

```bash
# Lister toutes les branches locales
gitmove branch list

# Lister toutes les branches (locales et distantes) au format JSON
gitmove branch list --all --format json
```

#### Basculer entre branches

```bash
gitmove branch switch <nom-de-branche>
```

Exemple :

```bash
gitmove branch switch feature/ma-fonctionnalite
```

#### Supprimer une branche

```bash
gitmove branch delete <nom-de-branche> [options]
```

Options principales :
- `--force` : Forcer la suppression même si la branche n'est pas totalement mergée
- `--remote` : Supprimer également la branche distante
- `--no-confirm` : Ne pas demander de confirmation

Exemples :

```bash
# Supprimer une branche locale
gitmove branch delete feature/terminee

# Supprimer une branche locale et sa version distante sans confirmation
gitmove branch delete feature/terminee --remote --no-confirm
```

### Synchronisation

#### Synchroniser la branche courante

```bash
gitmove sync [options]
```

Options principales :
- `--strategy <stratégie>` : Stratégie de synchronisation (merge, rebase, auto)
- `--from <branche-source>` : Branche source pour la synchronisation (par défaut : branche principale)

Exemples :

```bash
# Synchroniser la branche courante avec la branche principale (définie dans la config)
gitmove sync

# Synchroniser la branche courante avec develop en utilisant la stratégie merge
gitmove sync --from develop --strategy merge
```

#### Synchroniser plusieurs branches

```bash
gitmove sync --all [options]
```

Options principales :
- `--pattern <motif>` : Motif glob pour filtrer les branches à synchroniser
- `--exclude <motif>` : Motif glob pour exclure des branches

Exemples :

```bash
# Synchroniser toutes les branches de fonctionnalités
gitmove sync --all --pattern "feature/*"

# Synchroniser toutes les branches sauf celles commençant par "wip/"
gitmove sync --all --exclude "wip/*"
```

### Nettoyage

#### Afficher les branches à nettoyer

```bash
gitmove clean --dry-run [options]
```

Options principales :
- `--age <jours>` : Âge minimum en jours (remplace la valeur de configuration)
- `--pattern <motif>` : Motif glob pour filtrer les branches à nettoyer

Exemple :

```bash
# Afficher les branches de plus de 60 jours qui seraient nettoyées
gitmove clean --dry-run --age 60
```

#### Nettoyer les branches

```bash
gitmove clean [options]
```

Options principales :
- `--force` : Nettoyer sans demander de confirmation
- `--remote` : Supprimer également les branches distantes
- `--exclude <motif>` : Motif glob pour exclure des branches

Exemples :

```bash
# Nettoyer les branches locales obsolètes
gitmove clean

# Nettoyer les branches locales et distantes sans confirmation
gitmove clean --remote --force
```

### Configuration

#### Générer une configuration

```bash
gitmove config generate [options]
```

Options principales :
- `--output <chemin>` : Chemin du fichier de sortie
- `--format <format>` : Format de sortie (toml, env)

Exemples :

```bash
# Générer un fichier de configuration TOML
gitmove config generate --output ~/.config/gitmove/config.toml

# Générer des variables d'environnement
gitmove config generate --format env > .env
```

#### Valider une configuration

```bash
gitmove config validate [options]
```

Options principales :
- `--config <chemin>` : Chemin du fichier de configuration à valider

Exemple :

```bash
gitmove config validate --config ~/.config/gitmove/config.toml
```

#### Afficher la configuration actuelle

```bash
gitmove config show [options]
```

Options principales :
- `--format <format>` : Format de sortie (toml, json, env)

Exemples :

```bash
# Afficher la configuration actuelle en format TOML
gitmove config show

# Afficher la configuration actuelle en format JSON
gitmove config show --format json
```

## Workflows courants

### GitFlow avec GitMove

GitFlow est un modèle de branches populaire qui définit des branches spécifiques pour différentes étapes du développement. Voici comment configurer et utiliser GitMove avec GitFlow :

#### Configuration pour GitFlow

```toml
[general]
main_branch = "master"

[clean]
exclude_branches = ["develop", "master", "release/*", "hotfix/*"]

[sync]
default_strategy = "rebase"
```

#### Exemple de workflow GitFlow avec GitMove

```bash
# Démarrer une fonctionnalité
gitmove branch create feature/nouvelle-fonctionnalite --from develop

# Travailler sur la fonctionnalité...
# [Faire des commits]

# Synchroniser avec develop régulièrement
gitmove sync --from develop

# Une fois la fonctionnalité terminée, retourner sur develop
gitmove branch switch develop

# Merger la fonctionnalité
git merge feature/nouvelle-fonctionnalite

# Nettoyer les branches de fonctionnalités terminées
gitmove clean --pattern "feature/*"
```

### GitHub Flow avec GitMove

GitHub Flow est un modèle de branches plus simple centré sur des branches de fonctionnalités et une branche principale.

#### Configuration pour GitHub Flow

```toml
[general]
main_branch = "main"

[clean]
auto_clean = true
exclude_branches = ["main"]
age_threshold = 14

[sync]
default_strategy = "rebase"
auto_sync = true
```

#### Exemple de workflow GitHub Flow avec GitMove

```bash
# Démarrer une fonctionnalité
gitmove branch create feature/nouvelle-fonctionnalite

# Travailler sur la fonctionnalité...
# [Faire des commits]

# Synchroniser avec main régulièrement
gitmove sync

# Push de la branche pour créer une Pull Request
git push -u origin feature/nouvelle-fonctionnalite

# Une fois la PR mergée, revenir sur main et synchroniser
gitmove branch switch main
git pull

# Nettoyer les branches de fonctionnalités terminées
gitmove clean
```

## Meilleures pratiques

### Optimisation de la configuration

- **Adaptez les seuils d'âge** : Définissez `age_threshold` en fonction de la vélocité de votre équipe
- **Utilisez les patterns d'exclusion** : Protégez les branches importantes avec `exclude_branches`
- **Combinez les fichiers et variables d'environnement** : Utilisez le fichier pour les paramètres stables et les variables d'environnement pour les paramètres changeants

### Automatisation

Intégrez GitMove dans vos scripts et workflows d'intégration continue :

```bash
# Exemple de script CI pour nettoyer les branches obsolètes
#!/bin/bash
export GITMOVE_GENERAL_VERBOSE=true
export GITMOVE_CLEAN_AGE_THRESHOLD=30
gitmove clean --remote --force
```

### Conventions de nommage

Adoptez des conventions de nommage cohérentes pour tirer le meilleur parti des fonctionnalités de pattern matching de GitMove :

- `feature/*` pour les nouvelles fonctionnalités
- `bugfix/*` pour les corrections de bugs
- `hotfix/*` pour les corrections urgentes
- `release/*` pour les branches de release

### Synchronisation régulière

Synchronisez vos branches régulièrement pour éviter les conflits de merge complexes :

```bash
# Ajouter un alias dans votre shell pour une synchronisation rapide
alias gms='gitmove sync'
```

## Résolution des problèmes

### Problèmes courants et solutions

#### La commande ne fonctionne pas comme prévu

**Symptôme** : La commande s'exécute mais ne produit pas le résultat attendu.

**Solutions** :
1. Vérifiez votre configuration : `gitmove config show`
2. Activez le mode verbeux : `gitmove --verbose [commande]` ou définissez `verbose = true` dans la configuration
3. Assurez-vous que les prérequis Git sont remplis (ex: commits locaux, accès au dépôt distant)

#### Erreurs de configuration

**Symptôme** : Messages d'erreur concernant la configuration.

**Solutions** :
1. Validez votre configuration : `gitmove config validate`
2. Vérifiez les conflits potentiels entre le fichier de configuration et les variables d'environnement
3. Générez et utilisez une configuration par défaut : `gitmove config generate`

#### Conflits lors de la synchronisation

**Symptôme** : La synchronisation échoue avec des conflits.

**Solutions** :
1. Résolvez les conflits manuellement dans les fichiers concernés
2. Marquez les fichiers comme résolus : `git add [fichiers]`
3. Continuez la synchronisation : `gitmove sync --continue`
4. Pour éviter les conflits futurs, synchronisez plus fréquemment

#### Nettoyage supprimant des branches importantes

**Symptôme** : Des branches que vous souhaitiez conserver ont été supprimées.

**Solutions** :
1. Utilisez toujours `--dry-run` avant un nettoyage réel
2. Ajoutez les branches importantes à `exclude_branches` dans la configuration
3. Utilisez l'option `--exclude` pour protéger certaines branches : `gitmove clean --exclude "important/*"`

### Logs de débogage

Pour un débogage avancé, vous pouvez activer les logs détaillés :

```bash
# Définir le niveau de log en variable d'environnement
export GITMOVE_LOG_LEVEL=DEBUG
gitmove [commande]

# Ou rediriger les logs vers un fichier
gitmove --verbose [commande] 2> gitmove.log
```

## Références

### Schéma de configuration complet

Référez-vous à la [documentation complète du schéma de configuration](link-to-config-schema) pour une liste exhaustive de toutes les options disponibles.

### Variables d'environnement

Toutes les options de configuration peuvent être définies via des variables d'environnement en suivant le format `GITMOVE_SECTION_OPTION`.

### Commandes Git sous-jacentes

GitMove utilise des commandes Git standard en arrière-plan. Pour les utilisateurs avancés qui souhaitent comprendre ce qui se passe, voici les commandes Git équivalentes aux commandes GitMove courantes :

| Commande GitMove | Commandes Git équivalentes |
|------------------|----------------------------|
| `gitmove branch create feature/new` | `git checkout -b feature/new` |
| `gitmove sync` | `git fetch origin main && git rebase origin/main` |
| `gitmove clean` | Combinaison complexe de `git branch`, `git for-each-ref`, etc. |

### Ressources supplémentaires

- [Site officiel de GitMove](https://gitmove.example.com)
- [Dépôt GitHub](https://github.com/gitmove/gitmove)
- [Documentation de l'API](https://docs.gitmove.example.com/api)
- [Forum communautaire](https://community.gitmove.example.com)

---

*Ce guide est maintenu par l'équipe GitMove. Dernière mise à jour : Mars 2025.*