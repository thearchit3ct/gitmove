import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import datetime

# Ajouter le répertoire src au path pour pouvoir importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gitmove.core.branch_manager import BranchManager
from gitmove.exceptions import BranchError, MissingBranchError

class TestBranchManager(unittest.TestCase):
    """
    Tests unitaires pour le gestionnaire de branches.
    """
    
    def setUp(self):
        """Initialiser les tests"""
        # Créer des mocks pour Repo, Git et Config
        self.repo_mock = MagicMock()
        self.git_mock = MagicMock()
        self.config_mock = MagicMock()
        
        # Configurer les valeurs de retour des mocks
        self.repo_mock.working_dir = "/fake/path"
        self.repo_mock.git = self.git_mock
        self.config_mock.get_value.return_value = "main"
        
        # Créer le branch manager avec les mocks
        self.branch_manager = BranchManager(self.repo_mock, self.config_mock)
        self.branch_manager.git = self.git_mock  # Remplacer le Git créé par le mock
    
    def test_get_current_branch(self):
        """Tester la récupération de la branche courante"""
        # Arrange
        self.repo_mock.active_branch.name = "feature/test"
        
        # Act
        current_branch = self.branch_manager.get_current_branch()
        
        # Assert
        self.assertEqual(current_branch, "feature/test")
    
    def test_get_current_branch_detached_head(self):
        """Tester la récupération de la branche courante avec HEAD détaché"""
        # Arrange
        self.repo_mock.active_branch.name.side_effect = TypeError("HEAD is detached")
        self.git_mock.rev_parse.return_value = "abc1234"
        
        with patch("gitmove.core.branch_manager.get_current_branch", return_value="abc1234"):
            # Act
            current_branch = self.branch_manager.get_current_branch()
            
            # Assert
            self.assertEqual(current_branch, "abc1234")
    
    def test_list_branches(self):
        """Tester la récupération de la liste des branches"""
        # Arrange
        branch1 = MagicMock()
        branch1.name = "main"
        branch2 = MagicMock()
        branch2.name = "feature/test"
        self.repo_mock.heads = [branch1, branch2]
        
        # Configurer le mock pour _get_branch_info
        self.branch_manager._get_branch_info = MagicMock()
        self.branch_manager._get_branch_info.side_effect = [
            {"name": "main", "is_remote": False},
            {"name": "feature/test", "is_remote": False}
        ]
        
        # Act
        branches = self.branch_manager.list_branches()
        
        # Assert
        self.assertEqual(len(branches), 2)
        self.assertEqual(branches[0]["name"], "main")
        self.assertEqual(branches[1]["name"], "feature/test")
        
        # Vérifier les appels à _get_branch_info
        self.branch_manager._get_branch_info.assert_has_calls([
            call("main", False),
            call("feature/test", False)
        ])
    
    def test_list_branches_with_remote(self):
        """Tester la récupération de la liste des branches incluant les branches distantes"""
        # Arrange
        # Branches locales
        branch1 = MagicMock()
        branch1.name = "main"
        branch2 = MagicMock()
        branch2.name = "feature/test"
        self.repo_mock.heads = [branch1, branch2]
        
        # Branches distantes
        remote_ref1 = MagicMock()
        remote_ref1.name = "origin/main"
        remote_ref2 = MagicMock()
        remote_ref2.name = "origin/feature/remote"
        remote_ref3 = MagicMock()
        remote_ref3.name = "origin/HEAD"
        self.repo_mock.remotes.origin.refs = [remote_ref1, remote_ref2, remote_ref3]
        
        # Configurer le mock pour _get_branch_info
        self.branch_manager._get_branch_info = MagicMock()
        self.branch_manager._get_branch_info.side_effect = [
            {"name": "main", "is_remote": False},
            {"name": "feature/test", "is_remote": False},
            {"name": "feature/remote", "is_remote": True}
        ]
        
        # Act
        branches = self.branch_manager.list_branches(include_remote=True)
        
        # Assert
        self.assertEqual(len(branches), 3)
        self.assertEqual(branches[0]["name"], "main")
        self.assertEqual(branches[1]["name"], "feature/test")
        self.assertEqual(branches[2]["name"], "feature/remote")
        
        # Vérifier les appels à _get_branch_info
        self.branch_manager._get_branch_info.assert_has_calls([
            call("main", False),
            call("feature/test", False),
            call("feature/remote", True)
        ])
    
    def test_get_branch_info(self):
        """Tester la récupération des informations d'une branche"""
        # Arrange
        with patch("gitmove.core.branch_manager.get_branch_last_commit_date", return_value="2023-01-01"):
            with patch("gitmove.core.branch_manager.get_tracking_branch", return_value="origin/feature/test"):
                with patch("gitmove.core.branch_manager.is_branch_merged", return_value=False):
                    # Act
                    branch_info = self.branch_manager._get_branch_info("feature/test")
                    
                    # Assert
                    self.assertEqual(branch_info["name"], "feature/test")
                    self.assertEqual(branch_info["is_remote"], False)
                    self.assertEqual(branch_info["last_commit_date"], "2023-01-01")
                    self.assertEqual(branch_info["tracking"], "origin/feature/test")
                    self.assertEqual(branch_info["is_merged"], False)
                    self.assertEqual(branch_info["is_main"], False)
    
    def test_get_branch_info_error(self):
        """Tester la récupération des informations d'une branche avec une erreur"""
        # Arrange
        with patch("gitmove.core.branch_manager.get_branch_last_commit_date", side_effect=Exception("Test error")):
            # Act
            branch_info = self.branch_manager._get_branch_info("feature/test")
            
            # Assert
            self.assertEqual(branch_info["name"], "feature/test")
            self.assertEqual(branch_info["last_commit_date"], "Inconnue")
            self.assertEqual(branch_info["is_merged"], False)
    
    def test_find_merged_branches(self):
        """Tester la recherche des branches fusionnées"""
        # Arrange
        # Mock pour list_branches
        self.branch_manager.list_branches = MagicMock()
        self.branch_manager.list_branches.return_value = [
            {"name": "main", "is_merged": True, "is_main": True, "last_commit_date": "2023-01-01"},
            {"name": "feature/done", "is_merged": True, "is_main": False, "last_commit_date": "2023-01-01"},
            {"name": "feature/active", "is_merged": False, "is_main": False, "last_commit_date": "2023-01-01"},
            {"name": "develop", "is_merged": True, "is_main": False, "last_commit_date": "2023-01-01"}
        ]
        
        # Set up the config mock to return exclude_branches
        self.config_mock.get_value.side_effect = lambda key, default=None: {
            "clean.exclude_branches": ["develop", "staging"],
            "clean.age_threshold": 30,
            "general.main_branch": "main"
        }.get(key, default)
        
        # Act
        merged_branches = self.branch_manager.find_merged_branches()
        
        # Assert
        self.assertEqual(len(merged_branches), 1)
        self.assertEqual(merged_branches[0]["name"], "feature/done")
    
    def test_clean_merged_branches(self):
        """Tester le nettoyage des branches fusionnées"""
        # Arrange
        # Branches à nettoyer
        branches_to_clean = [
            {"name": "feature/done1", "is_remote": False, "tracking": None},
            {"name": "feature/done2", "is_remote": False, "tracking": "origin/feature/done2"}
        ]
        
        with patch("gitmove.core.branch_manager.delete_branch") as delete_branch_mock:
            # Act
            result = self.branch_manager.clean_merged_branches(branches=branches_to_clean)
            
            # Assert
            self.assertEqual(result["cleaned_count"], 2)
            self.assertEqual(len(result["cleaned_branches"]), 2)
            self.assertEqual(result["failed_count"], 0)
            
            # Vérifier que delete_branch a été appelé avec les bons paramètres
            delete_branch_mock.assert_has_calls([
                call(self.repo_mock, "feature/done1"),
                call(self.repo_mock, "feature/done2")
            ])
    
    def test_clean_merged_branches_with_remote(self):
        """Tester le nettoyage des branches fusionnées avec les branches distantes"""
        # Arrange
        # Branches à nettoyer
        branches_to_clean = [
            {"name": "feature/done1", "is_remote": False, "tracking": "origin/feature/done1"},
            {"name": "feature/done2", "is_remote": True}
        ]
        
        with patch("gitmove.core.branch_manager.delete_branch") as delete_branch_mock:
            # Act
            result = self.branch_manager.clean_merged_branches(
                branches=branches_to_clean,
                include_remote=True
            )
            
            # Assert
            self.assertEqual(result["cleaned_count"], 2)
            self.assertEqual(len(result["cleaned_branches"]), 2)
            self.assertEqual(result["failed_count"], 0)
            
            # Vérifier que delete_branch a été appelé avec les bons paramètres
            delete_branch_mock.assert_has_calls([
                call(self.repo_mock, "feature/done1"),
                call(self.repo_mock, "feature/done1", remote=True, remote_name="origin"),
                call(self.repo_mock, "feature/done2", remote=True)
            ])
    
    def test_clean_merged_branches_with_failure(self):
        """Tester le nettoyage des branches fusionnées avec un échec"""
        # Arrange
        # Branches à nettoyer
        branches_to_clean = [
            {"name": "feature/done1", "is_remote": False, "tracking": None},
            {"name": "feature/error", "is_remote": False, "tracking": None}
        ]
        
        def delete_branch_side_effect(repo, branch_name, **kwargs):
            if branch_name == "feature/error":
                raise Exception("Test error")
        
        with patch("gitmove.core.branch_manager.delete_branch") as delete_branch_mock:
            delete_branch_mock.side_effect = delete_branch_side_effect
            
            # Act
            result = self.branch_manager.clean_merged_branches(branches=branches_to_clean)
            
            # Assert
            self.assertEqual(result["cleaned_count"], 1)
            self.assertEqual(result["cleaned_branches"], ["feature/done1"])
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["failed_branches"], ["feature/error"])
    
    def test_get_branch_status(self):
        """Tester la récupération du statut d'une branche"""
        # Arrange
        # Mock des branches existantes
        branch1 = MagicMock()
        branch1.name = "main"
        branch2 = MagicMock()
        branch2.name = "feature/test"
        self.repo_mock.heads = [branch1, branch2]
        
        # Mock _get_branch_info et _get_branch_divergence
        self.branch_manager._get_branch_info = MagicMock()
        self.branch_manager._get_branch_info.return_value = {
            "name": "feature/test",
            "is_merged": False,
            "last_commit_date": "2023-01-01",
            "tracking": "origin/feature/test"
        }
        
        self.branch_manager._get_branch_divergence = MagicMock()
        self.branch_manager._get_branch_divergence.return_value = (3, 2)  # ahead, behind
        
        # Act
        status = self.branch_manager.get_branch_status("feature/test")
        
        # Assert
        self.assertEqual(status["name"], "feature/test")
        self.assertEqual(status["is_main"], False)
        self.assertEqual(status["ahead_commits"], 3)
        self.assertEqual(status["behind_commits"], 2)
        
        # Vérifier les appels aux mocks
        self.branch_manager._get_branch_info.assert_called_once_with("feature/test")
        self.branch_manager._get_branch_divergence.assert_called_once_with("feature/test", "main")
    
    def test_get_branch_status_non_existent(self):
        """Tester la récupération du statut d'une branche inexistante"""
        # Arrange
        # Mock des branches existantes
        branch1 = MagicMock()
        branch1.name = "main"
        self.repo_mock.heads = [branch1]
        
        # Act/Assert
        with self.assertRaises(ValueError):
            self.branch_manager.get_branch_status("feature/nonexistent")
    
    def test_get_branch_divergence(self):
        """Tester le calcul de la divergence entre deux branches"""
        # Arrange
        self.git_mock.merge_base.return_value = "common-ancestor-sha"
        self.git_mock.rev_list.side_effect = ["3", "2"]  # ahead, behind
        
        # Act
        ahead, behind = self.branch_manager._get_branch_divergence("feature/test", "main")
        
        # Assert
        self.assertEqual(ahead, 3)
        self.assertEqual(behind, 2)
        
        # Vérifier les appels au mock Git
        self.git_mock.merge_base.assert_called_once_with("feature/test", "main")
        self.git_mock.rev_list.assert_has_calls([
            call("--count", "common-ancestor-sha..feature/test"),
            call("--count", "common-ancestor-sha..main")
        ])
    
    def test_get_branch_divergence_same_branch(self):
        """Tester le calcul de la divergence entre la même branche"""
        # Act
        ahead, behind = self.branch_manager._get_branch_divergence("main", "main")
        
        # Assert
        self.assertEqual(ahead, 0)
        self.assertEqual(behind, 0)
        
        # Vérifier que merge_base n'a pas été appelé
        self.git_mock.merge_base.assert_not_called()

if __name__ == '__main__':
    unittest.main()