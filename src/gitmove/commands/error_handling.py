"""
Gestion des erreurs pour les commandes CLI de GitMove.

Ce module fournit des wrappers et des utilitaires pour gérer les
erreurs dans les commandes CLI de manière élégante.
"""

import sys
import functools
from typing import Callable, Any, Optional

import click
from rich.console import Console

from gitmove.exceptions import GitMoveError, GitError, ConfigError
from gitmove.ui.error_handler import ErrorHandler
from gitmove.utils.logger import get_logger, set_verbose_mode

logger = get_logger(__name__)

def handle_command_errors(verbose_option: str = "verbose"):
    """
    Décorateur pour gérer les erreurs dans les commandes CLI.
    
    Args:
        verbose_option: Nom de l'option de verbosité dans les paramètres de la fonction
        
    Returns:
        Fonction décorée
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extraire l'option verbose
            verbose = kwargs.get(verbose_option, False)
            
            # Configurer le logger
            set_verbose_mode(verbose)
            
            # Créer le gestionnaire d'erreurs
            console = Console()
            error_handler = ErrorHandler(console)
            
            try:
                # Exécuter la fonction
                return func(*args, **kwargs)
            except click.Abort:
                # Interruption volontaire (Ctrl+C)
                console.print("\n[yellow]Opération annulée par l'utilisateur.[/]")
                sys.exit(1)
            except GitMoveError as e:
                # Erreur spécifique à GitMove
                error_handler.handle_error(e, verbose=verbose, exit_on_error=True)
            except Exception as e:
                # Erreur inattendue
                logger.error(f"Erreur inattendue: {str(e)}")
                if verbose:
                    error_handler.handle_error(e, verbose=True, exit_on_error=True)
                else:
                    console.print(f"[bold red]Erreur inattendue:[/] {str(e)}")
                    console.print("[dim]Exécutez la commande avec --verbose pour plus de détails.[/]")
                    sys.exit(1)
        
        return wrapper
    
    return decorator

def confirm_dangerous_operation(
    operation: str, 
    details: Optional[str] = None,
    abort_message: str = "Opération annulée."
) -> bool:
    """
    Demande une confirmation pour une opération dangereuse.
    
    Args:
        operation: Description de l'opération
        details: Détails supplémentaires
        abort_message: Message à afficher en cas d'annulation
        
    Returns:
        True si confirmé, False sinon
    """
    console = Console()
    error_handler = ErrorHandler(console)
    
    confirmed = error_handler.confirm_risky_operation(operation, details)
    
    if not confirmed:
        console.print(f"[yellow]{abort_message}[/]")
        return False
    
    return True

def wrap_click_command(command_func):
    """
    Wrapper pour ajouter la gestion des erreurs aux commandes Click.
    
    Args:
        command_func: Fonction de commande Click à wrapper
        
    Returns:
        Fonction de commande avec gestion des erreurs
    """
    # Appliquer le décorateur de gestion des erreurs
    wrapped_func = handle_command_errors()(command_func)
    
    # Garder les attributs de la commande Click
    wrapped_func.__click_params__ = getattr(command_func, '__click_params__', [])
    wrapped_func.__doc__ = command_func.__doc__
    
    return wrapped_func

def register_error_handlers(cli_group):
    """
    Enregistre des gestionnaires d'erreurs pour toutes les commandes d'un groupe CLI.
    
    Args:
        cli_group: Groupe de commandes Click
    """
    # Parcourir les commandes du groupe
    for name, command in cli_group.commands.items():
        if isinstance(command, click.Command):
            # Sauvegarder la callback originale
            original_callback = command.callback
            
            # Remplacer par une version avec gestion des erreurs
            command.callback = handle_command_errors()(original_callback)
            
        elif isinstance(command, click.Group):
            # Si c'est un sous-groupe, appliquer récursivement
            register_error_handlers(command)
