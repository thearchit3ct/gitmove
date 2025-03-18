"""
Commandes de synchronisation améliorées pour GitMove.

Ce module fournit des commandes CLI améliorées pour la synchronisation
des branches Git avec une meilleure gestion des erreurs.
"""

import os
import sys
from typing import Optional

import click
from rich.console import Console

from gitmove.utils.logger import get_logger
from gitmove.commands.error_handling import handle_command_errors, confirm_dangerous_operation

logger = get_logger(__name__)

def register_sync_commands(cli):
    """
    Enregistre les commandes de synchronisation.
    
    Args:
        cli: Groupe de commandes Click
    """
    @cli.command("sync")
    @click.option(
        "--strategy", 
        type=click.Choice(["merge", "rebase", "auto"]), 
        default="auto",
        help="Stratégie de synchronisation à utiliser"
    )
    @click.option(
        "--branch", 
        help="Branche à synchroniser (par défaut: branche courante)"
    )
    @click.option(
        "--force", "-f", 
        is_flag=True, 
        help="Forcer la synchronisation même en cas de conflits potentiels"
    )
    @click.option("--verbose", "-v", is_flag=True, help="Affiche des informations détaillées")
    @click.option("--quiet", "-q", is_flag=True, help="Minimise les sorties")
    @click.option(
        "--config", "-c", 
        type=click.Path(exists=False), 
        help="Spécifie un fichier de configuration alternatif"
    )
    @handle_command_errors()
    def sync(strategy, branch, force, verbose, quiet, config):
        """Synchronise la branche courante avec la principale"""
        # Importation à l'intérieur de la fonction pour éviter les importations circulaires
        from gitmove import get_manager
        from gitmove.core.sync_manager import SyncManager
        from gitmove.utils.git_commands import get_current_branch
        
        console = Console()
        
        try:
            # Récupérer le dépôt Git courant
            repo_path = os.getcwd()
            
            # Récupérer le gestionnaire
            managers = get_manager(repo_path)
            
            # Créer un gestionnaire de synchronisation
            sync_manager = SyncManager(managers["repo"], managers["config"])
            
            # Afficher l'en-tête
            console.print()
            console.print(f"[bold blue]{'=' * 50}[/]")
            console.print(f"[bold blue]Synchronisation de branches[/]".center(50))
            console.print(f"[blue]Mise à jour avec la branche principale[/]".center(50))
            console.print(f"[bold blue]{'=' * 50}[/]")
            console.print()
            
            # Utiliser le gestionnaire de progression
            with console.status("[blue]Vérification des mises à jour...[/]") as status:
                # Déterminer la branche à synchroniser
                current_branch = branch or get_current_branch(managers["repo"])
                main_branch = managers["config"].get_value("general.main_branch")
                
                # Vérifier l'état de synchronisation
                sync_status = sync_manager.check_sync_status(current_branch)
            
            # Afficher l'état initial
            console.print("[bold]État actuel:[/]")
            
            if sync_status["is_synced"]:
                console.print(f"[green]✓ La branche '{current_branch}' est déjà à jour avec '{main_branch}'.[/]")
                return
            
            # Afficher les informations de désynchronisation
            console.print(f"[bold]Branche:[/] [cyan]{current_branch}[/]")
            console.print(f"[bold]Cible:[/] [cyan]{main_branch}[/]")
            console.print(f"[bold]Commits en avance:[/] [yellow]{sync_status['ahead_commits']}[/]")
            console.print(f"[bold]Commits en retard:[/] [yellow]{sync_status['behind_commits']}[/]")
            
            # Déterminer la stratégie si 'auto'
            if strategy == "auto":
                with console.status("[blue]Analyse de la stratégie optimale...[/]") as status:
                    # Obtenir un conseil de stratégie
                    advice_result = managers["strategy_advisor"].get_strategy_advice(current_branch, main_branch)
                    strategy = advice_result["strategy"]
                
                console.print(f"\n[bold]Stratégie recommandée:[/] [green]{strategy}[/]")
                console.print(f"[bold]Raison:[/] [blue]{advice_result['reason']}[/]")
            else:
                console.print(f"\n[bold]Stratégie sélectionnée:[/] [green]{strategy}[/]")
            
            # Vérifier les conflits potentiels
            if not force:
                with console.status("[blue]Détection des conflits potentiels...[/]") as status:
                    conflicts = managers["conflict_detector"].detect_conflicts(current_branch, main_branch)
                
                if conflicts["has_conflicts"]:
                    console.print(f"[bold red]⚠️ La synchronisation a détecté {len(conflicts['conflicting_files'])} conflit(s) potentiel(s).[/]")
                    
                    # Afficher les fichiers en conflit
                    console.print("\n[bold]Fichiers en conflit:[/]")
                    for conflict in conflicts["conflicting_files"][:5]:
                        console.print(f"- [red]{conflict['file_path']}[/] ({conflict['severity']})")
                    
                    if len(conflicts["conflicting_files"]) > 5:
                        console.print(f"...et {len(conflicts['conflicting_files']) - 5} autres fichiers.")
                    
                    # Demander confirmation
                    confirmed = confirm_dangerous_operation(
                        "Synchronisation avec conflits potentiels",
                        "Les conflits détectés pourraient nécessiter une résolution manuelle."
                    )
                    
                    if not confirmed:
                        console.print("[yellow]Opération annulée.[/]")
                        console.print("Utilisez l'option --force pour ignorer les vérifications de conflits.")
                        return
            
            # Demander confirmation
            if not force:
                confirm = click.confirm(
                    f"Voulez-vous synchroniser '{current_branch}' avec '{main_branch}' via {strategy}?",
                    default=True
                )
                
                if not confirm:
                    console.print("[yellow]Opération annulée.[/]")
                    return
            
            # Effectuer la synchronisation
            with console.status(f"[blue]Synchronisation en cours...[/]") as status:
                sync_result = sync_manager.sync_with_main(
                    branch_name=current_branch,
                    strategy=strategy
                )
            
            # Afficher le résultat
            console.print("\n[bold]Résultat de la synchronisation:[/]")
            
            if sync_result["status"] == "up-to-date":
                console.print(f"[green]✓ La branche '{current_branch}' était déjà à jour avec '{main_branch}'.[/]")
            elif sync_result["status"] == "synchronized":
                console.print(f"[green]✓ Synchronisation de '{current_branch}' avec '{main_branch}' réussie via {sync_result['strategy']}.[/]")
                
                # Afficher plus de détails si disponibles
                if "details" in sync_result:
                    console.print("\n[bold]Détails:[/]")
                    for key, value in sync_result["details"].items():
                        console.print(f"- [blue]{key}:[/] {value}")
            elif sync_result["status"] == "conflicts":
                console.print(f"[bold red]⚠️ La synchronisation a rencontré {len(sync_result['conflicts']['conflicting_files'])} conflit(s) potentiel(s).[/]")
                
                # Afficher les fichiers en conflit
                console.print("\n[bold]Fichiers en conflit:[/]")
                for conflict in sync_result["conflicts"]["conflicting_files"][:5]:
                    console.print(f"- [red]{conflict['file_path']}[/] ({conflict['severity']})")
                
                if len(sync_result["conflicts"]["conflicting_files"]) > 5:
                    console.print(f"...et {len(sync_result['conflicts']['conflicting_files']) - 5} autres fichiers.")
                
                # Afficher des suggestions pour résoudre les conflits
                console.print("\n[bold]Suggestions:[/]")
                console.print("1. [cyan]Utilisez la commande 'check-conflicts' pour analyser les conflits en détail[/]")
                console.print("   [dim]gitmove check-conflicts[/]")
                console.print("2. [cyan]Résolvez manuellement les conflits avant de réessayer[/]")
            else:
                console.print(f"[bold yellow]⚠️ Synchronisation incomplète: {sync_result['message']}[/]")
                
                if "error" in sync_result:
                    console.print(f"\n[bold red]Erreur:[/] {sync_result['error']}")
            
        except Exception as e:
            console.print(f"[bold red]Erreur lors de la synchronisation:[/] {str(e)}")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            sys.exit(1)
    
    @cli.command("force-sync")
    @click.option(
        "--strategy", 
        type=click.Choice(["merge", "rebase"]), 
        default="merge",
        help="Stratégie de synchronisation à utiliser"
    )
    @click.option(
        "--branch", 
        help="Branche à synchroniser (par défaut: branche courante)"
    )
    @click.option("--verbose", "-v", is_flag=True, help="Affiche des informations détaillées")
    @click.option("--quiet", "-q", is_flag=True, help="Minimise les sorties")
    @click.option(
        "--config", "-c", 
        type=click.Path(exists=False), 
        help="Spécifie un fichier de configuration alternatif"
    )
    def force_sync(strategy, branch, verbose, quiet, config):
        """
        Force la synchronisation d'une branche même en cas de conflits potentiels.
        
        Cette commande est à utiliser avec précaution, car elle ignore les vérifications
        de conflits potentiels et peut nécessiter une résolution manuelle des conflits.
        """
        # Appeler la commande sync avec l'option force activée
        return sync(strategy, branch, True, verbose, quiet, config)
    
    return sync

# Fonction principale pour les tests directs du module
if __name__ == "__main__":
    import click
    
    @click.group()
    def cli():
        pass
    
    register_sync_commands(cli)
    
    cli()
