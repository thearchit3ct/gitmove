"""
Conseiller de stratégie Git pour GitMove.

Ce module fournit des fonctionnalités pour :
- Analyser une branche et recommander une stratégie (merge ou rebase)
- Évaluer l'historique des branches et leur divergence
- Suggérer la meilleure approche selon le contexte
"""

import datetime
import os
from typing import Dict, List, Optional, Tuple, Union

from git import Git, Repo
from git.exc import GitCommandError

from gitmove.config import Config
from gitmove.utils.git_commands import (
    get_current_branch,
    get_branch_divergence,
    get_branch_age,
    get_branch_commit_count,
    get_common_ancestor,
    get_modified_files,
)
from gitmove.utils.logger import get_logger
from gitmove.core.conflict_detector import ConflictDetector

logger = get_logger(__name__)

class StrategyAdvisor:
    """
    Conseiller de stratégie Git.
    """
    
    def __init__(self, repo: Repo, config: Config):
        """
        Initialise le conseiller de stratégie.
        
        Args:
            repo: Instance du dépôt Git
            config: Configuration de GitMove
        """
        self.repo = repo
        self.config = config
        self.git = Git(repo.working_dir)
        self.main_branch = config.get_value("general.main_branch", "main")
        self.conflict_detector = ConflictDetector(repo, config)
        self.rebase_threshold = config.get_value("advice.rebase_threshold", 5)
        self.consider_branch_age = config.get_value("advice.consider_branch_age", True)
    
    def get_strategy_advice(
        self, 
        branch_name: Optional[str] = None, 
        target_branch: Optional[str] = None
    ) -> Dict:
        """
        Analyse une branche et recommande une stratégie (merge ou rebase).
        
        Args:
            branch_name: Nom de la branche à analyser. Si None, utilise la branche courante.
            target_branch: Nom de la branche cible. Si None, utilise la branche principale.
            
        Returns:
            Dictionnaire contenant la recommandation et ses raisons
        """
        if branch_name is None:
            branch_name = get_current_branch(self.repo)
        
        if target_branch is None:
            target_branch = self.main_branch
        
        # Si la branche est la branche cible, pas besoin de fusion
        if branch_name == target_branch:
            return {
                "strategy": "none",
                "reason": f"La branche '{branch_name}' est identique à la branche cible",
                "details": {
                    "branch": branch_name,
                    "target": target_branch,
                }
            }
        
        try:
            # Collecter les données pour l'analyse
            analysis_data = self._analyze_branch(branch_name, target_branch)
            
            # Prendre en compte les règles de force pour certaines branches
            force_strategy = self._check_forced_strategy(branch_name)
            if force_strategy:
                return {
                    "strategy": force_strategy,
                    "reason": f"Stratégie forcée pour les branches correspondant au motif",
                    "details": analysis_data
                }
            
            # Déterminer la stratégie recommandée
            strategy, reason = self._determine_strategy(analysis_data)
            
            return {
                "strategy": strategy,
                "reason": reason,
                "details": analysis_data
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la stratégie: {str(e)}")
            return {
                "strategy": "merge",  # Par défaut, merge est plus sûr
                "reason": f"Erreur lors de l'analyse: {str(e)}",
                "error": str(e)
            }
    
    def _analyze_branch(self, branch_name: str, target_branch: str) -> Dict:
        """
        Analyse une branche et collecte des données pour la recommandation.
        
        Args:
            branch_name: Nom de la branche à analyser
            target_branch: Nom de la branche cible
            
        Returns:
            Dictionnaire contenant les données d'analyse
        """
        analysis = {}
        
        # 1. Divergence avec la branche cible
        ahead, behind = get_branch_divergence(self.repo, branch_name, target_branch)
        analysis["ahead_commits"] = ahead
        analysis["behind_commits"] = behind
        
        # 2. Âge de la branche
        branch_age = get_branch_age(self.repo, branch_name)
        analysis["branch_age_days"] = branch_age
        
        # 3. Nombre total de commits dans la branche
        commit_count = get_branch_commit_count(self.repo, branch_name)
        analysis["commit_count"] = commit_count
        
        # 4. Types de fichiers modifiés
        try:
            ancestor = get_common_ancestor(self.repo, branch_name, target_branch)
            if ancestor:
                modified_files = get_modified_files(self.repo, ancestor, branch_name)
                
                # Classer les fichiers par type
                file_types = self._classify_files(modified_files)
                analysis["file_types"] = file_types
                
                # Calculer des statistiques sur les types de fichiers
                analysis["file_stats"] = {
                    "total": len(modified_files),
                    "code": sum(1 for f in modified_files if self._get_file_type(f) == "code"),
                    "config": sum(1 for f in modified_files if self._get_file_type(f) == "config"),
                    "doc": sum(1 for f in modified_files if self._get_file_type(f) == "doc"),
                    "other": sum(1 for f in modified_files if self._get_file_type(f) not in ["code", "config", "doc"])
                }
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse des fichiers modifiés: {str(e)}")
            analysis["file_types"] = {}
            analysis["file_stats"] = {"error": str(e)}
        
        # 5. Conflits potentiels
        try:
            conflicts = self.conflict_detector.detect_conflicts(branch_name, target_branch)
            analysis["has_conflicts"] = conflicts["has_conflicts"]
            if conflicts["has_conflicts"]:
                analysis["conflict_count"] = len(conflicts.get("conflicting_files", []))
                
                # Gravité des conflits
                high_severity = sum(1 for c in conflicts.get("conflicting_files", []) 
                                  if c.get("severity") == "Élevée")
                medium_severity = sum(1 for c in conflicts.get("conflicting_files", []) 
                                    if c.get("severity") == "Moyenne")
                low_severity = sum(1 for c in conflicts.get("conflicting_files", []) 
                                 if c.get("severity") == "Faible")
                
                analysis["conflict_severity"] = {
                    "high": high_severity,
                    "medium": medium_severity,
                    "low": low_severity
                }
            else:
                analysis["conflict_count"] = 0
                analysis["conflict_severity"] = {"high": 0, "medium": 0, "low": 0}
        except Exception as e:
            logger.warning(f"Erreur lors de la détection des conflits: {str(e)}")
            analysis["has_conflicts"] = False
            analysis["conflict_count"] = 0
            analysis["conflict_severity"] = {"error": str(e)}
        
        # 6. Historique de nommage (pattern de la branche)
        analysis["branch_pattern"] = self._get_branch_pattern(branch_name)
        
        return analysis
    
    def _determine_strategy(self, analysis: Dict) -> Tuple[str, str]:
        """
        Détermine la stratégie recommandée en fonction des données d'analyse.
        
        Args:
            analysis: Données d'analyse de la branche
            
        Returns:
            Tuple (stratégie, raison)
        """
        # Facteurs favorisant le rebase
        rebase_factors = []
        merge_factors = []
        
        # 1. Nombre de commits
        if analysis["ahead_commits"] <= self.rebase_threshold:
            rebase_factors.append(f"Peu de commits ({analysis['ahead_commits']} <= {self.rebase_threshold})")
        else:
            merge_factors.append(f"Nombreux commits ({analysis['ahead_commits']} > {self.rebase_threshold})")
        
        # 2. Âge de la branche
        if self.consider_branch_age:
            if analysis["branch_age_days"] <= 7:  # Une semaine
                rebase_factors.append(f"Branche récente ({analysis['branch_age_days']} jours)")
            elif analysis["branch_age_days"] >= 30:  # Un mois
                merge_factors.append(f"Branche ancienne ({analysis['branch_age_days']} jours)")
        
        # 3. Conflits
        if analysis["has_conflicts"]:
            if analysis["conflict_severity"]["high"] > 0:
                merge_factors.append(f"{analysis['conflict_severity']['high']} conflit(s) de gravité élevée")
            elif analysis["conflict_count"] > 3:
                merge_factors.append(f"Nombreux conflits ({analysis['conflict_count']} fichiers)")
            else:
                rebase_factors.append(f"Peu de conflits ({analysis['conflict_count']} fichiers)")
        else:
            rebase_factors.append("Pas de conflits détectés")
        
        # 4. Types de fichiers
        if analysis.get("file_stats"):
            if analysis["file_stats"].get("config", 0) > 0:
                # Les fichiers de configuration ont tendance à avoir plus de conflits
                merge_factors.append(f"{analysis['file_stats']['config']} fichier(s) de configuration modifié(s)")
            
            if analysis["file_stats"].get("code", 0) > 10:
                # Beaucoup de fichiers de code modifiés
                merge_factors.append(f"Nombreux fichiers de code modifiés ({analysis['file_stats']['code']})")
        
        # 5. Pattern de branche
        if analysis["branch_pattern"] == "feature":
            merge_factors.append("Branche de fonctionnalité (feature/*)")
        elif analysis["branch_pattern"] == "bugfix":
            rebase_factors.append("Branche de correction de bug (fix/*)")
        
        # Décision finale
        if len(rebase_factors) > len(merge_factors):
            reason = "Rebase recommandé: " + ", ".join(rebase_factors[:2])
            if merge_factors:
                reason += " (malgré " + ", ".join(merge_factors[:1]) + ")"
            return "rebase", reason
        elif len(merge_factors) > len(rebase_factors):
            reason = "Merge recommandé: " + ", ".join(merge_factors[:2])
            if rebase_factors:
                reason += " (malgré " + ", ".join(rebase_factors[:1]) + ")"
            return "merge", reason
        else:
            # En cas d'égalité, favoriser le merge qui est plus sûr
            reason = "Merge recommandé par défaut (facteurs équilibrés)"
            return "merge", reason
    
    def _check_forced_strategy(self, branch_name: str) -> Optional[str]:
        """
        Vérifie si une stratégie est forcée pour ce type de branche.
        
        Args:
            branch_name: Nom de la branche
            
        Returns:
            Stratégie forcée ou None
        """
        import fnmatch
        
        force_merge_patterns = self.config.get_value("advice.force_merge_patterns", [])
        force_rebase_patterns = self.config.get_value("advice.force_rebase_patterns", [])
        
        for pattern in force_merge_patterns:
            if fnmatch.fnmatch(branch_name, pattern):
                return "merge"
        
        for pattern in force_rebase_patterns:
            if fnmatch.fnmatch(branch_name, pattern):
                return "rebase"
        
        return None
    
    def _classify_files(self, files: set) -> Dict[str, int]:
        """
        Classifie les fichiers par type.
        
        Args:
            files: Ensemble de chemins de fichiers
            
        Returns:
            Dictionnaire comptant les fichiers par type
        """
        file_types = {
            "code": 0,
            "config": 0,
            "doc": 0,
            "test": 0,
            "other": 0
        }
        
        for file_path in files:
            file_type = self._get_file_type(file_path)
            
            if file_type == "code":
                file_types["code"] += 1
            elif file_type == "config":
                file_types["config"] += 1
            elif file_type == "doc":
                file_types["doc"] += 1
            elif file_type == "test":
                file_types["test"] += 1
            else:
                file_types["other"] += 1
        
        return file_types
    
    def _get_file_type(self, file_path: str) -> str:
        """
        Détermine le type d'un fichier.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Type du fichier
        """
        file_name = os.path.basename(file_path).lower()
        extension = os.path.splitext(file_name)[1].lower()
        
        # Détection des fichiers de test
        if "test" in file_name or "spec" in file_name:
            return "test"
        
        # Classification par extension
        if extension in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rb', '.php']:
            return "code"
        elif extension in ['.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf']:
            return "config"
        elif extension in ['.md', '.txt', '.rst', '.adoc', '.pdf', '.doc', '.docx']:
            return "doc"
        elif extension in ['.html', '.css', '.scss', '.less', '.sass']:
            return "code"  # Front-end code
        elif extension in ['.sql', '.graphql']:
            return "code"  # Database code
        else:
            return "other"
    
    def _get_branch_pattern(self, branch_name: str) -> str:
        """
        Détermine le pattern de nommage d'une branche.
        
        Args:
            branch_name: Nom de la branche
            
        Returns:
            Pattern identifié
        """
        # Motifs courants de nommage de branches
        if branch_name.startswith("feature/") or branch_name.startswith("feat/"):
            return "feature"
        elif branch_name.startswith("fix/") or branch_name.startswith("bugfix/") or branch_name.startswith("hotfix/"):
            return "bugfix"
        elif branch_name.startswith("release/"):
            return "release"
        elif branch_name.startswith("chore/"):
            return "chore"
        elif branch_name.startswith("doc/") or branch_name.startswith("docs/"):
            return "doc"
        elif branch_name.startswith("test/"):
            return "test"
        else:
            return "unknown"