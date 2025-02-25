# Tests GitMove

Ce répertoire contient les tests unitaires et d'intégration pour le projet GitMove.

## Structure des tests

Les tests sont organisés par composant testé :

- `test_branch_manager.py` : Tests pour le gestionnaire de branches
- `test_conflict_detector.py` : Tests pour le détecteur de conflits
- `test_sync_manager.py` : Tests pour le gestionnaire de synchronisation
- `test_strategy_advisor.py` : Tests pour le conseiller de stratégie
- `test_git_commands.py` : Tests pour les commandes Git de base
- `test_validators.py` : Tests pour les validateurs
- `test_config.py` : Tests pour la gestion de la configuration
- `test_cli.py` : Tests pour l'interface en ligne de commande

## Fixtures

Les fixtures réutilisables sont définies dans `conftest.py` :

- `temp_dir` : Fournit un répertoire temporaire pour les tests
- `git_repo` : Crée un dépôt Git minimal pour les tests
- `configured_git_repo` : Un dépôt Git avec une configuration GitMove
- `multi_branch_repo` : Un dépôt avec plusieurs branches dans différents états
- `conflict_repo` : Un dépôt avec des branches qui génèrent des conflits
- `gitmove_config` : Une instance préconfigurée de Config

## Exécution des tests

Pour exécuter tous les tests :

```bash
pytest
```

Pour exécuter un fichier de test spécifique :

```bash
pytest tests/test_branch_manager.py
```

Pour exécuter un test spécifique :

```bash
pytest tests/test_branch_manager.py::test_find_merged_branches
```

Pour obtenir une couverture de code :

```bash
pytest --cov=gitmove tests/
```

## Bonnes pratiques

Lors de l'écriture de nouveaux tests :

1. **Utilisez les fixtures existantes** plutôt que de créer des environnements de test à chaque fois
2. **Isolez les tests** pour qu'ils ne dépendent pas de l'état d'autres tests
3. **Nommez clairement les tests** pour indiquer ce qu'ils vérifient
4. **Utilisez des assertions spécifiques** qui donnent des messages d'erreur clairs
5. **Vérifiez les cas limites et d'erreur** en plus des cas normaux
6. **Nettoyez les ressources** créées pendant les tests

## Dépannage

### Problèmes courants

- **Tests Git échouant avec GitCommandError** : Vérifiez que git est correctement installé et accessible dans le PATH
- **Erreurs de permission** : Assurez-vous que les répertoires temporaires sont accessibles en lecture/écriture
- **Tests intermittents** : Certains tests peuvent échouer occasionnellement si git n'a pas le temps de terminer une opération

### Conseils

- Utilisez `pytest -v` pour un affichage plus détaillé
- Ajoutez `--showlocals` pour voir les variables locales en cas d'échec
- L'option `-s` désactive la capture de sortie pour faciliter le débogage