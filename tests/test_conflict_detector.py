"""
Tests pour le détecteur de conflits.

Ce module teste les fonctionnalités de ConflictDetector.
"""

import os
import pytest

from gitmove.core.conflict_detector import ConflictDetector


def test_init(configured_git_repo, gitmove_config):
    """Teste l'initialisation du détecteur de conflits."""
    conflict_detector = ConflictDetector(configured_git_repo, gitmove_config)
    
    assert conflict_detector.repo == configured_git_repo
    assert conflict_detector.config == gitmove_config
    assert conflict_detector.main_branch == "main"
    assert conflict_detector.show_diff is True  # valeur par défaut


def test_detect_conflicts_no_conflict(multi_branch_repo, gitmove_config):
    """Teste la détection quand il n'y a pas de conflit."""
    conflict_detector = ConflictDetector(multi_branch_repo, gitmove_config)
    
    # La branche feature/a ne devrait pas avoir de conflit avec main
    # car elle modifie un fichier distinct
    result = conflict_detector.detect_conflicts("feature/a", "main")
    
    assert result["has_conflicts"] is False
    assert len(result.get("conflicting_files", [])) == 0


def test_detect_conflicts_with_conflict(conflict_repo, gitmove_config):
    """Teste la détection quand il y a des conflits."""
    conflict_detector = ConflictDetector(conflict_repo, gitmove_config)
    
    # La branche feature/conflict devrait avoir un conflit avec main
    result = conflict_detector.detect_conflicts("feature/conflict", "main")
    
    assert result["has_conflicts"] is True
    assert len(result.get("conflicting_files", [])) > 0
    
    # Vérifier que conflict_file.txt est détecté comme étant en conflit
    conflict_files = [file["file_path"] for file in result.get("conflicting_files", [])]
    assert "conflict_file.txt" in conflict_files


def test_conflict_classification(conflict_repo, gitmove_config):
    """Teste la classification des conflits."""
    conflict_detector = ConflictDetector(conflict_repo, gitmove_config)
    
    # Détecter les conflits
    result = conflict_detector.detect_conflicts("feature/conflict", "main")
    
    # Vérifier qu'il y a des conflits
    assert result["has_conflicts"] is True
    
    # Vérifier les détails du conflit
    conflict_file = next(
        (file for file in result.get("conflicting_files", []) if file["file_path"] == "conflict_file.txt"),
        None
    )
    
    assert conflict_file is not None
    assert "severity" in conflict_file
    assert "conflict_type" in conflict_file
    assert "modified_lines" in conflict_file


def test_conflict_suggestions(conflict_repo, gitmove_config):
    """Teste les suggestions générées en cas de conflits."""
    conflict_detector = ConflictDetector(conflict_repo, gitmove_config)
    
    # Détecter les conflits
    result = conflict_detector.detect_conflicts("feature/conflict", "main")
    
    # Vérifier qu'il y a des suggestions
    assert "suggestions" in result
    assert len(result["suggestions"]) > 0


def test_same_branch_no_conflict(configured_git_repo, gitmove_config):
    """Teste qu'il n'y a pas de conflit quand on compare une branche avec elle-même."""
    conflict_detector = ConflictDetector(configured_git_repo, gitmove_config)
    
    result = conflict_detector.detect_conflicts("main", "main")
    
    assert result["has_conflicts"] is False


def test_conflict_severity_levels(conflict_repo, gitmove_config):
    """Teste les différents niveaux de gravité des conflits."""
    # Modifier le fichier conflict_file.txt pour créer des conflits plus graves
    repo = conflict_repo
    repo_path = repo.working_dir
    
    # Créer une nouvelle branche avec des modifications plus significatives
    repo.git.checkout("-b", "feature/major-conflict")
    
    # Ajouter un import ou une fonction qui créera un conflit grave
    file_path = os.path.join(repo_path, "code_file.py")
    with open(file_path, "w") as f:
        f.write("def main_function():\n    return 'feature version'\n\nimport sys\n")
    
    repo.git.add("code_file.py")
    repo.git.commit("-m", "Add Python code in feature branch", author="Test User <test@example.com>")
    
    # Revenir à main et créer une version différente
    repo.git.checkout("main")
    
    with open(file_path, "w") as f:
        f.write("def main_function():\n    return 'main version'\n\nimport os\n")
    
    repo.git.add("code_file.py")
    repo.git.commit("-m", "Add Python code in main branch", author="Test User <test@example.com>")
    
    # Détecter les conflits
    conflict_detector = ConflictDetector(repo, gitmove_config)
    result = conflict_detector.detect_conflicts("feature/major-conflict", "main")
    
    # Vérifier la gravité du conflit
    assert result["has_conflicts"] is True
    
    python_file_conflict = next(
        (file for file in result.get("conflicting_files", []) if file["file_path"] == "code_file.py"),
        None
    )
    
    assert python_file_conflict is not None
    # Le conflit sur import ou fonction devrait être classé comme Élevée
    assert python_file_conflict["severity"] == "Élevée"