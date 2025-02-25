"""
Tests pour l'interface en ligne de commande.

Ce module teste les commandes CLI de GitMove.
"""

import os
import tempfile
import shutil
import pytest
from click.testing import CliRunner

from gitmove.cli import cli, main


@pytest.fixture
def cli_runner():
    """Fournit un runner pour tester les commandes CLI."""
    return CliRunner()


def test_cli_version(cli_runner):
    """Teste la commande d'affichage de version."""
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "GitMove" in result.output
    assert "0.1.0" in result.output


def test_cli_help(cli_runner):
    """Teste la commande d'aide."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "GitMove" in result.output
    assert "Options:" in result.output
    assert "Commands:" in result.output
    
    # Vérifier que toutes les commandes principales sont listées
    assert "init " in result.output
    assert "clean " in result.output
    assert "sync " in result.output
    assert "advice " in result.output
    assert "check-conflicts " in result.output
    assert "status " in result.output


def test_cli_init_help(cli_runner):
    """Teste l'aide de la commande init."""
    result = cli_runner.invoke(cli, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialise la configuration" in result.output


@pytest.mark.parametrize("command", [
    "clean",
    "sync",
    "advice",
    "check-conflicts",
    "status",
])
def test_cli_command_help(cli_runner, command):
    """Teste l'aide de différentes commandes."""
    result = cli_runner.invoke(cli, [command, "--help"])
    assert result.exit_code == 0
    assert command in result.output.lower()


def test_cli_init_command(cli_runner, temp_dir, monkeypatch):
    """Teste la commande init."""
    # Créer un dépôt Git temporaire
    repo_path = os.path.join(temp_dir, "test-repo")
    os.makedirs(repo_path)
    os.chdir(repo_path)
    os.system("git init")
    
    # Exécuter la commande dans le contexte du dépôt temporaire
    monkeypatch.chdir(repo_path)
    
    result = cli_runner.invoke(cli, ["init"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    assert "Configuration initialisée avec succès" in result.output
    
    # Vérifier que le fichier de configuration a été créé
    config_path = os.path.join(repo_path, ".gitmove.toml")
    assert os.path.exists(config_path)


def test_cli_clean_dry_run(cli_runner, multi_branch_repo, monkeypatch):
    """Teste la commande clean avec l'option dry-run."""
    repo_path = multi_branch_repo.working_dir
    
    # Exécuter la commande dans le contexte du dépôt
    monkeypatch.chdir(repo_path)
    
    # Créer une configuration GitMove
    config_path = os.path.join(repo_path, ".gitmove.toml")
    with open(config_path, "w") as f:
        f.write("""
[general]
main_branch = "main"
        """)
    
    result = cli_runner.invoke(cli, ["clean", "--dry-run"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    
    # Vérifier que les branches fusionnées sont détectées
    assert "Branches fusionnées à nettoyer" in result.output
    assert "feature/b" in result.output
    assert "release/1.0" in result.output
    
    # Vérifier que le mode dry-run est mentionné
    assert "Mode dry-run" in result.output


def test_cli_status(cli_runner, multi_branch_repo, monkeypatch):
    """Teste la commande status."""
    repo_path = multi_branch_repo.working_dir
    
    # Exécuter la commande dans le contexte du dépôt
    monkeypatch.chdir(repo_path)
    
    # Créer une configuration GitMove
    config_path = os.path.join(repo_path, ".gitmove.toml")
    with open(config_path, "w") as f:
        f.write("""
[general]
main_branch = "main"
        """)
    
    result = cli_runner.invoke(cli, ["status"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    
    # Vérifier les informations de base
    assert "Branche courante:" in result.output
    assert "main" in result.output
    assert "Branche principale:" in result.output


def test_cli_status_detailed(cli_runner, multi_branch_repo, monkeypatch):
    """Teste la commande status avec l'option detailed."""
    repo_path = multi_branch_repo.working_dir
    
    # Exécuter la commande dans le contexte du dépôt
    monkeypatch.chdir(repo_path)
    
    # Créer une configuration GitMove
    config_path = os.path.join(repo_path, ".gitmove.toml")
    with open(config_path, "w") as f:
        f.write("""
[general]
main_branch = "main"
        """)
    
    result = cli_runner.invoke(cli, ["status", "--detailed"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    
    # Vérifier les informations détaillées
    assert "Branches fusionnées" in result.output


def test_cli_advice(cli_runner, multi_branch_repo, monkeypatch):
    """Teste la commande advice."""
    repo_path = multi_branch_repo.working_dir
    
    # Passer à la branche feature/a
    multi_branch_repo.git.checkout("feature/a")
    
    # Exécuter la commande dans le contexte du dépôt
    monkeypatch.chdir(repo_path)
    
    # Créer une configuration GitMove
    config_path = os.path.join(repo_path, ".gitmove.toml")
    with open(config_path, "w") as f:
        f.write("""
[general]
main_branch = "main"

[advice]
rebase_threshold = 5
        """)
    
    result = cli_runner.invoke(cli, ["advice"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    
    # Vérifier les informations de base
    assert "Stratégie recommandée:" in result.output
    # La stratégie peut être "rebase" ou "merge" selon le contexte
    assert any(strategy in result.output for strategy in ["rebase", "merge"])
    assert "Raison:" in result.output


def test_cli_check_conflicts(cli_runner, conflict_repo, monkeypatch):
    """Teste la commande check-conflicts."""
    repo_path = conflict_repo.working_dir
    
    # Passer à la branche feature/conflict
    conflict_repo.git.checkout("feature/conflict")
    
    # Exécuter la commande dans le contexte du dépôt
    monkeypatch.chdir(repo_path)
    
    # Créer une configuration GitMove
    config_path = os.path.join(repo_path, ".gitmove.toml")
    with open(config_path, "w") as f:
        f.write("""
[general]
main_branch = "main"
        """)
    
    result = cli_runner.invoke(cli, ["check-conflicts"])
    
    # Vérifier que la commande a réussi
    assert result.exit_code == 0
    
    # Vérifier les informations sur les conflits
    assert "Conflits potentiels détectés" in result.output
    assert "Fichiers en conflit" in result.output
    assert "conflict_file.txt" in result.output


def test_cli_sync(cli_runner, multi_branch_repo, monkeypatch):
    """Teste la commande sync."""
    repo_path = multi_branch_repo.working_dir
    
    # Passer à la branche feature/a
    multi_branch_repo.git.checkout("feature/a")
    
    # Exécuter la commande dans le contexte du dépôt
    monkeypatch.chdir(repo_path)
    
    # Créer une configuration GitMove
    config_path = os.path.join(repo_path, ".gitmove.toml")
    with open(config_path, "w") as f:
        f.write("""
[general]
main_branch = "main"

[sync]
default_strategy = "rebase"
        """)
    
    result = cli_runner.invoke(cli, ["sync"])
    
    # La commande peut réussir ou détecter des conflits selon le contexte
    assert result.exit_code == 0
    assert any(msg in result.output for msg in [
        "Synchronisation réussie",
        "Synchronisation incomplète",
        "Conflits potentiels détectés"
    ])


def test_main_function(monkeypatch):
    """Teste la fonction main (point d'entrée)."""
    # Utiliser monkeypatch pour simuler l'appel à cli()
    called = False
    
    def mock_cli():
        nonlocal called
        called = True
    
    monkeypatch.setattr("gitmove.cli.cli", mock_cli)
    
    # Appeler la fonction main
    main()
    
    # Vérifier que cli() a été appelé
    assert called is True