# Guide de Configuration CI/CD pour GitMove

Ce guide explique comment configurer l'environnement CI/CD pour le projet GitMove, en utilisant GitHub Actions pour l'automatisation des tests et du déploiement.

## Table des matières

1. [Prérequis](#prérequis)
2. [Structure des Tests](#structure-des-tests)
3. [Configuration des GitHub Actions](#configuration-des-github-actions)
4. [Déploiement Automatique](#déploiement-automatique)
5. [Variables d'Environnement et Secrets](#variables-denvironnement-et-secrets)
6. [Badges de Statut](#badges-de-statut)
7. [Résolution des Problèmes](#résolution-des-problèmes)

## Prérequis

Pour utiliser l'environnement CI/CD, vous aurez besoin de :

- Un compte GitHub
- Un dépôt GitHub contenant le code du projet GitMove
- Droits d'administrateur sur ce dépôt
- Pour le déploiement sur PyPI : un compte PyPI et un compte TestPyPI

## Structure des Tests

Le projet GitMove utilise plusieurs niveaux de tests :

### Tests Unitaires

Les tests unitaires se trouvent dans le répertoire `tests/` et sont nommés `test_*.py`. Ils vérifient le comportement de composants individuels.

```bash
# Exécuter les tests unitaires
pytest tests/
```

### Tests d'Intégration

Les tests d'intégration vérifient les interactions entre plusieurs composants du système.

```bash
# Exécuter les tests d'intégration
pytest tests/integration/
```

### Couverture de Code

La couverture de code est mesurée à l'aide de pytest-cov.

```bash
# Exécuter les tests avec couverture
pytest --cov=gitmove --cov-report=xml --cov-report=term
```

### Validation de la Qualité du Code

La qualité du code est vérifiée à l'aide de plusieurs outils :

- **Black** : formatage du code
- **isort** : tri des imports
- **flake8** : vérification du style et détection des erreurs
- **mypy** : vérification des types

```bash
# Vérifier le formatage
black --check src tests

# Vérifier les imports
isort --check-only --profile black src tests

# Vérifier le style
flake8 src tests

# Vérifier les types
mypy src
```

## Configuration des GitHub Actions

Le projet utilise GitHub Actions pour l'automatisation des tests et du déploiement. Les workflows sont définis dans le répertoire `.github/workflows/`.

### Flux de Travail Principal

Le fichier principal est `gitmove-tests.yml`, qui définit les étapes à exécuter lors des push et pull requests.

1. Créez le répertoire `.github/workflows/` s'il n'existe pas :

```bash
mkdir -p .github/workflows
```

2. Copiez le fichier de workflow à cet emplacement :

```bash
cp chemin/vers/gitmove-tests.yml .github/workflows/
```

### Activation des GitHub Actions

Les GitHub Actions sont automatiquement activées lorsque des fichiers de workflow sont présents dans le dépôt. Vérifiez que les actions sont bien activées dans les paramètres du dépôt GitHub :

1. Allez dans l'onglet "Settings" de votre dépôt
2. Sélectionnez "Actions" dans le menu de gauche
3. Assurez-vous que l'option "Allow all actions and reusable workflows" est sélectionnée

## Déploiement Automatique

Le projet est configuré pour un déploiement automatique sur PyPI lors de la création d'une release GitHub.

### Configuration du Déploiement

1. Configurez les secrets GitHub pour PyPI (voir section suivante)
2. Pour publier une nouvelle version :
   - Mettez à jour la version dans `pyproject.toml`
   - Créez une nouvelle release GitHub avec un tag correspondant
   - Le workflow de déploiement s'exécutera automatiquement

### Déploiement sur TestPyPI

Les versions de développement sont automatiquement déployées sur TestPyPI depuis la branche `develop`.

## Variables d'Environnement et Secrets

Les variables d'environnement et secrets suivants doivent être configurés dans les paramètres du dépôt GitHub :

### Secrets Requis

- `PYPI_USERNAME` : Nom d'utilisateur PyPI
- `PYPI_PASSWORD` : Mot de passe ou token PyPI
- `TEST_PYPI_USERNAME` : Nom d'utilisateur TestPyPI
- `TEST_PYPI_PASSWORD` : Mot de passe ou token TestPyPI

Pour configurer ces secrets :

1. Allez dans l'onglet "Settings" de votre dépôt
2. Sélectionnez "Secrets and variables" puis "Actions" dans le menu de gauche
3. Cliquez sur "New repository secret" et ajoutez chaque secret un par un

### Variables d'Environnement Optionnelles

Vous pouvez également configurer des variables d'environnement pour personnaliser le comportement des workflows :

- `COVERAGE_THRESHOLD` : Seuil minimum de couverture de code (par défaut : 80)
- `SKIP_INTEGRATION_TESTS` : Définir à "true" pour ignorer les tests d'intégration

Pour configurer ces variables :

1. Allez dans l'onglet "Settings" de votre dépôt
2. Sélectionnez "Secrets and variables" puis "Actions" dans le menu de gauche
3. Allez dans l'onglet "Variables" et ajoutez chaque variable

## Badges de Statut

Vous pouvez ajouter des badges de statut à votre README.md pour afficher l'état des workflows CI/CD :

```markdown
[![Tests](https://github.com/username/gitmove/actions/workflows/gitmove-tests.yml/badge.svg)](https://github.com/username/gitmove/actions/workflows/gitmove-tests.yml)
[![PyPI version](https://badge.fury.io/py/gitmove.svg)](https://badge.fury.io/py/gitmove)
[![codecov](https://codecov.io/gh/username/gitmove/branch/main/graph/badge.svg)](https://codecov.io/gh/username/gitmove)
```

N'oubliez pas de remplacer `username` par votre nom d'utilisateur GitHub ou celui de votre organisation.

## Résolution des Problèmes

### Les tests échouent dans GitHub Actions mais passent en local

Cela peut être dû à plusieurs raisons :

1. **Différences d'environnement** : Assurez-vous que les dépendances sont correctement spécifiées dans `pyproject.toml` et `tox.ini`.
2. **Problèmes liés à Git** : Les tests d'intégration créent des dépôts Git temporaires. Assurez-vous que la configuration Git est correcte dans les workflows.
3. **Problèmes de chemin** : Vérifiez que les chemins relatifs dans les tests fonctionnent correctement dans un environnement CI.

Solution : Examinez les logs de CI et essayez de reproduire l'environnement CI localement avec tox.

### Échec du déploiement sur PyPI

Si le déploiement sur PyPI échoue, vérifiez les points suivants :

1. Assurez-vous que les secrets `PYPI_USERNAME` et `PYPI_PASSWORD` sont correctement configurés.
2. Vérifiez que la version spécifiée dans `pyproject.toml` n'existe pas déjà sur PyPI.
3. Assurez-vous que le package est correctement construit (vérifiez les artefacts de build).

Solution : Essayez un déploiement manuel pour identifier le problème spécifique.

## Procédure de Test Complète

Pour exécuter l'ensemble complet des tests localement, comme le ferait GitHub Actions, utilisez tox :

```bash
# Installer tox
pip install tox

# Exécuter tous les environnements de test
tox

# Exécuter un environnement spécifique
tox -e py310  # Tests Python 3.10
tox -e lint   # Vérifications de qualité du code
tox -e coverage  # Tests avec couverture
```

## Intégration avec d'autres Services CI/CD

Bien que ce guide se concentre sur GitHub Actions, GitMove peut être intégré à d'autres services CI/CD :

### GitLab CI/CD

1. Créez un fichier `.gitlab-ci.yml` à la racine du projet
2. Utilisez le générateur de workflow CI/CD intégré à GitMove :
   ```bash
   gitmove cicd generate-workflow --platform gitlab_ci --output .gitlab-ci.yml
   ```

### Jenkins

1. Créez un `Jenkinsfile` à la racine du projet
2. Utilisez le générateur de workflow CI/CD intégré à GitMove :
   ```bash
   gitmove cicd generate-workflow --platform jenkins --output Jenkinsfile
   ```

### Travis CI

1. Créez un fichier `.travis.yml` à la racine du projet
2. Utilisez le générateur de workflow CI/CD intégré à GitMove :
   ```bash
   gitmove cicd generate-workflow --platform travis_ci --output .travis.yml
   ```

## Workflows Spécifiques

### Pull Requests

Pour les pull requests, le workflow exécute les tests et les vérifications de qualité du code, mais ne déploie pas le package.

### Déploiement de la Documentation

Un workflow séparé peut être configuré pour déployer automatiquement la documentation sur GitHub Pages :

```yaml
name: Deploy Documentation

on:
  push:
    branches: [ main ]
    paths:
      - 'doc/**'
      - 'mkdocs.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install mkdocs-material
      - name: Deploy documentation
        run: mkdocs gh-deploy --force
```

## Automatisation Supplémentaire

### Publication des Releases

Vous pouvez automatiser la création des releases GitHub à l'aide de l'outil `semantic-release` :

1. Configurez `semantic-release` dans votre projet
2. Ajoutez un workflow pour exécuter `semantic-release` lorsque des commits sont poussés vers `main`

### Tests de Sécurité

Vous pouvez ajouter des tests de sécurité à votre pipeline CI/CD :

```yaml
security:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install bandit safety
    - name: Run security checks
      run: |
        bandit -r src/
        safety check
```

## Conclusion

Avec cette configuration, vous disposez d'un pipeline CI/CD complet qui :

1. Exécute les tests unitaires et d'intégration sur plusieurs versions de Python
2. Vérifie la qualité du code avec plusieurs outils
3. Mesure la couverture du code
4. Déploie automatiquement sur TestPyPI pour les versions de développement
5. Déploie automatiquement sur PyPI pour les releases
6. Construit et publie des images Docker

Ce pipeline garantit que le code maintient un haut niveau de qualité et facilite le processus de release.