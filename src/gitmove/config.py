"""
Gestion de la configuration pour GitMove
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import toml

from gitmove.config_validator import ConfigValidator
from gitmove.env_config import EnvConfigLoader

# Configuration par défaut
DEFAULT_CONFIG = {
    "general": {
        "main_branch": "main",
        "verbose": False,
    },
    "clean": {
        "auto_clean": False,
        "exclude_branches": ["develop", "staging"],
        "age_threshold": 30,  # jours
    },
    "sync": {
        "default_strategy": "rebase",
        "auto_sync": True,
        "sync_frequency": "daily",
    },
    "advice": {
        "rebase_threshold": 5,  # nombre de commits
        "consider_branch_age": True,
        "force_merge_patterns": ["feature/*", "release/*"],
        "force_rebase_patterns": ["fix/*", "chore/*"],
    },
    "conflict_detection": {
        "pre_check_enabled": True,
        "show_diff": True,
    },
}

class Config:
    """
    Gestionnaire de configuration pour GitMove.
    
    Gère la lecture et l'écriture des configurations à différents niveaux :
    - Global (~/.config/gitmove/config.toml)
    - Projet (.gitmove.toml à la racine du dépôt)
    - Spécifique (chemin personnalisé)
    """
    
    def __init__(self):
        """Initialise une nouvelle configuration avec les valeurs par défaut."""
        self.config = DEFAULT_CONFIG.copy()
        self.config_path = None
        self.validator = ConfigValidator()
    
    @classmethod
    def load(cls, repo_path: Optional[str] = None) -> 'Config':
        """
        Charge la configuration en fusionnant les différents niveaux.
        
        Args:
            repo_path: Chemin vers le dépôt Git. Si None, utilise le répertoire courant.
            
        Returns:
            Une instance de Config avec les configurations fusionnées.
        """
        config = cls()
        
        # 1. Charger la configuration globale
        global_config = cls._get_global_config_path()
        if global_config.exists():
            config.load_from_file(global_config)
        
        # 2. Charger la configuration du projet
        if repo_path:
            repo_config = cls._get_repo_config_path(repo_path)
            if repo_config.exists():
                config.load_from_file(repo_config)
                config.config_path = str(repo_config)
        
        # 3. Fusionner avec les variables d'environnement
        env_config = EnvConfigLoader.load_from_env(config.config)
        config.config.update(env_config)
        
        # 4. Valider la configuration finale
        try:
            config.config = config.validator.validate_config(config.config)
        except ValueError as e:
            print(f"Erreur de configuration : {e}")
        
        return config
    
    def load_from_file(self, path: Union[str, Path]):
        """
        Charge la configuration depuis un fichier et la fusionne avec l'existante.
        
        Args:
            path: Chemin vers le fichier de configuration.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Le fichier de configuration {path} n'existe pas.")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_config = toml.load(f)
            
            # Fusionner la configuration du fichier avec l'existante
            self._merge_config(file_config)
            self.config_path = str(path)
        except Exception as e:
            raise Exception(f"Erreur lors de la lecture du fichier de configuration: {str(e)}")
    
    def save(self, path: Optional[Union[str, Path]] = None):
        """
        Enregistre la configuration dans un fichier.
        
        Args:
            path: Chemin où enregistrer la configuration. Si None, utilise le chemin actuel.
        """
        if path is None:
            if self.config_path is None:
                raise ValueError("Aucun chemin de configuration spécifié.")
            path = self.config_path
        
        path = Path(path)
        
        try:
            # Créer le répertoire parent s'il n'existe pas
            os.makedirs(path.parent, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                toml.dump(self.config, f)
        except Exception as e:
            raise Exception(f"Erreur lors de l'enregistrement de la configuration: {str(e)}")
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration par son chemin.
        
        Args:
            key_path: Chemin de la clé (ex: 'general.main_branch')
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            La valeur de configuration ou la valeur par défaut
        """
        parts = key_path.split(".")
        value = self.config
        
        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_value(self, key_path: str, value: Any):
        """
        Définit une valeur de configuration.
        
        Args:
            key_path: Chemin de la clé (ex: 'general.main_branch')
            value: Valeur à définir
        """
        parts = key_path.split(".")
        config = self.config
        
        # Naviguer jusqu'au dernier niveau
        for i, part in enumerate(parts[:-1]):
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # Définir la valeur
        config[parts[-1]] = value
    
    def get_all(self) -> Dict:
        """
        Récupère toute la configuration.
        
        Returns:
            Dictionnaire complet de la configuration
        """
        return self.config.copy()
    
    def _merge_config(self, new_config: Dict):
        """
        Fusionne une nouvelle configuration avec l'existante de façon récursive.
        
        Args:
            new_config: Nouvelle configuration à fusionner
        """
        for key, value in new_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                self._merge_config_section(self.config[key], value)
            else:
                self.config[key] = value
    
    def _merge_config_section(self, target: Dict, source: Dict):
        """
        Fusionne une section de configuration de façon récursive.
        
        Args:
            target: Section cible
            source: Section source
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config_section(target[key], value)
            else:
                target[key] = value
    
    @staticmethod
    def _get_global_config_path() -> Path:
        """
        Retrouve le chemin de la configuration globale.
        
        Returns:
            Chemin vers le fichier de configuration globale
        """
        if sys.platform == "win32":
            base_path = os.environ.get("APPDATA", os.path.expanduser("~"))
            return Path(base_path) / "gitmove" / "config.toml"
        else:
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            return Path(xdg_config_home) / "gitmove" / "config.toml"
    
    @staticmethod
    def _get_repo_config_path(repo_path: str) -> Path:
        """
        Retrouve le chemin de la configuration du projet.
        
        Args:
            repo_path: Chemin du dépôt
            
        Returns:
            Chemin vers le fichier de configuration du projet
        """
        return Path(repo_path) / ".gitmove.toml"
    
    def validate(self) -> List[str]:
        """
        Valide la configuration actuelle.
        
        Returns:
            Liste des problèmes trouvés. Liste vide si tout est valide.
        """
        # issues = []
        
        # # Vérifier les valeurs obligatoires
        # if not self.get_value("general.main_branch"):
        #     issues.append("La branche principale n'est pas définie (general.main_branch)")
        
        # # Vérifier les types
        # if not isinstance(self.get_value("clean.age_threshold"), int):
        #     issues.append("Le seuil d'âge doit être un nombre entier (clean.age_threshold)")
        
        # if not isinstance(self.get_value("advice.rebase_threshold"), int):
        #     issues.append("Le seuil de rebase doit être un nombre entier (advice.rebase_threshold)")
        
        # # Vérifier les valeurs acceptables
        # if self.get_value("sync.default_strategy") not in ["merge", "rebase", "auto"]:
        #     issues.append(
        #         "La stratégie de synchronisation par défaut doit être 'merge', 'rebase' ou 'auto' "
        #         "(sync.default_strategy)"
        #     )
        
        # return issues
        try:
            self.validator.validate_config(self.config)
            return []
        except ValueError as e:
            return [str(e)]
        
    def get_recommendations(self) -> Dict:
        """
        Obtient des recommandations pour la configuration.
        
        Returns:
            Dictionnaire de recommandations
        """
        return self.validator.recommend_configuration(self.config)
    
    # Les autres méthodes de la classe restent similaires à l'implémentation précédente
    
    def generate_sample_config(self, output_path: Optional[str] = None) -> str:
        """
        Génère un exemple de configuration.
        
        Args:
            output_path: Chemin de sortie pour le fichier de configuration
        
        Returns:
            Contenu de la configuration d'exemple
        """
        return self.validator.generate_sample_config(output_path)