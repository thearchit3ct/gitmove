import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import toml

# Ajouter le répertoire src au path pour pouvoir importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gitmove.validators.config_validator import ConfigValidator

class TestConfigValidator(unittest.TestCase):
    """
    Tests unitaires pour le validateur de configuration.
    """
    
    def setUp(self):
        """Initialiser les tests"""
        # Créer un validateur de configuration sans console pour les tests
        self.validator = ConfigValidator()
        self.validator.console = MagicMock()
        
        # Configuration de test valide
        self.valid_config = {
            "general": {
                "main_branch": "main",
                "verbose": False
            },
            "clean": {
                "auto_clean": False,
                "exclude_branches": ["develop", "staging"],
                "age_threshold": 30
            },
            "sync": {
                "default_strategy": "rebase",
                "auto_sync": True
            }
        }
    
    def test_validate_valid_config(self):
        """Tester la validation d'une configuration valide"""
        # Arrange
        config = self.valid_config.copy()
        
        # Act
        normalized_config = self.validator.validate_config(config)
        
        # Assert
        self.assertIn("general", normalized_config)
        self.assertEqual(normalized_config["general"]["main_branch"], "main")
        self.assertIn("clean", normalized_config)
        self.assertEqual(normalized_config["clean"]["age_threshold"], 30)
    
    def test_validate_missing_required(self):
        """Tester la validation avec un champ requis manquant"""
        # Arrange
        config = self.valid_config.copy()
        del config["general"]["main_branch"]
        
        # Act/Assert
        with self.assertRaises(ValueError) as context:
            self.validator.validate_config(config)
        
        self.assertIn("Invalid configuration detected", str(context.exception))
        # Vérifier que la console a été appelée pour afficher l'erreur
        self.validator.console.print.assert_called()
    
    def test_validate_invalid_type(self):
        """Tester la validation avec un type incorrect"""
        # Arrange
        config = self.valid_config.copy()
        config["clean"]["age_threshold"] = "not-an-integer"
        
        # Act/Assert
        with self.assertRaises(ValueError) as context:
            self.validator.validate_config(config)
        
        self.assertIn("Invalid configuration detected", str(context.exception))
    
    def test_validate_out_of_range(self):
        """Tester la validation avec une valeur hors limites"""
        # Arrange
        config = self.valid_config.copy()
        config["clean"]["age_threshold"] = 400  # Plus grand que la limite max de 365
        
        # Act/Assert
        with self.assertRaises(ValueError) as context:
            self.validator.validate_config(config)
        
        self.assertIn("Invalid configuration detected", str(context.exception))
    
    def test_validate_invalid_enum(self):
        """Tester la validation avec une valeur d'énumération non autorisée"""
        # Arrange
        config = self.valid_config.copy()
        config["sync"]["default_strategy"] = "invalid-strategy"
        
        # Act/Assert
        with self.assertRaises(ValueError) as context:
            self.validator.validate_config(config)
        
        self.assertIn("Invalid configuration detected", str(context.exception))
    
    def test_interpolate_env_vars(self):
        """Tester l'interpolation des variables d'environnement"""
        # Arrange
        config = {
            "general": {
                "main_branch": "${MAIN_BRANCH}"
            }
        }
        
        # Mock la variable d'environnement
        with patch.dict(os.environ, {"MAIN_BRANCH": "develop"}):
            # Act
            interpolated = self.validator.interpolate_env_vars(config)
            
            # Assert
            self.assertEqual(interpolated["general"]["main_branch"], "develop")
    
    def test_generate_sample_config(self):
        """Tester la génération d'un exemple de configuration"""
        # Act
        sample_config = self.validator.generate_sample_config()
        
        # Assert
        self.assertIsInstance(sample_config, str)
        self.assertIn("[general]", sample_config)
        self.assertIn("main_branch", sample_config)
    
    def test_generate_sample_config_with_output(self):
        """Tester la génération d'un exemple de configuration dans un fichier"""
        # Arrange
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Act
            self.validator.generate_sample_config(tmp_path)
            
            # Assert
            self.assertTrue(os.path.exists(tmp_path))
            with open(tmp_path, 'r') as f:
                content = f.read()
            self.assertIn("[general]", content)
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_recommend_configuration(self):
        """Tester les recommandations de configuration"""
        # Arrange
        config = self.valid_config.copy()
        config["general"]["verbose"] = True
        config["clean"]["age_threshold"] = 120
        
        # Act
        recommendations = self.validator.recommend_configuration(config)
        
        # Assert
        self.assertIsInstance(recommendations, dict)
        self.assertIn("verbose_mode", recommendations)
        self.assertIn("branch_cleanup", recommendations)
    
    def test_load_config(self):
        """Tester le chargement d'une configuration depuis un fichier"""
        # Arrange
        mock_config_content = toml.dumps(self.valid_config)
        
        # Mock l'ouverture du fichier
        with patch("builtins.open", mock_open(read_data=mock_config_content)):
            # Act
            config = self.validator._load_config()
            
            # Assert
            self.assertEqual(config["general"]["main_branch"], "main")
    
    def test_load_config_file_not_found(self):
        """Tester le chargement d'une configuration avec un fichier manquant"""
        # Arrange
        with patch("builtins.open", side_effect=FileNotFoundError()):
            # Act
            config = self.validator._load_config()
            
            # Assert
            self.assertEqual(config, {})
    
    def test_load_config_invalid_toml(self):
        """Tester le chargement d'une configuration avec un TOML invalide"""
        # Arrange
        invalid_toml = "general = { main_branch = unclosed string }"
        
        # Mock l'ouverture du fichier
        with patch("builtins.open", mock_open(read_data=invalid_toml)):
            # Act/Assert
            with self.assertRaises(ValueError) as context:
                self.validator._load_config()
            
            self.assertIn("Invalid TOML configuration", str(context.exception))

if __name__ == '__main__':
    unittest.main()