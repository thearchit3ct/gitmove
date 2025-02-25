"""
Détecteur de conflits Git pour GitMove.

Ce module fournit des fonctionnalités pour :
- Détecter les conflits potentiels avant les fusions
- Analyser la gravité des conflits
- Suggérer des stratégies pour éviter ou minimiser les conflits
"""

import os
import tempfile
import re
from typing import Dict, List, Optional, Set, Tuple

from git import Git, Repo
from git.exc import GitCommandError

from gitmove.config import Config
from gitmove.utils.git_commands import (
    get_current_branch,
    get_common_ancestor,
    get_modified_files,
)
from gitmove.utils.logger import get_logger

logger = get_logger(__name__)

class ConflictDetector:
    """
    Détecteur de conflits Git.
    """
    
    def __init__(self, repo: Repo, config: Config):
        """
        Initialise le détecteur de conflits.
        
        Args:
            repo: Instance du dépôt Git
            config: Configuration de GitMove
        """
        self.repo = repo
        self.config = config
        self.git = Git(repo.working_dir)
        self.main_branch = config.get_value("general.main_branch", "main")
        self.show_diff = config.get_value("conflict_detection.show_diff", True)
    
    def detect_conflicts(
        self, 
        branch_name: Optional[str] = None, 
        target_branch: Optional[str] = None
    ) -> Dict:
        """
        Détecte les conflits potentiels entre deux branches.
        
        Args:
            branch_name: Nom de la branche source. Si None, utilise la branche courante.
            target_branch: Nom de la branche cible. Si None, utilise la branche principale.
            
        Returns:
            Dictionnaire contenant les résultats de la détection
        """
        if branch_name is None:
            branch_name = get_current_branch(self.repo)
        
        if target_branch is None:
            target_branch = self.main_branch
        
        # Si les branches sont identiques, pas de conflit possible
        if branch_name == target_branch:
            return {
                "has_conflicts": False,
                "conflicting_files": [],
                "suggestions": [],
            }
        
        try:
            # 1. Identifier les fichiers modifiés dans les deux branches depuis leur ancêtre commun
            ancestor = get_common_ancestor(self.repo, branch_name, target_branch)
            
            if not ancestor:
                logger.warning(f"Pas d'ancêtre commun trouvé entre {branch_name} et {target_branch}")
                return {
                    "has_conflicts": True,
                    "conflicting_files": [],
                    "error": "Pas d'ancêtre commun trouvé",
                    "suggestions": ["Effectuer un rebase de la branche sur la branche cible d'abord"],
                }
            
            source_files = get_modified_files(self.repo, ancestor, branch_name)
            target_files = get_modified_files(self.repo, ancestor, target_branch)
            
            # 2. Trouver les fichiers modifiés dans les deux branches (intersection)
            common_files = source_files.intersection(target_files)
            
            if not common_files:
                # Pas de fichiers modifiés en commun, pas de conflit probable
                return {
                    "has_conflicts": False,
                    "conflicting_files": [],
                    "suggestions": [],
                }
            
            # 3. Tenter une fusion simulée pour détecter les conflits
            conflicting_files = self._simulate_merge(branch_name, target_branch)
            
            if not conflicting_files:
                # Fusion automatique possible
                return {
                    "has_conflicts": False,
                    "common_modified_files": list(common_files),
                    "suggestions": ["Les fichiers modifiés en commun peuvent être fusionnés automatiquement"],
                }
            
            # 4. Analyse détaillée des conflits
            detailed_conflicts = self._analyze_conflicts(conflicting_files, branch_name, target_branch)
            
            # 5. Générer des suggestions
            suggestions = self._generate_suggestions(detailed_conflicts, branch_name, target_branch)
            
            return {
                "has_conflicts": True,
                "conflicting_files": detailed_conflicts,
                "common_modified_files": list(common_files),
                "conflict_count": len(detailed_conflicts),
                "suggestions": suggestions,
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des conflits: {str(e)}")
            return {
                "has_conflicts": True,  # Par sécurité, on suppose qu'il y a des conflits
                "error": str(e),
                "conflicting_files": [],
                "suggestions": ["Erreur lors de la détection des conflits, vérifier manuellement"],
            }
    
    def _simulate_merge(self, source_branch: str, target_branch: str) -> List[str]:
        """
        Simule une fusion pour détecter les conflits sans modifier le dépôt.
        
        Args:
            source_branch: Nom de la branche source
            target_branch: Nom de la branche cible
            
        Returns:
            Liste des fichiers en conflit
        """
        # Sauvegarder l'état actuel du dépôt
        original_branch = get_current_branch(self.repo)
        
        # Créer un clone temporaire du dépôt pour simuler la fusion
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Cloner le dépôt dans le répertoire temporaire
                temp_repo = Repo.clone_from(self.repo.working_dir, temp_dir)
                temp_git = Git(temp_dir)
                
                # Tenter la fusion
                temp_git.checkout(target_branch)
                try:
                    temp_git.merge(source_branch, "--no-commit", "--no-ff")
                    # Si on arrive ici, il n'y a pas de conflit
                    return []
                except GitCommandError as e:
                    # Extraire les fichiers en conflit du message d'erreur
                    conflict_output = str(e)
                    conflicting_files = []
                    
                    # Lire l'état des fichiers en conflit
                    status_output = temp_git.status()
                    for line in status_output.splitlines():
                        line = line.strip()
                        if "both modified:" in line:
                            file_path = line.split("both modified:")[-1].strip()
                            conflicting_files.append(file_path)
                    
                    return conflicting_files
            except Exception as e:
                logger.error(f"Erreur lors de la simulation de fusion: {str(e)}")
                # En cas d'erreur, on suppose qu'il y a des conflits
                return ["Erreur lors de la simulation"]
    
    def _analyze_conflicts(
        self, 
        conflicting_files: List[str], 
        source_branch: str, 
        target_branch: str
    ) -> List[Dict]:
        """
        Analyse les fichiers en conflit pour déterminer leur gravité.
        
        Args:
            conflicting_files: Liste des fichiers en conflit
            source_branch: Nom de la branche source
            target_branch: Nom de la branche cible
            
        Returns:
            Liste de dictionnaires contenant les détails des conflits
        """
        detailed_conflicts = []
        
        for file_path in conflicting_files:
            try:
                # Obtenir les différences
                diff_output = ""
                if self.show_diff:
                    diff_output = self.git.diff(f"{source_branch}:{file_path}", f"{target_branch}:{file_path}")
                
                # Déterminer le type de conflit et sa gravité
                conflict_type, severity = self._classify_conflict(file_path, diff_output)
                
                # Nombre de lignes modifiées
                modified_lines = self._count_modified_lines(diff_output)
                
                detailed_conflicts.append({
                    "file_path": file_path,
                    "conflict_type": conflict_type,
                    "severity": severity,
                    "modified_lines": modified_lines,
                    "diff": diff_output if self.show_diff else ""
                })
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse du conflit pour {file_path}: {str(e)}")
                detailed_conflicts.append({
                    "file_path": file_path,
                    "conflict_type": "Inconnu",
                    "severity": "Élevée",  # Par défaut, on considère que c'est grave
                    "error": str(e)
                })
        
        return detailed_conflicts
    
    def _classify_conflict(self, file_path: str, diff_output: str) -> Tuple[str, str]:
        """
        Classifie le type de conflit et sa gravité.
        
        Args:
            file_path: Chemin du fichier en conflit
            diff_output: Sortie de la commande diff
            
        Returns:
            Tuple (type_de_conflit, gravité)
        """
        # Déterminer le type de fichier
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Types de fichiers courants
        if file_extension in ['.py', '.js', '.java', '.c', '.cpp', '.go', '.rb']:
            file_type = "Code source"
        elif file_extension in ['.json', '.xml', '.yaml', '.yml', '.toml', '.ini']:
            file_type = "Configuration"
        elif file_extension in ['.md', '.txt', '.rst']:
            file_type = "Documentation"
        elif file_extension in ['.html', '.css', '.scss', '.less']:
            file_type = "Interface web"
        else:
            file_type = "Autre"
        
        # Analyse de la gravité basée sur le diff
        if not diff_output:
            return file_type, "Inconnue"
        
        # Compter les lignes modifiées
        additions = diff_output.count('\n+')
        deletions = diff_output.count('\n-')
        changes = additions + deletions
        
        # Heuristiques pour la gravité
        if changes <= 5:
            severity = "Faible"
        elif changes <= 20:
            severity = "Moyenne"
        else:
            severity = "Élevée"
        
        # Détection de patterns critiques
        if "import" in diff_output or "require" in diff_output:
            severity = "Élevée"  # Conflit sur les imports/requires
        
        if "function" in diff_output or "def " in diff_output or "class" in diff_output:
            severity = "Élevée"  # Modification de signature de fonction ou classe
        
        return file_type, severity
    
    def _count_modified_lines(self, diff_output: str) -> int:
        """
        Compte le nombre de lignes modifiées dans un diff.
        
        Args:
            diff_output: Sortie de la commande diff
            
        Returns:
            Nombre de lignes modifiées
        """
        if not diff_output:
            return 0
        
        additions = len(re.findall(r'\n\+', diff_output))
        deletions = len(re.findall(r'\n\-', diff_output))
        
        return additions + deletions
    
    def _generate_suggestions(
        self, 
        conflicts: List[Dict], 
        source_branch: str, 
        target_branch: str
    ) -> List[str]:
        """
        Génère des suggestions pour résoudre ou minimiser les conflits.
        
        Args:
            conflicts: Liste des conflits détaillés
            source_branch: Nom de la branche source
            target_branch: Nom de la branche cible
            
        Returns:
            Liste de suggestions
        """
        suggestions = []
        
        if not conflicts:
            return suggestions
        
        # Calculer les statistiques des conflits
        high_severity_count = sum(1 for c in conflicts if c["severity"] == "Élevée")
        medium_severity_count = sum(1 for c in conflicts if c["severity"] == "Moyenne")
        low_severity_count = sum(1 for c in conflicts if c["severity"] == "Faible")
        
        total_conflicts = len(conflicts)
        
        # Suggestions basées sur la gravité
        if high_severity_count > 0:
            if high_severity_count == total_conflicts:
                suggestions.append(
                    f"Tous les conflits sont de gravité élevée. Envisagez de travailler sur les fichiers "
                    f"un par un et de soumettre des changements incrémentiels."
                )
            else:
                suggestions.append(
                    f"{high_severity_count} conflit(s) de gravité élevée détecté(s). "
                    f"Résolvez d'abord les fichiers moins critiques."
                )
        
        # Suggestions basées sur le type de fichier
        config_files = [c for c in conflicts if c["conflict_type"] == "Configuration"]
        if config_files:
            suggestions.append(
                f"Conflit(s) dans {len(config_files)} fichier(s) de configuration. "
                f"Vérifiez les modifications spécifiques pour éviter des problèmes de compatibilité."
            )
        
        # Suggestions générales
        if total_conflicts > 5:
            suggestions.append(
                f"Nombre élevé de conflits ({total_conflicts}). Envisagez de diviser cette branche "
                f"en branches plus petites et de les fusionner séparément."
            )
        
        # Synchronisation recommandée
        suggestions.append(
            f"Synchronisez régulièrement votre branche avec '{target_branch}' pour minimiser "
            f"les conflits futurs."
        )
        
        # Stratégie recommandée
        if high_severity_count > total_conflicts / 2:
            suggestions.append(
                f"En raison de la gravité des conflits, envisagez d'utiliser 'merge' plutôt que 'rebase' "
                f"pour conserver l'historique des modifications."
            )
        else:
            suggestions.append(
                f"Pour ces conflits, la stratégie 'rebase' peut être appropriée pour maintenir "
                f"un historique plus propre."
            )
        
        return suggestions