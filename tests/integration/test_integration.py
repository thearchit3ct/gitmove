import os
import sys
import unittest
import shutil
import tempfile
import subprocess
from contextlib import contextmanager
from git import Repo, GitCommandError

# Ajouter le répertoire src au path pour pouvoir importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gitmove import get_manager
from gitmove.config import Config

class GitMoveIntegrationTests(unittest.TestCase):
    """
    Tests d'intégration pour GitMove.
    
    Ces tests créent des dépôts Git temporaires et effectuent des opérations
    réelles pour tester les fonctionnalités de GitMove de bout en bout.
    """
    
    def setUp(self):
        """
        Préparer l'environnement de test en créant un dépôt Git temporaire.
        """
        # Créer un répertoire temporaire pour le dépôt de test
        self.test_dir = tempfile.mkdtemp()
        
        # Initialiser un dépôt Git
        self.repo = Repo.init(self.test_dir)
        self.git = self.repo.git
        
        # Configurer l'identité Git pour les commits
        self.git.config('user.name', 'GitMove Test')
        self.git.config('user.email', 'test@gitmove.example.com')
        
        # Créer un premier commit (fichier README.md)
        readme_path = os.path.join(self.test_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write('# Test Repository\n\nThis is a test repository for GitMove integration tests.')
        
        self.git.add('README.md')
        self.git.commit('-m', 'Initial commit')
        
        # Créer une configuration GitMove par défaut
        self.config = Config()
        self.config.set_value('general.main_branch', 'main')
        self.config.set_value('clean.exclude_branches', ['develop'])
        self.config.set_value('sync.default_strategy', 'rebase')
        
        # Enregistrer la configuration
        config_path = os.path.join(self.test_dir, '.gitmove.toml')
        self.config.save(config_path)
        
        # S'assurer que la branche principale est nommée "main"
        current_branch = self.repo.active_branch.name
        if current_branch != 'main':
            # Renommer la branche si nécessaire (pour les versions anciennes de Git)
            self.git.branch('-m', current_branch, 'main')
    
    def tearDown(self):
        """
        Nettoyer l'environnement après les tests.
        """
        # Supprimer le répertoire temporaire
        shutil.rmtree(self.test_dir)
    
    @contextmanager
    def create_branch(self, branch_name, create_commits=1):
        """
        Créer une branche temporaire pour les tests.
        
        Args:
            branch_name: Nom de la branche à créer
            create_commits: Nombre de commits à créer sur la branche
        """
        # Sauvegarder la branche actuelle
        original_branch = self.repo.active_branch.name
        
        try:
            # Créer et basculer sur la nouvelle branche
            self.git.checkout('-b', branch_name)
            
            # Créer des commits si demandé
            for i in range(create_commits):
                file_name = f'file_{branch_name}_{i}.txt'
                file_path = os.path.join(self.test_dir, file_name)
                with open(file_path, 'w') as f:
                    f.write(f'Content for {file_name}\n')
                
                self.git.add(file_name)
                self.git.commit('-m', f'Add {file_name}')
            
            # Rendre la branche accessible au test
            yield branch_name
        
        finally:
            # Revenir à la branche d'origine
            self.git.checkout(original_branch)
    
    def test_branch_manager_integration(self):
        """
        Test d'intégration pour BranchManager.
        """
        # Obtenir un gestionnaire pour le dépôt de test
        managers = get_manager(self.test_dir)
        branch_manager = managers['branch_manager']
        
        # Vérifier que la branche principale est bien détectée
        current_branch = branch_manager.get_current_branch()
        self.assertEqual(current_branch, 'main')
        
        # Créer une branche feature
        with self.create_branch('feature/test', create_commits=2):
            # Vérifier que la branche existe
            branches = branch_manager.list_branches()
            branch_names = [b['name'] for b in branches]
            self.assertIn('feature/test', branch_names)
            
            # Vérifier le statut de la branche
            status = branch_manager.get_branch_status('feature/test')
            self.assertEqual(status['name'], 'feature/test')
            self.assertEqual(status['ahead_commits'], 2)
            
            # Revenir à main et fusionner la branche feature
            self.git.checkout('main')
            self.git.merge('feature/test', '--no-ff', '-m', 'Merge feature/test')
            
            # Vérifier que la branche est maintenant fusionnée
            merged_branches = branch_manager.find_merged_branches()
            merged_branch_names = [b['name'] for b in merged_branches]
            self.assertIn('feature/test', merged_branch_names)
            
            # Nettoyer les branches fusionnées
            result = branch_manager.clean_merged_branches()
            self.assertIn('feature/test', result['cleaned_branches'])
            
            # Vérifier que la branche a bien été supprimée
            branches_after = branch_manager.list_branches()
            branch_names_after = [b['name'] for b in branches_after]
            self.assertNotIn('feature/test', branch_names_after)
    
    def test_conflict_detector_integration(self):
        """
        Test d'intégration pour ConflictDetector.
        """
        # Obtenir un gestionnaire pour le dépôt de test
        managers = get_manager(self.test_dir)
        conflict_detector = managers['conflict_detector']
        
        # Créer une première branche qui modifie un fichier
        with self.create_branch('branch1'):
            # Créer un fichier qui sera en conflit
            conflict_file = os.path.join(self.test_dir, 'conflict.txt')
            with open(conflict_file, 'w') as f:
                f.write('Content from branch1\n')
            
            self.git.add('conflict.txt')
            self.git.commit('-m', 'Add conflict.txt from branch1')
        
        # Créer une seconde branche qui modifie le même fichier
        with self.create_branch('branch2'):
            # Modifier le même fichier avec un contenu différent
            conflict_file = os.path.join(self.test_dir, 'conflict.txt')
            with open(conflict_file, 'w') as f:
                f.write('Content from branch2\n')
            
            self.git.add('conflict.txt')
            self.git.commit('-m', 'Add conflict.txt from branch2')
            
            # Détecter les conflits entre branch2 et branch1
            conflicts = conflict_detector.detect_conflicts('branch2', 'branch1')
            
            # Vérifier qu'un conflit a été détecté
            self.assertTrue(conflicts['has_conflicts'])
            self.assertEqual(len(conflicts['conflicting_files']), 1)
            self.assertEqual(conflicts['conflicting_files'][0]['file_path'], 'conflict.txt')
    
    def test_sync_manager_integration(self):
        """
        Test d'intégration pour SyncManager.
        """
        # Obtenir un gestionnaire pour le dépôt de test
        managers = get_manager(self.test_dir)
        sync_manager = managers['sync_manager']
        
        # Créer une branche pour la synchronisation
        with self.create_branch('feature/sync', create_commits=2):
            # Basculer sur main et créer un commit
            self.git.checkout('main')
            new_file = os.path.join(self.test_dir, 'main_file.txt')
            with open(new_file, 'w') as f:
                f.write('Content from main\n')
            
            self.git.add('main_file.txt')
            self.git.commit('-m', 'Add file on main')
            
            # Basculer sur la branche feature
            self.git.checkout('feature/sync')
            
            # Vérifier que la branche n'est pas à jour
            status = sync_manager.check_sync_status('feature/sync')
            self.assertFalse(status['is_synced'])
            self.assertEqual(status['behind_commits'], 1)
            
            # Synchroniser la branche
            result = sync_manager.sync_with_main('feature/sync', strategy='rebase')
            
            # Vérifier que la synchronisation a réussi
            self.assertEqual(result['status'], 'synchronized')
            
            # Vérifier que la branche est maintenant à jour
            status_after = sync_manager.check_sync_status('feature/sync')
            self.assertTrue(status_after['is_synced'])
            self.assertEqual(status_after['behind_commits'], 0)
    
    def test_strategy_advisor_integration(self):
        """
        Test d'intégration pour StrategyAdvisor.
        """
        # Obtenir un gestionnaire pour le dépôt de test
        managers = get_manager(self.test_dir)
        advisor = managers['strategy_advisor']
        
        # Créer une branche avec peu de commits
        with self.create_branch('feature/small', create_commits=2):
            # Demander une recommandation de stratégie
            advice = advisor.get_strategy_advice('feature/small')
            
            # Vérifier que la stratégie recommandée est rebase
            self.assertEqual(advice['strategy'], 'rebase')
        
        # Créer une branche avec beaucoup de commits
        with self.create_branch('feature/large', create_commits=10):
            # Demander une recommandation de stratégie
            advice = advisor.get_strategy_advice('feature/large')
            
            # Vérifier que la stratégie recommandée est merge
            self.assertEqual(advice['strategy'], 'merge')
    
    def test_complete_workflow_integration(self):
        """
        Test d'intégration pour un workflow complet.
        """
        # Obtenir tous les gestionnaires
        managers = get_manager(self.test_dir)
        
        # Extraire les gestionnaires individuels
        branch_manager = managers['branch_manager']
        sync_manager = managers['sync_manager']
        advisor = managers['strategy_advisor']
        conflict_detector = managers['conflict_detector']
        
        # 1. Créer une branche de fonctionnalité
        with self.create_branch('feature/workflow', create_commits=3):
            # 2. Ajouter un commit sur main
            self.git.checkout('main')
            main_file = os.path.join(self.test_dir, 'main_update.txt')
            with open(main_file, 'w') as f:
                f.write('Update on main\n')
            
            self.git.add('main_update.txt')
            self.git.commit('-m', 'Update on main')
            
            # 3. Revenir à la branche de fonctionnalité
            self.git.checkout('feature/workflow')
            
            # 4. Vérifier si la branche est à jour
            status = sync_manager.check_sync_status('feature/workflow')
            self.assertFalse(status['is_synced'])
            
            # 5. Obtenir un conseil de stratégie
            advice = advisor.get_strategy_advice('feature/workflow')
            
            # 6. Vérifier les conflits potentiels
            conflicts = conflict_detector.detect_conflicts('feature/workflow')
            
            # 7. Synchroniser la branche
            result = sync_manager.sync_with_main('feature/workflow', strategy=advice['strategy'])
            self.assertEqual(result['status'], 'synchronized')
            
            # 8. Vérifier que la branche est maintenant à jour
            status_after = sync_manager.check_sync_status('feature/workflow')
            self.assertTrue(status_after['is_synced'])
            
            # 9. Revenir à main et fusionner la branche
            self.git.checkout('main')
            self.git.merge('feature/workflow', '--no-ff', '-m', 'Merge feature/workflow')
            
            # 10. Nettoyer les branches fusionnées
            merged_branches = branch_manager.find_merged_branches()
            result = branch_manager.clean_merged_branches(branches=merged_branches)
            
            # 11. Vérifier que la branche a été supprimée
            branches_after = branch_manager.list_branches()
            branch_names = [b['name'] for b in branches_after]
            self.assertNotIn('feature/workflow', branch_names)
    
    def test_command_line_interface(self):
        """
        Test d'intégration pour l'interface en ligne de commande.
        """
        # Vérifier que le CLI est disponible
        try:
            result = subprocess.run(['gitmove', '--version'], 
                                   capture_output=True, text=True, check=True)
            # S'assurer que la sortie contient une version
            self.assertIn('GitMove', result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("L'interface en ligne de commande gitmove n'est pas installée")
        
        # Test avec un dépôt réel
        os.chdir(self.test_dir)
        
        # Exécuter la commande status pour vérifier l'état
        result = subprocess.run(['gitmove', 'status'], 
                               capture_output=True, text=True, check=True)
        self.assertIn('main', result.stdout)
        
        # Créer une branche pour tester les commandes
        with self.create_branch('feature/cli-test', create_commits=2):
            # Vérifier la commande advice
            result = subprocess.run(['gitmove', 'advice', '--branch', 'feature/cli-test'],
                                   capture_output=True, text=True, check=True)
            self.assertIn('recommandée', result.stdout.lower())
            
            # Vérifier la commande check-conflicts
            result = subprocess.run(['gitmove', 'check-conflicts', '--branch', 'feature/cli-test'],
                                   capture_output=True, text=True, check=True)
            # La sortie devrait indiquer s'il y a des conflits ou non
            self.assertTrue('conflit' in result.stdout.lower() or 'aucun conflit' in result.stdout.lower())

if __name__ == '__main__':
    unittest.main()