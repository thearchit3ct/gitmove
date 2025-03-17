# Documentation de l'amélioration du système de configuration de GitMove

## Vue d'ensemble

GitMove a récemment bénéficié d'importantes améliorations de son système de gestion de configuration, avec l'introduction de deux nouveaux modules :

1. **ConfigValidator** - Un système de validation avancé pour les fichiers de configuration
2. **EnvConfigLoader** - Un chargeur de configuration basé sur les variables d'environnement

Ces améliorations permettent une configuration plus robuste, plus flexible et une meilleure expérience utilisateur grâce à la validation détaillée et au support multi-sources.

## Nouvelles fonctionnalités

### Validation de configuration avancée

Le module `ConfigValidator` offre :

- **Validation basée sur un schéma** - Définition stricte des paramètres attendus avec leurs types et contraintes
- **Rapports d'erreur détaillés** - Messages d'erreur clairs avec formatage enrichi via Rich
- **Interpolation des variables d'environnement** - Support des variables d'environnement directement dans les fichiers de configuration
- **Recommandations de configuration** - Suggestions pour optimiser la configuration en fonction des paramètres actuels
- **Génération de configuration** - Possibilité de créer des fichiers de configuration d'exemple

### Support des variables d'environnement

Le module `EnvConfigLoader` fournit :

- **Configuration hiérarchique** - Support de structures de configuration imbriquées via les variables d'environnement
- **Conversion de types intelligente** - Détection automatique des types de données (booléens, nombres, JSON)
- **Fusion de configuration** - Intégration transparente avec les configurations existantes
- **Support JSON** - Possibilité d'encoder des structures complexes dans les variables d'environnement

## Utilisation

### Configuration via fichier TOML

GitMove utilise désormais les fichiers TOML pour sa configuration. Voici un exemple de configuration :

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

### Configuration via variables d'environnement

Toutes les options peuvent également être configurées via des variables d'environnement avec le préfixe `GITMOVE_` :

```bash
# Configuration générale
export GITMOVE_GENERAL_MAIN_BRANCH="main"
export GITMOVE_GENERAL_VERBOSE=false

# Configuration du nettoyage
export GITMOVE_CLEAN_AUTO_CLEAN=false
export GITMOVE_CLEAN_EXCLUDE_BRANCHES='["develop", "staging"]'
export GITMOVE_CLEAN_AGE_THRESHOLD=30

# Configuration de synchronisation
export GITMOVE_SYNC_DEFAULT_STRATEGY="rebase"
export GITMOVE_SYNC_AUTO_SYNC=true
```

## Schéma de configuration

Le schéma de configuration complet est défini comme suit :

| Section | Option | Type | Requis | Valeur par défaut | Description |
|---------|--------|------|--------|------------------|-------------|
| general | main_branch | string | Oui | "main" | Nom de la branche principale du dépôt |
| general | verbose | boolean | Non | false | Active le mode verbeux pour plus de détails |
| clean | auto_clean | boolean | Non | false | Active le nettoyage automatique des branches |
| clean | exclude_branches | liste de strings | Non | ["develop", "staging"] | Branches à exclure du nettoyage |
| clean | age_threshold | entier (1-365) | Non | 30 | Âge minimum (en jours) pour qu'une branche soit éligible au nettoyage |
| sync | default_strategy | string | Non | "rebase" | Stratégie par défaut pour la synchronisation (merge, rebase, auto) |
| sync | auto_sync | boolean | Non | true | Active la synchronisation automatique des branches |

## Commandes CLI

De nouvelles commandes ont été ajoutées pour gérer la configuration :

```bash
# Générer un fichier de configuration d'exemple
gitmove config generate --output ~/.config/gitmove/config.toml

# Valider un fichier de configuration existant
gitmove config validate --config ~/.config/gitmove/config.toml
```

## Emplacement par défaut du fichier de configuration

- **Linux/macOS** : `~/.config/gitmove/config.toml`
- **Windows** : `~\.gitmove\config.toml`

## Validation et gestion des erreurs

Le système de validation fournit des messages d'erreur détaillés et formatés pour faciliter la correction :

- Erreurs de type (par exemple, un entier attendu mais une chaîne fournie)
- Valeurs hors limites (par exemple, age_threshold doit être entre 1 et 365)
- Options requises manquantes
- Formats invalides pour les valeurs de chaîne
- Avertissements pour les sections ou options inconnues

## Recommandations

Le système peut également fournir des recommandations basées sur la configuration actuelle, comme :

- Suggestions pour désactiver le mode verbeux en production
- Recommandations pour ajuster les seuils de nettoyage des branches
- Conseils sur l'utilisation de la synchronisation automatique

## Intégration avec d'autres composants

Ces nouveaux modules de configuration sont conçus pour s'intégrer facilement avec les autres composants de GitMove et peuvent être utilisés indépendamment pour d'autres besoins de configuration.

## Exemple d'utilisation avancée

```python
from gitmove.config import ConfigValidator, EnvConfigLoader

# Charger la configuration depuis le fichier par défaut
validator = ConfigValidator()
config = validator.validate_config()

# Enrichir avec les variables d'environnement
env_config = EnvConfigLoader.load_from_env(config)

# Utiliser la configuration
main_branch = env_config.get('general', {}).get('main_branch', 'main')
```

## Limitations connues

- L'interpolation des variables d'environnement ne supporte pas les valeurs par défaut (par exemple, `${VAR:-default}`)
- La validation ne prend pas encore en charge les schémas récursifs ou très complexes

## Prochaines étapes

Les développements futurs pourraient inclure :

- Support pour d'autres formats de configuration (YAML, JSON)
- Interface web pour la gestion de la configuration
- Plus d'options pour la configuration spécifique à l'environnement (dev, staging, prod)