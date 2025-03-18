import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ajouter le répertoire src au path pour pouvoir importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gitmove.env_config import EnvConfigManager

class TestEnvConfigManager(unittest.TestCase):
    """
    Tests unitaires pour le gestionnaire de configuration par variables d'environnement.
    """
    
    def setUp(self):
        """Initialiser les tests"""
        # Configuration de base pour les tests
        self.base_config = {
            "general": {
                "main_branch": "main",
                "verbose": False
            },
            "clean": {
                "auto_clean": False
            }
        }
    
    def test_load_config_no_env_vars(self):
        """Tester le chargement de configuration sans variables d'environnement"""
        # Arrange
        env_vars = {}
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfigManager.load_config(self.base_config)
        
        # Assert
        self.assertIsInstance(config["clean"]["exclude_branches"], list)
        self.assertEqual(len(config["clean"]["exclude_branches"]), 3)
        self.assertEqual(config["clean"]["exclude_branches"][0], "develop")
        
        self.assertIsInstance(config["test"]["complex_json"], dict)
        self.assertEqual(config["test"]["complex_json"]["key1"], "value1")
        self.assertEqual(config["test"]["complex_json"]["key2"], 42)
        self.assertEqual(config["test"]["complex_json"]["key3"], True)
    
    def test_load_config_with_custom_prefix(self):
        """Tester le chargement de configuration avec un préfixe personnalisé"""
        # Arrange
        env_vars = {
            "CUSTOM_GENERAL_MAIN_BRANCH": "custom-branch"
        }
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfigManager.load_config(self.base_config, prefix="CUSTOM_")
        
        # Assert
        self.assertEqual(config["general"]["main_branch"], "custom-branch")
    
    def test_convert_value_integer(self):
        """Tester la conversion d'une chaîne en entier"""
        # Act
        result = EnvConfigManager._convert_value("42")
        
        # Assert
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)
    
    def test_convert_value_float(self):
        """Tester la conversion d'une chaîne en nombre à virgule flottante"""
        # Act
        result = EnvConfigManager._convert_value("3.14")
        
        # Assert
        self.assertEqual(result, 3.14)
        self.assertIsInstance(result, float)
    
    def test_convert_value_boolean(self):
        """Tester la conversion d'une chaîne en booléen"""
        # Assert
        self.assertEqual(EnvConfigManager._convert_value("true"), True)
        self.assertEqual(EnvConfigManager._convert_value("True"), True)
        self.assertEqual(EnvConfigManager._convert_value("TRUE"), True)
        self.assertEqual(EnvConfigManager._convert_value("yes"), True)
        self.assertEqual(EnvConfigManager._convert_value("1"), True)
        self.assertEqual(EnvConfigManager._convert_value("on"), True)
        
        self.assertEqual(EnvConfigManager._convert_value("false"), False)
        self.assertEqual(EnvConfigManager._convert_value("False"), False)
        self.assertEqual(EnvConfigManager._convert_value("FALSE"), False)
        self.assertEqual(EnvConfigManager._convert_value("no"), False)
        self.assertEqual(EnvConfigManager._convert_value("0"), False)
        self.assertEqual(EnvConfigManager._convert_value("off"), False)
    
    def test_convert_value_string(self):
        """Tester la conservation d'une chaîne simple"""
        # Act
        result = EnvConfigManager._convert_value("simple string")
        
        # Assert
        self.assertEqual(result, "simple string")
        self.assertIsInstance(result, str)
    
    def test_convert_value_json(self):
        """Tester la conversion d'une chaîne JSON"""
        # Act
        result = EnvConfigManager._convert_value('{"key": "value", "number": 42}')
        
        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["number"], 42)
    
    def test_convert_value_json_array(self):
        """Tester la conversion d'un tableau JSON"""
        # Act
        result = EnvConfigManager._convert_value('["item1", "item2", "item3"]')
        
        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "item1")
    
    def test_merge_config_value(self):
        """Tester la fusion d'une valeur dans la configuration"""
        # Arrange
        config = {}
        
        # Act
        config = EnvConfigManager._merge_config_value(config, "general_main_branch", "develop")
        
        # Assert
        self.assertIn("general", config)
        self.assertIn("main_branch", config["general"])
        self.assertEqual(config["general"]["main_branch"], "develop")
    
    def test_merge_config_value_nested(self):
        """Tester la fusion d'une valeur dans une configuration imbriquée existante"""
        # Arrange
        config = {
            "general": {
                "verbose": False
            }
        }
        
        # Act
        config = EnvConfigManager._merge_config_value(config, "general_main_branch", "develop")
        
        # Assert
        self.assertEqual(config["general"]["verbose"], False)
        self.assertEqual(config["general"]["main_branch"], "develop")
    
    def test_generate_env_template(self):
        """Tester la génération d'un template de variables d'environnement"""
        # Act
        template = EnvConfigManager.generate_env_template()
        
        # Assert
        self.assertIsInstance(template, str)
        self.assertIn("GITMOVE_GENERAL_MAIN_BRANCH", template)
        self.assertIn("GITMOVE_GENERAL_VERBOSE", template)
    
    def test_generate_env_template_custom_schema(self):
        """Tester la génération d'un template avec un schéma personnalisé"""
        # Arrange
        custom_schema = {
            'test': {
                'option1': {
                    'type': 'string',
                    'description': 'Test option',
                    'example': 'test-value'
                }
            }
        }
        
        # Act
        template = EnvConfigManager.generate_env_template(custom_schema)
        
        # Assert
        self.assertIsInstance(template, str)
        self.assertIn("GITMOVE_TEST_OPTION1", template)
        self.assertIn("Test option", template)
        self.assertIn("Example: test-value", template)
    
    def test_validate_env_config_valid(self):
        """Tester la validation d'une configuration valide"""
        # Arrange
        config = {
            'general': {
                'main_branch': 'develop',
                'verbose': True
            },
            'sync': {
                'default_strategy': 'rebase',
                'auto_sync': True
            }
        }
        
        # Act
        errors = EnvConfigManager.validate_env_config(config)
        
        # Assert
        self.assertEqual(errors, {})
    
    def test_validate_env_config_invalid_type(self):
        """Tester la validation avec un type invalide"""
        # Arrange
        config = {
            'general': {
                'main_branch': 42,  # Devrait être une chaîne
                'verbose': 'not-a-boolean'  # Devrait être un booléen
            }
        }
        
        # Act
        errors = EnvConfigManager.validate_env_config(config)
        
        # Assert
        self.assertIn('general', errors)
        self.assertEqual(len(errors['general']), 2)
    
    def test_validate_env_config_pattern(self):
        """Tester la validation avec une regex de pattern"""
        # Arrange
        config = {
            'general': {
                'main_branch': 'invalid@branch'  # Ne correspond pas au pattern
            }
        }
        
        # Act
        errors = EnvConfigManager.validate_env_config(config)
        
        # Assert
        self.assertIn('general', errors)
        self.assertEqual(len(errors['general']), 1)
        self.assertIn('Invalid format for general.main_branch', errors['general'][0])
    
    def test_validate_env_config_allowed_values(self):
        """Tester la validation avec des valeurs autorisées"""
        # Arrange
        config = {
            'sync': {
                'default_strategy': 'invalid-strategy'  # Pas dans les valeurs autorisées
            }
        }
        
        # Act
        errors = EnvConfigManager.validate_env_config(config)
        
        # Assert
        self.assertIn('sync', errors)
        self.assertEqual(len(errors['sync']), 1)
        self.assertIn('Invalid value for sync.default_strategy', errors['sync'][0])

