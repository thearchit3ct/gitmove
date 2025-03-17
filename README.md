# GitMove 🚀

[![Version PyPI](https://img.shields.io/pypi/v/gitmove.svg)](https://pypi.org/project/gitmove/)
[![Versions Python](https://img.shields.io/pypi/pyversions/gitmove.svg)](https://pypi.org/project/gitmove/)
[![Licence : MIT](https://img.shields.io/badge/Licence-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Introduction

GitMove est un gestionnaire de branches Git intelligent conçu pour simplifier et automatiser la gestion de vos workflows Git. Il offre des fonctionnalités avancées pour maintenir un environnement de développement propre et efficace.

## ✨ Fonctionnalités Principales

### 1. Nettoyage Automatique des Branches
- Identification et suppression des branches obsolètes
- Personnalisation des critères de nettoyage
- Support des branches locales et distantes

### 2. Synchronisation Intelligente
- Synchronisation automatique avec la branche principale
- Stratégies de fusion et de rebase configurables
- Détection intelligente du meilleur stratégie de synchronisation

### 3. Gestion des Conflits
- Détection précoce des conflits potentiels
- Suggestions de résolution de conflits
- Analyse détaillée des modifications

### 4. Configuration Avancée
- Support complet des variables d'environnement
- Validation de configuration
- Génération de modèles de configuration

### 5. Intégration CI/CD
- Génération de workflows pour différentes plateformes
- Validation des noms de branches
- Détection automatique de l'environnement CI

## 🚀 Installation

```bash
pip install gitmove
```

### Prérequis
- Python 3.8+
- Git 2.x

## 🔧 Configuration

### Configuration Globale
Créez un fichier de configuration global :

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
```

### Variables d'Environnement
Configurez GitMove via des variables d'environnement :

```bash
export GITMOVE_GENERAL_VERBOSE=true
export GITMOVE_SYNC_DEFAULT_STRATEGY=merge
```

## 📋 Utilisation

### Nettoyage des Branches

```bash
# Afficher les branches fusionnées
gitmove clean --dry-run

# Nettoyer les branches locales
gitmove clean

# Nettoyer les branches locales et distantes
gitmove clean --remote
```

### Synchronisation

```bash
# Synchroniser la branche courante
gitmove sync

# Spécifier une stratégie
gitmove sync --strategy rebase
```

### Gestion de Configuration

```bash
# Générer un modèle de configuration
gitmove config generate

# Valider la configuration
gitmove config validate
```

### Intégration CI/CD

```bash
# Générer un workflow GitHub Actions
gitmove cicd generate-workflow --platform github_actions

# Valider le nom d'une branche
gitmove cicd validate-branch feature/nouvelle-fonctionnalite
```

## 🤝 Contribution

### Installation de Développement

```bash
# Cloner le dépôt
git clone https://github.com/votre-nom/gitmove.git
cd gitmove

# Installer en mode développement
pip install -e ".[dev]"

# Exécuter les tests
pytest
```

### Directives de Contribution
1. Fork du projet
2. Créez votre branche de fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Commitez vos modifications (`git commit -m 'Ajouter une nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une Pull Request

## 📄 Licence

Distribué sous la Licence MIT. Voir `LICENSE` pour plus de détails.

## 🔗 Liens Utiles

- Documentation : [Lien vers la documentation]
- Rapporter un problème : [Lien vers les issues]
- Discussions : [Lien vers les discussions]

---

**Fait avec ❤️ par la communauté GitMove**