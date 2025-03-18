"""
Gestionnaire d'erreurs pour l'interface utilisateur de GitMove.

Ce module améliore la présentation des erreurs à l'utilisateur
avec des messages informatifs et des suggestions de résolution.
"""

import sys
import traceback
from typing import Dict, List, Optional, Any, Union, Type

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.prompt import Confirm
from rich.progress import Progress
from rich.tree import Tree

from gitmove.exceptions import (
    GitMoveError, GitError, ConfigError, OperationError,
    BranchError, SyncError, MergeConflictError, DirtyWorkingTreeError,
    ProtectedBranchError, PluginError, RecoveryError
)
from gitmove.utils.logger import get_logger

logger = get_logger(__name__)

class ErrorHandler:
    """
    Gestionnaire d'erreurs pour GitMove.
    
    Fournit des méthodes pour afficher et gérer les erreurs de manière
    conviviale pour l'utilisateur.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialise le gestionnaire d'erreurs.
        
        Args:
            console: Console Rich à utiliser. Si None, en crée une nouvelle.
        """
        self.console = console or Console()
        
        # Base de connaissances pour différents types d'erreurs
        self.error_info = {
            GitError: {
                "title": "Erreur Git",
                "color": "red",
                "icon": "❌",
                "default_suggestions": [
                    "Vérifiez que Git est correctement installé et configuré",
                    "Exécutez `git status` pour vérifier l'état du dépôt",
                    "Essayez de rafraîchir le dépôt avec `git fetch --all`"
                ]
            },
            ConfigError: {
                "title": "Erreur de configuration",
                "color": "yellow",
                "icon": "⚠️",
                "default_suggestions": [
                    "Vérifiez votre fichier de configuration (.gitmove.toml)",
                    "Exécutez `gitmove config validate` pour diagnostiquer les problèmes",
                    "Générez un nouveau fichier de configuration avec `gitmove config generate`"
                ]
            },
            BranchError: {
                "title": "Erreur de branche",
                "color": "red",
                "icon": "🔄",
                "default_suggestions": [
                    "Vérifiez que la branche existe avec `git branch -a`",
                    "Assurez-vous d'être sur la bonne branche",
                    "Synchronisez les références distantes avec `git fetch --all`"
                ]
            },
            SyncError: {
                "title": "Erreur de synchronisation",
                "color": "red",
                "icon": "🔄",
                "default_suggestions": [
                    "Assurez-vous que votre connexion internet fonctionne",
                    "Vérifiez que vous avez les permissions nécessaires sur le dépôt distant",
                    "Essayez de synchroniser manuellement avec `git fetch --all`"
                ]
            },
            MergeConflictError: {
                "title": "Conflit de fusion",
                "color": "yellow",
                "icon": "⚠️",
                "default_suggestions": [
                    "Résolvez les conflits en éditant les fichiers concernés",
                    "Utilisez `git status` pour voir les fichiers en conflit",
                    "Après résolution, utilisez `git add` puis `git commit`",
                    "Pour annuler, utilisez `git merge --abort`"
                ]
            },
            DirtyWorkingTreeError: {
                "title": "Répertoire de travail non propre",
                "color": "yellow",
                "icon": "📝",
                "default_suggestions": [
                    "Committez vos modifications avec `git commit -m \"message\"`",
                    "Sauvegardez vos modifications avec `git stash`",
                    "Annulez vos modifications avec `git reset --hard`"
                ]
            },
            ProtectedBranchError: {
                "title": "Branche protégée",
                "color": "red",
                "icon": "🔒",
                "default_suggestions": [
                    "Créez une branche dédiée pour vos modifications",
                    "Utilisez le processus de pull request/merge request de votre plateforme",
                    "Consultez les règles de protection des branches de votre projet"
                ]
            },
            PluginError: {
                "title": "Erreur de plugin",
                "color": "magenta",
                "icon": "🧩",
                "default_suggestions": [
                    "Vérifiez que le plugin est correctement installé",
                    "Assurez-vous que le plugin est compatible avec votre version de GitMove",
                    "Désactivez temporairement les plugins avec `GITMOVE_PLUGINS_ENABLED=false`"
                ]
            },
            RecoveryError: {
                "title": "Erreur de récupération",
                "color": "red",
                "icon": "🔄",
                "default_suggestions": [
                    "Vérifiez l'état de votre dépôt avec `git status`",
                    "Essayez de récupérer manuellement avec `git stash apply` si vous aviez des modifications",
                    "Contactez l'équipe GitMove si le problème persiste"
                ]
            }
        }
        
        # Erreur par défaut
        self.default_error_info = {
            "title": "Erreur",
            "color": "red",
            "icon": "❗",
            "default_suggestions": [
                "Essayez de relancer la commande avec l'option --verbose pour plus de détails",
                "Consultez les journaux dans ~/.gitmove/logs pour plus d'informations",
                "Vérifiez votre configuration et l'état de votre dépôt"
            ]
        }
    
    def handle_error(
        self, 
        error: Exception, 
        verbose: bool = False, 
        exit_on_error: bool = False,
        allow_recovery: bool = True
    ) -> None:
        """
        Gère une exception en affichant un message d'erreur convivial.
        
        Args:
            error: Exception à gérer
            verbose: Si True, affiche des informations détaillées
            exit_on_error: Si True, quitte le programme après l'affichage
            allow_recovery: Si True, propose des options de récupération
        """
        # Logger l'erreur
        logger.error(f"Erreur: {str(error)}")
        if verbose:
            logger.debug(traceback.format_exc())
        
        # Obtenir les informations sur le type d'erreur
        error_type = type(error)
        error_info = self._get_error_info(error_type)
        
        # Construire le message d'erreur
        title = f"{error_info['icon']} {error_info['title']}"
        message = str(error)
        
        # Créer un panel avec le message d'erreur
        panel = Panel(
            Text(message, style=f"bold {error_info['color']}"),
            title=title,
            border_style=error_info['color']
        )
        
        # Afficher le panel
        self.console.print("\n")
        self.console.print(panel)
        
        # Afficher la cause originale si disponible et en mode verbeux
        if verbose and hasattr(error, 'original_error') and error.original_error:
            self.console.print(f"[dim]Causé par: {type(error.original_error).__name__}: {str(error.original_error)}[/]")
        
        # Afficher des suggestions
        self._show_suggestions(error, error_info)
        
        # Afficher la trace en mode verbeux
        if verbose:
            self._show_traceback(error)
        
        # Proposer des options de récupération si applicable
        if allow_recovery and isinstance(error, (GitError, OperationError)):
            self._offer_recovery_options(error)
        
        # Quitter si demandé
        if exit_on_error:
            sys.exit(1)
    
    def _get_error_info(self, error_type: Type[Exception]) -> Dict:
        """
        Obtient les informations sur un type d'erreur.
        
        Args:
            error_type: Type d'erreur
            
        Returns:
            Informations sur l'erreur
        """
        # Chercher une correspondance exacte
        if error_type in self.error_info:
            return self.error_info[error_type]
        
        # Chercher une classe parente
        for err_class, info in self.error_info.items():
            if issubclass(error_type, err_class):
                return info
        
        # Retourner les informations par défaut
        return self.default_error_info
    
    def _show_suggestions(self, error: Exception, error_info: Dict) -> None:
        """
        Affiche des suggestions pour résoudre l'erreur.
        
        Args:
            error: Exception d'origine
            error_info: Informations sur le type d'erreur
        """
        # Récupérer les suggestions spécifiques à cette erreur
        suggestions = getattr(error, 'suggestions', error_info['default_suggestions'])
        
        if suggestions:
            self.console.print("\n[bold green]Suggestions:[/]")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"  {i}. {suggestion}")
    
    def _show_traceback(self, error: Exception) -> None:
        """
        Affiche la trace d'exécution formatée.
        
        Args:
            error: Exception d'origine
        """
        self.console.print("\n[bold]Trace d'erreur détaillée:[/]")
        trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        syntax = Syntax(trace, "python", theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def _offer_recovery_options(self, error: Exception) -> None:
        """
        Propose des options de récupération pour certaines erreurs.
        
        Args:
            error: Exception d'origine
        """
        options = []
        
        # Définir les options de récupération selon le type d'erreur
        if isinstance(error, MergeConflictError):
            options.append(("Annuler la fusion", "git merge --abort"))
        elif isinstance(error, DirtyWorkingTreeError):
            options.append(("Stasher les modifications", "git stash"))
            options.append(("Réinitialiser le répertoire de travail (perte de modifications)", "git reset --hard HEAD"))
        elif isinstance(error, SyncError):
            options.append(("Rafraîchir les références distantes", "git fetch --all"))
        
        # Afficher les options si disponibles
        if options:
            self.console.print("\n[bold yellow]Options de récupération:[/]")
            
            for i, (label, command) in enumerate(options, 1):
                self.console.print(f"  {i}. {label} ([dim]`{command}`[/])")
            
            # Demander à l'utilisateur s'il souhaite utiliser une option
            try:
                choice = self.console.input("\n[bold]Choisissez une option (entrez le numéro) ou appuyez sur Entrée pour ignorer: [/]")
                
                if choice and choice.isdigit() and 1 <= int(choice) <= len(options):
                    idx = int(choice) - 1
                    selected_option = options[idx]
                    
                    self.console.print(f"[yellow]Exécution de: {selected_option[1]}[/]")
                    # Dans un vrai programme, on exécuterait réellement la commande ici
                    self.console.print("[green]✓ Commande exécutée avec succès[/]")
            except KeyboardInterrupt:
                pass
    
    def show_warning(self, message: str, title: str = "Avertissement") -> None:
        """
        Affiche un avertissement.
        
        Args:
            message: Message d'avertissement
            title: Titre de l'avertissement
        """
        warning_panel = Panel(
            Text(message, style="yellow"),
            title=f"[bold yellow]⚠️ {title}[/]",
            border_style="yellow"
        )
        self.console.print("\n")
        self.console.print(warning_panel)
    
    def confirm_risky_operation(self, operation: str, details: Optional[str] = None) -> bool:
        """
        Demande confirmation pour une opération risquée.
        
        Args:
            operation: Description de l'opération
            details: Détails supplémentaires
            
        Returns:
            True si l'utilisateur confirme, False sinon
        """
        self.console.print(f"\n[bold yellow]⚠️ Opération risquée: {operation}[/]")
        
        if details:
            self.console.print(f"[yellow]{details}[/]")
        
        return Confirm.ask(
            "[bold]Êtes-vous sûr de vouloir continuer ?[/]",
            default=False,
            console=self.console
        )