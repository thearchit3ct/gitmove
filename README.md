# GitMove 🚀

[![Version PyPI](https://img.shields.io/pypi/v/gitmove.svg)](https://pypi.org/project/gitmove/)
[![Versions Python](https://img.shields.io/pypi/pyversions/gitmove.svg)](https://pypi.org/project/gitmove/)
[![Licence : MIT](https://img.shields.io/badge/Licence-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Introduction

GitMove est un gestionnaire de branches Git intelligent conçu pour simplifier et automatiser la gestion de vos workflows Git. Il offre des fonctionnalités avancées pour maintenir un environnement de développement propre et efficace avec une interface utilisateur intuitive et riche.

## ✨ Fonctionnalités Principales

### 1. Nettoyage Automatique des Branches
- Identification et suppression des branches obsolètes
- Personnalisation des critères de nettoyage
- Support des branches locales et distantes

- Visualisation claire des branches à nettoyer

### 2. Synchronisation Intelligente
- Synchronisation automatique avec la branche principale
- Stratégies de fusion et de rebase configurables
- Détection intelligente de la meilleure stratégie de synchronisation
- Barres de progression interactives pour les opérations longues

### 3. Gestion des Conflits
- Détection précoce des conflits potentiels
- Analyse détaillée avec visualisation des branches
- Mode interactif pour explorer les conflits un par un
- Suggestions de résolution adaptées au niveau de sévérité

### 4. Configuration Avancée
- Support complet des variables d'environnement
- Validation de configuration avec schéma extensible
- Génération de modèles de configuration
- Recommandations intelligentes pour l'optimisation

### 5. Interface Utilisateur Améliorée
- Interface en ligne de commande riche et colorée
- Visualisations des branches et de leurs relations
- Messages d'erreur informatifs avec suggestions de résolution
- Auto-complétion pour les shells (Bash, Zsh, Fish)

### 6. Intégration CI/CD
- Génération de workflows pour différentes plateformes
- Validation des noms de branches
- Détection automatique de l'environnement CI
- Export des analyses pour intégration dans les pipelines

## 🚀 Installation

```bash
pip install gitmove
```

### Prérequis
- Python 3.8+
- Git 2.x

### Installation de l'auto-complétion (optionnel)

Pour activer l'auto-complétion des commandes dans votre shell :

```bash
# Générer et installer automatiquement le script d'auto-complétion
gitmove completion --install

# Ou pour un shell spécifique
gitmove completion --shell zsh --install
```

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

### Vérification des Conflits

```bash
# Vérifier les conflits potentiels
gitmove check-conflicts

# Mode interactif pour explorer les conflits
gitmove check-conflicts --interactive

# Exporter les résultats d'analyse
gitmove check-conflicts --export rapport_conflits.json
```

### Obtenir des Conseils

```bash
# Obtenir un conseil de stratégie
gitmove advice

# Pour une branche spécifique
gitmove advice --branch feature/nouvelle-fonctionnalite
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

### Auto-complétion

```bash
# Générer un script d'auto-complétion pour votre shell
gitmove completion

# Installer l'auto-complétion
gitmove completion --install
```

## 🌈 Interface Utilisateur

GitMove propose une interface en ligne de commande riche et interactive:

- **Barres de progression** pour les opérations longues
- **Visualisations des branches** sous forme d'arbres ASCII
- **Tableaux colorés** pour une meilleure lisibilité
- **Messages d'erreur informatifs** avec suggestions de résolution
- **Mode interactif** pour l'exploration des conflits
- **Auto-complétion** des commandes et options

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