# --------------------------------------------------------------------------------------------
        # Assert
        self.assertEqual(config["general"]["main_branch"], "main")
        self.assertEqual(config["general"]["verbose"], False)
        self.assertEqual(config["clean"]["auto_clean"], False)
    
    def test_load_config_with_env_vars(self):
        """Tester le chargement de configuration avec variables d'environnement"""
        # Arrange
        env_vars = {
            "GITMOVE_GENERAL_MAIN_BRANCH": "develop",
            "GITMOVE_GENERAL_VERBOSE": "true",
            "GITMOVE_CLEAN_AUTO_CLEAN": "true"
        }
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfigManager.load_config(self.base_config)
        
        # Assert
        self.assertEqual(config["general"]["main_branch"], "develop")
        self.assertEqual(config["general"]["verbose"], True)
        self.assertEqual(config["clean"]["auto_clean"], True)
    
    def test_load_config_with_new_section(self):
        """Tester le chargement de configuration avec une nouvelle section"""
        # Arrange
        env_vars = {
            "GITMOVE_NEW_SECTION_NEW_OPTION": "new-value"
        }
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfigManager.load_config(self.base_config)
        
        # Assert
        self.assertIn("new_section", config)
        self.assertEqual(config["new_section"]["new_option"], "new-value")
    
    def test_load_config_with_integer(self):
        """Tester le chargement de configuration avec une valeur entière"""
        # Arrange
        env_vars = {
            "GITMOVE_CLEAN_AGE_THRESHOLD": "45"
        }
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfigManager.load_config(self.base_config)
        
        # Assert
        self.assertEqual(config["clean"]["age_threshold"], 45)
        self.assertIsInstance(config["clean"]["age_threshold"], int)
    
    def test_load_config_with_float(self):
        """Tester le chargement de configuration avec une valeur à virgule flottante"""
        # Arrange
        env_vars = {
            "GITMOVE_TEST_FLOAT_VALUE": "3.14"
        }
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfigManager.load_config(self.base_config)
        
        # Assert
        self.assertEqual(config["test"]["float_value"], 3.14)
        self.assertIsInstance(config["test"]["float_value"], float)
    
    def test_load_config_with_boolean(self):
        """Tester le chargement de configuration avec différentes valeurs booléennes"""
        # Arrange
        env_vars = {
            "GITMOVE_TEST_BOOL1": "true",
            "GITMOVE_TEST_BOOL2": "false",
            "GITMOVE_TEST_BOOL3": "yes",
            "GITMOVE_TEST_BOOL4": "no",
            "GITMOVE_TEST_BOOL5": "1",
            "GITMOVE_TEST_BOOL6": "0"
        }
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfigManager.load_config(self.base_config)
        
        # Assert
        self.assertEqual(config["test"]["bool1"], True)
        self.assertEqual(config["test"]["bool2"], False)
        self.assertEqual(config["test"]["bool3"], True)
        self.assertEqual(config["test"]["bool4"], False)
        self.assertEqual(config["test"]["bool5"], True)
        self.assertEqual(config["test"]["bool6"], False)
    
    def test_load_config_with_json(self):
        """Tester le chargement de configuration avec une valeur JSON"""
        # Arrange
        env_vars = {
            "GITMOVE_CLEAN_EXCLUDE_BRANCHES": '["develop", "staging", "production"]',
            "GITMOVE_TEST_COMPLEX_JSON": '{"key1": "value1", "key2": 42, "key3": true}'
        }
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfigManager.load_config(self.base_config)
        
        #

if __name__ == '__main__':
    unittest.main()
