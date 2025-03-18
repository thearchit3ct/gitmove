import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call

# Ajouter le répertoire src au path pour pouvoir importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gitmove.core.sync_manager import SyncManager
from gitmove.exceptions import GitError, SyncError, MergeConflictError, DirtyWorkingTreeError

class TestSyncManager(unittest.TestCase):
    """
    Tests unitaires pour le gestionnaire de synchronisation.
    """
    
    def setUp(self):
        """Initialiser les tests"""
        # Créer des mocks pour Repo, Git et Config
        self.repo_mock = MagicMock()
        self.git_mock = MagicMock()
        self.config_mock = MagicMock()
        self.conflict_detector_mock = MagicMock()
        self.recovery_mock = MagicMock()
        
        # Configurer les valeurs de retour des mocks
        self.repo_mock.working_dir = "/fake/path"
        self.repo_mock.git = self.git_mock
        
        # Mock la méthode get_value de Config
        self.config_mock.get_value.side_effect = lambda key, default=None: {
            "general.main_branch": "main",
            "sync.default_strategy": "rebase"
        }.get(key, default)
        
        # Patch le ConflictDetector et RecoveryManager
        with patch("gitmove.core.sync_manager.ConflictDetector") as conflict_detector_class_mock:
            conflict_detector_class_mock.return_value = self.conflict_detector_mock
            with patch("gitmove.core.sync_manager.RecoveryManager") as recovery_class_mock:
                recovery_class_mock.return_value = self.recovery_mock
                
                # Créer le sync manager avec les mocks
                self.sync_manager = SyncManager(self.repo_mock, self.config_mock)
        
        # Remplacer le Git créé par le mock
        self.sync_manager.git = self.git_mock
    
    def test_check_sync_status_synced(self):
        """Tester la vérification de l'état de synchronisation quand la branche est à jour"""
        # Arrange
        with patch("gitmove.core.sync_manager.get_current_branch", return_value="feature/test"):
            with patch("gitmove.core.sync_manager.fetch_updates"):
                with patch("gitmove.core.sync_manager.get_branch_divergence", return_value=(2, 0)):  # ahead, behind
                    # Act
                    status = self.sync_manager.check_sync_status("feature/test")
                    
                    # Assert
                    self.assertTrue(status["is_synced"])
                    self.assertEqual(status["branch"], "feature/test")
                    self.assertEqual(status["target"], "main")
                    self.assertEqual(status["ahead_commits"], 2)
                    self.assertEqual(status["behind_commits"], 0)
    
    def test_check_sync_status_not_synced(self):
        """Tester la vérification de l'état de synchronisation quand la branche n'est pas à jour"""
        # Arrange
        with patch("gitmove.core.sync_manager.get_current_branch", return_value="feature/test"):
            with patch("gitmove.core.sync_manager.fetch_updates"):
                with patch("gitmove.core.sync_manager.get_branch_divergence", return_value=(2, 3)):  # ahead, behind
                    # Act
                    status = self.sync_manager.check_sync_status("feature/test")
                    
                    # Assert
                    self.assertFalse(status["is_synced"])
                    self.assertEqual(status["branch"], "feature/test")
                    self.assertEqual(status["target"], "main")
                    self.assertEqual(status["ahead_commits"], 2)
                    self.assertEqual(status["behind_commits"], 3)
                    self.assertIn("en retard de 3 commit(s)", status["message"])
    
    def test_check_sync_status_main_branch(self):
        """Tester la vérification de l'état de synchronisation sur la branche principale"""
        # Act
        status = self.sync_manager.check_sync_status("main")
        
        # Assert
        self.assertTrue(status["is_synced"])
        self.assertEqual(status["branch"], "main")
        self.assertEqual(status["target"], "main")
        self.assertEqual(status["ahead_commits"], 0)
        self.assertEqual(status["behind_commits"], 0)
    
    def test_sync_with_main_already_synced(self):
        """Tester la synchronisation quand la branche est déjà à jour"""
        # Arrange
        self.sync_manager.check_sync_status = MagicMock()
        self.sync_manager.check_sync_status.return_value = {
            "is_synced": True,
            "branch": "feature/test",
            "target": "main",
            "ahead_commits": 2,
            "behind_commits": 0,
            "message": "La branche est à jour avec la branche principale"
        }
        
        # Act
        result = self.sync_manager.sync_with_main("feature/test")
        
        # Assert
        self.assertEqual(result["status"], "up-to-date")
        self.assertEqual(result["branch"], "feature/test")
        self.assertEqual(result["target"], "main")
    
    def test_sync_with_main_dirty_working_tree(self):
        """Tester la synchronisation avec un répertoire de travail non propre"""
        # Arrange
        self.sync_manager.check_sync_status = MagicMock()
        self.sync_manager.check_sync_status.return_value = {
            "is_synced": False,
            "branch": "feature/test",
            "target": "main",
            "ahead_commits": 2,
            "behind_commits": 3
        }
        
        # Simuler un répertoire de travail non propre
        self.repo_mock.is_dirty.return_value = True
        
        # Simuler un échec de stash
        with patch("gitmove.core.sync_manager.stash_changes", return_value=None):
            # Act/Assert
            with self.assertRaises(DirtyWorkingTreeError):
                self.sync_manager.sync_with_main("feature/test")
    
    def test_sync_with_main_stashes_changes(self):
        """Tester que les modifications sont stashées avant la synchronisation"""
        # Arrange
        self.sync_manager.check_sync_status = MagicMock()
        self.sync_manager.check_sync_status.return_value = {
            "is_synced": False,
            "branch": "feature/test",
            "target": "main",
            "ahead_commits": 2,
            "behind_commits": 3
        }
        
        # Simuler un répertoire de travail non propre, puis un stash réussi
        self.repo_mock.is_dirty.return_value = True
        
        # Simuler un stash réussi
        with patch("gitmove.core.sync_manager.stash_changes", return_value="stash@{0}"):
            # Simuler une détection de conflit sans conflit
            self.conflict_detector_mock.detect_conflicts.return_value = {
                "has_conflicts": False
            }
            
            # Simuler un rebase réussi
            with patch("gitmove.core.sync_manager.rebase_branch") as rebase_mock:
                rebase_mock.return_value = {
                    "success": True,
                    "message": "Rebase successful"
                }
                
                # Act
                result = self.sync_manager.sync_with_main("feature/test", strategy="rebase")
                
                # Assert
                self.assertEqual(result["status"], "synchronized")
                # Vérifier que register_recovery_action a été appelé pour le stash
                self.recovery_mock.register_recovery_action.assert_called_once()
    
    def test_sync_with_main_potential_conflicts(self):
        """Tester la synchronisation avec des conflits potentiels"""
        # Arrange
        self.sync_manager.check_sync_status = MagicMock()
        self.sync_manager.check_sync_status.return_value = {
            "is_synced": False,
            "branch": "feature/test",
            "target": "main",
            "ahead_commits": 2,
            "behind_commits": 3
        }
        
        # Simuler un répertoire de travail propre
        self.repo_mock.is_dirty.return_value = False
        
        # Simuler une détection de conflit avec des conflits
        self.conflict_detector_mock.detect_conflicts.return_value = {
            "has_conflicts": True,
            "conflicting_files": [
                {"file_path": "file1.txt", "severity": "Élevée"},
                {"file_path": "file2.txt", "severity": "Moyenne"}
            ]
        }
        
        # Act
        result = self.sync_manager.sync_with_main("feature/test", strategy="rebase", force_sync=False)
        
        # Assert
        self.assertEqual(result["status"], "conflicts")
        self.assertEqual(result["branch"], "feature/test")
        self.assertEqual(result["target"], "main")
        self.assertEqual(result["strategy"], "rebase")
        self.assertEqual(len(result["conflicts"]["conflicting_files"]), 2)
    
    def test_sync_with_main_rebase_success(self):
        """Tester une synchronisation réussie avec rebase"""
        # Arrange
        self.sync_manager.check_sync_status = MagicMock()
        self.sync_manager.check_sync_status.return_value = {
            "is_synced": False,
            "branch": "feature/test",
            "target": "main",
            "ahead_commits": 2,
            "behind_commits": 3
        }
        
        # Simuler un répertoire de travail propre
        self.repo_mock.is_dirty.return_value = False
        
        # Simuler une détection de conflit sans conflit
        self.conflict_detector_mock.detect_conflicts.return_value = {
            "has_conflicts": False
        }
        
        # Simuler un rebase réussi
        with patch("gitmove.core.sync_manager.rebase_branch") as rebase_mock:
            rebase_mock.return_value = {
                "success": True,
                "message": "Rebase réussi",
                "branch_changed": False
            }
            
            # Act
            result = self.sync_manager.sync_with_main("feature/test", strategy="rebase")
            
            # Assert
            self.assertEqual(result["status"], "synchronized")
            self.assertEqual(result["branch"], "feature/test")
            self.assertEqual(result["target"], "main")
            self.assertEqual(result["strategy"], "rebase")
            self.assertIn("details", result)
    
    def test_sync_with_main_merge_success(self):
        """Tester une synchronisation réussie avec merge"""
        # Arrange
        self.sync_manager.check_sync_status = MagicMock()
        self.sync_manager.check_sync_status.return_value = {
            "is_synced": False,
            "branch": "feature/test",
            "target": "main",
            "ahead_commits": 2,
            "behind_commits": 3
        }
        
        # Simuler un répertoire de travail propre
        self.repo_mock.is_dirty.return_value = False
        
        # Simuler une détection de conflit sans conflit
        self.conflict_detector_mock.detect_conflicts.return_value = {
            "has_conflicts": False
        }
        
        # Simuler un merge réussi
        with patch("gitmove.core.sync_manager.merge_branch") as merge_mock:
            merge_mock.return_value = {
                "success": True,
                "message": "Merge réussi",
                "branch_changed": False
            }
            
            # Act
            result = self.sync_manager.sync_with_main("feature/test", strategy="merge")
            
            # Assert
            self.assertEqual(result["status"], "synchronized")
            self.assertEqual(result["branch"], "feature/test")
            self.assertEqual(result["target"], "main")
            self.assertEqual(result["strategy"], "merge")
            self.assertIn("details", result)
    
    def test_sync_with_main_conflict_occurs(self):
        """Tester une synchronisation avec un conflit survenant pendant le processus"""
        # Arrange
        self.sync_manager.check_sync_status = MagicMock()
        self.sync_manager.check_sync_status.return_value = {
            "is_synced": False,
            "branch": "feature/test",
            "target": "main",
            "ahead_commits": 2,
            "behind_commits": 3
        }
        
        # Simuler un répertoire de travail propre
        self.repo_mock.is_dirty.return_value = False
        
        # Simuler une détection de conflit sans conflit (pour permettre la tentative)
        self.conflict_detector_mock.detect_conflicts.return_value = {
            "has_conflicts": False
        }
        
        # Simuler un merge qui lève une erreur de conflit
        with patch("gitmove.core.sync_manager.merge_branch") as merge_mock:
            merge_mock.side_effect = MergeConflictError("Conflit de fusion")
            
            # Act
            result = self.sync_manager.sync_with_main("feature/test", strategy="merge")
            
            # Assert
            self.assertEqual(result["status"], "conflict_occurred")
            self.assertEqual(result["branch"], "feature/test")
            self.assertEqual(result["target"], "main")
            self.assertEqual(result["strategy"], "merge")
            self.assertIn("Conflit de fusion", result["error"])
            self.assertIn("suggestion", result)
    
    def test_determine_sync_strategy_rebase_threshold(self):
        """Tester la détermination de la stratégie basée sur le seuil de rebase"""
        # Arrange
        with patch("gitmove.core.sync_manager.get_branch_divergence") as divergence_mock:
            # Cas 1: Peu de commits en avance -> rebase
            divergence_mock.return_value = (3, 5)  # ahead, behind
            
            # Act
            strategy1 = self.sync_manager._determine_sync_strategy("feature/test", "main")
            
            # Assert
            self.assertEqual(strategy1, "rebase")
            
            # Cas 2: Beaucoup de commits en avance -> merge
            divergence_mock.return_value = (10, 5)  # ahead, behind (au-delà du seuil)
            
            # Act
            strategy2 = self.sync_manager._determine_sync_strategy("feature/test", "main")
            
            # Assert
            self.assertEqual(strategy2, "merge")
    
    def test_determine_sync_strategy_pattern_match(self):
        """Tester la détermination de la stratégie basée sur le pattern de branche"""
        # Arrange
        with patch("gitmove.core.sync_manager.get_branch_divergence", return_value=(3, 5)):
            # Setup mock pour les patterns de branches
            self.config_mock.get_value.side_effect = lambda key, default=None: {
                "general.main_branch": "main",
                "sync.default_strategy": "rebase",
                "advice.rebase_threshold": 5,
                "advice.force_merge_patterns": ["feature/*"],
                "advice.force_rebase_patterns": ["fix/*"]
            }.get(key, default)
            
            # Act - Branche feature (devrait être merge à cause du pattern)
            strategy1 = self.sync_manager._determine_sync_strategy("feature/test", "main")
            
            # Assert
            self.assertEqual(strategy1, "merge")
            
            # Act - Branche fix (devrait être rebase à cause du pattern)
            strategy2 = self.sync_manager._determine_sync_strategy("fix/bug", "main")
            
            # Assert
            self.assertEqual(strategy2, "rebase")
    
    def test_determine_sync_strategy_conflicts(self):
        """Tester la détermination de la stratégie basée sur les conflits potentiels"""
        # Arrange
        with patch("gitmove.core.sync_manager.get_branch_divergence", return_value=(3, 5)):
            # Setup mock pour les patterns de branches et le seuil
            self.config_mock.get_value.side_effect = lambda key, default=None: {
                "general.main_branch": "main",
                "sync.default_strategy": "rebase",
                "advice.rebase_threshold": 5,
                "advice.force_merge_patterns": [],
                "advice.force_rebase_patterns": []
            }.get(key, default)
            
            # Cas 1: Pas de conflits -> rebase
            self.conflict_detector_mock.detect_conflicts.return_value = {
                "has_conflicts": False
            }
            
            # Act
            strategy1 = self.sync_manager._determine_sync_strategy("branch/no-conflicts", "main")
            
            # Assert
            self.assertEqual(strategy1, "rebase")
            
            # Cas 2: Conflits graves -> merge
            self.conflict_detector_mock.detect_conflicts.return_value = {
                "has_conflicts": True,
                "conflicting_files": [
                    {"severity": "Élevée", "file_path": "file1.txt"}
                ]
            }
            
            # Act
            strategy2 = self.sync_manager._determine_sync_strategy("branch/conflicts", "main")
            
            # Assert
            self.assertEqual(strategy2, "merge")
    
    def test_schedule_sync(self):
        """Tester la planification de synchronisation automatique"""
        # Arrange
        # Mock auto_sync à True
        self.config_mock.get_value.side_effect = lambda key, default=None: {
            "general.main_branch": "main",
            "sync.default_strategy": "rebase",
            "sync.auto_sync": True
        }.get(key, default)
        
        # Act
        result = self.sync_manager.schedule_sync("daily")
        
        # Assert
        self.assertEqual(result["status"], "scheduled")
        self.assertEqual(result["frequency"], "daily")
        self.assertEqual(result["target"], "main")
        self.assertEqual(result["strategy"], "rebase")
    
    def test_schedule_sync_disabled(self):
        """Tester la planification de synchronisation quand elle est désactivée"""
        # Arrange
        # Mock auto_sync à False
        self.config_mock.get_value.side_effect = lambda key, default=None: {
            "general.main_branch": "main",
            "sync.default_strategy": "rebase",
            "sync.auto_sync": False
        }.get(key, default)
        
        # Act
        result = self.sync_manager.schedule_sync("daily")
        
        # Assert
        self.assertEqual(result["status"], "disabled")
        self.assertIn("désactivée", result["message"])
    
    def test_force_sync(self):
        """Tester la synchronisation forcée"""
        # Arrange
        self.sync_manager.sync_with_main = MagicMock()
        self.sync_manager.sync_with_main.return_value = {"status": "synchronized"}
        
        # Act
        self.sync_manager.force_sync("feature/test", "merge")
        
        # Assert
        self.sync_manager.sync_with_main.assert_called_once_with(
            "feature/test", "merge", force_sync=True
        )

if __name__ == '__main__':
    unittest.main()