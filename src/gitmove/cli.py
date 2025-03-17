"""
Interface en ligne de commande pour GitMove
"""

import os
import sys
from pathlib import Path

# Add import
from gitmove.cicd import register_cicd_commands, generate_ci_config
from gitmove.config_validator import register_config_commands
import click
from rich.console import Console
from rich.table import Table

from rich.console import Console
from gitmove.config import Config
from gitmove.env_config import register_env_config_commands

from gitmove import __version__, get_manager
from gitmove.config import Config
from gitmove.utils.logger import setup_logger

# Initialisation de la console rich pour un affichage amélioré
console = Console()
logger = setup_logger()

# Options globales partagées par toutes les commandes
global_options = [
    click.option("--verbose", "-v", is_flag=True, help="Affiche des informations détaillées"),
    click.option("--quiet", "-q", is_flag=True, help="Minimise les sorties"),
    click.option(
        "--config", "-c", 
        type=click.Path(exists=False), 
        help="Spécifie un fichier de configuration alternatif"
    ),
]

def add_options(options):
    """Ajoute des options à une commande"""
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options

def get_current_git_repo():
    """Retrouve le dépôt Git courant"""
    try:
        cwd = os.getcwd()
        return cwd
    except Exception as e:
        console.print(f"[bold red]Erreur:[/] {str(e)}")
        sys.exit(1)

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="GitMove")
def cli():
    """
    GitMove - Gestionnaire de branches Git intelligent
    
    Un outil pour simplifier et automatiser la gestion des branches Git.
    """
    pass

register_cicd_commands(cli)
generate_ci_config(cli)
register_env_config_commands(cli)
register_config_commands(cli)
@cli.group()
def config():
    """Commandes de gestion de configuration."""
    pass

@cli.command("clean")
@click.option("--remote", is_flag=True, help="Nettoie également les branches distantes")
@click.option("--dry-run", is_flag=True, help="Simule l'opération sans effectuer de changements")
@click.option("--force", "-f", is_flag=True, help="Ne pas demander de confirmation")
@click.option(
    "--exclude",
    multiple=True, 
    help="Branches à exclure du nettoyage (peut être utilisé plusieurs fois)"
)
@add_options(global_options)
def clean(remote, dry_run, force, exclude, verbose, quiet, config):
    """Nettoie les branches fusionnées"""
    repo_path = get_current_git_repo()
    
    try:
        managers = get_manager(repo_path)
        branch_manager = managers["branch_manager"]
        
        if verbose:
            console.print("[bold blue]Recherche des branches fusionnées...[/]")
        
        merged_branches = branch_manager.find_merged_branches(
            include_remote=remote,
            excluded_branches=exclude
        )
        
        if not merged_branches:
            console.print("[green]Aucune branche fusionnée à nettoyer.[/]")
            return
        
        # Afficher les branches à nettoyer
        table = Table(title="Branches fusionnées à nettoyer")
        table.add_column("Branche", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Dernière modification", style="yellow")
        
        for branch in merged_branches:
            branch_type = "Distante" if branch["is_remote"] else "Locale"
            table.add_row(branch["name"], branch_type, branch["last_commit_date"])
        
        console.print(table)
        
        if dry_run:
            console.print("[yellow]Mode dry-run: aucune branche ne sera supprimée.[/]")
            return
        
        if not force:
            confirm = click.confirm("Voulez-vous supprimer ces branches?", default=False)
            if not confirm:
                console.print("[yellow]Opération annulée.[/]")
                return
        
        result = branch_manager.clean_merged_branches(
            branches=merged_branches,
            include_remote=remote
        )
        
        console.print(f"[green]Nettoyage terminé: {result['cleaned_count']} branches supprimées.[/]")
        
    except Exception as e:
        console.print(f"[bold red]Erreur lors du nettoyage des branches:[/] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

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
@add_options(global_options)
def sync(strategy, branch, verbose, quiet, config):
    """Synchronise la branche courante avec la principale"""
    repo_path = get_current_git_repo()
    
    try:
        managers = get_manager(repo_path)
        sync_manager = managers["sync_manager"]
        
        if verbose:
            console.print("[bold blue]Vérification des mises à jour...[/]")
        
        sync_result = sync_manager.sync_with_main(
            branch_name=branch,
            strategy=strategy
        )
        
        if sync_result["status"] == "up-to-date":
            console.print("[green]La branche est déjà à jour avec la branche principale.[/]")
        elif sync_result["status"] == "synchronized":
            console.print(f"[green]Synchronisation réussie avec la stratégie '{sync_result['strategy']}'.[/]")
        else:
            console.print(f"[yellow]Synchronisation incomplète: {sync_result['message']}[/]")
        
    except Exception as e:
        console.print(f"[bold red]Erreur lors de la synchronisation:[/] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

@config.command('validate')
@click.option('--config', '-c', type=click.Path(exists=True), help='Chemin du fichier de configuration')
def validate_config(config):
    """Valide le fichier de configuration."""
    console = Console()
    
    try:
        config_obj = Config()
        if config:
            config_obj.load_from_file(config)
        
        errors = config_obj.validate()
        
        if not errors:
            console.print("[green]La configuration est valide.[/green]")
            
            # Afficher les recommandations
            recommendations = config_obj.get_recommendations()
            if recommendations:
                console.print("\n[yellow]Recommandations:[/yellow]")
                for key, recommendation in recommendations.items():
                    console.print(f"- {recommendation}")
        else:
            console.print("[red]Erreurs de configuration :[/red]")
            for error in errors:
                console.print(f"  - {error}")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]Erreur lors de la validation : {e}[/red]")
        sys.exit(1)

@config.command('generate')
@click.option('--output', '-o', type=click.Path(), help='Chemin de sortie pour la configuration')
def generate_config(output):
    """Génère un exemple de fichier de configuration."""
    config_obj = Config()
    sample_config = config_obj.generate_sample_config(output)
    
    console = Console()
    if not output:
        console.print(sample_config)
    else:
        console.print(f"[green]Configuration d'exemple générée dans {output}[/green]")

@cli.command("advice")
@click.option(
    "--branch",
    help="Branche à analyser (par défaut: branche courante)"
)
@click.option(
    "--target",
    help="Branche cible (par défaut: branche principale configurée)"
)
@add_options(global_options)
def advice(branch, target, verbose, quiet, config):
    """Suggère une stratégie pour fusionner/rebaser"""
    repo_path = get_current_git_repo()
    
    try:
        managers = get_manager(repo_path)
        advisor = managers["strategy_advisor"]
        
        if verbose:
            console.print("[bold blue]Analyse de la branche et suggestion de stratégie...[/]")
        
        advice_result = advisor.get_strategy_advice(
            branch_name=branch,
            target_branch=target
        )
        
        console.print(f"[bold green]Stratégie recommandée:[/] {advice_result['strategy']}")
        console.print(f"[bold blue]Raison:[/] {advice_result['reason']}")
        
        if advice_result.get("details"):
            console.print("\n[bold]Détails de l'analyse:[/]")
            for key, value in advice_result["details"].items():
                console.print(f"- {key}: {value}")
        
    except Exception as e:
        console.print(f"[bold red]Erreur lors de l'analyse:[/] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

@cli.command("check-conflicts")
@click.option(
    "--branch",
    help="Branche à vérifier (par défaut: branche courante)"
)
@click.option(
    "--target",
    help="Branche cible (par défaut: branche principale configurée)"
)
@add_options(global_options)
def check_conflicts(branch, target, verbose, quiet, config):
    """Détecte les conflits potentiels"""
    repo_path = get_current_git_repo()
    
    try:
        managers = get_manager(repo_path)
        conflict_detector = managers["conflict_detector"]
        
        if verbose:
            console.print("[bold blue]Détection des conflits potentiels...[/]")
        
        conflicts = conflict_detector.detect_conflicts(
            branch_name=branch,
            target_branch=target
        )
        
        if not conflicts["has_conflicts"]:
            console.print("[green]Aucun conflit potentiel détecté.[/]")
            return
        
        console.print("[bold red]Conflits potentiels détectés![/]")
        
        table = Table(title="Fichiers en conflit")
        table.add_column("Fichier", style="cyan")
        table.add_column("Type de conflit", style="yellow")
        table.add_column("Sévérité", style="red")
        
        for conflict in conflicts["conflicting_files"]:
            table.add_row(
                conflict["file_path"],
                conflict["conflict_type"],
                conflict["severity"]
            )
        
        console.print(table)
        
        if conflicts.get("suggestions"):
            console.print("\n[bold green]Suggestions pour minimiser les conflits:[/]")
            for suggestion in conflicts["suggestions"]:
                console.print(f"- {suggestion}")
        
    except Exception as e:
        console.print(f"[bold red]Erreur lors de la détection des conflits:[/] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

@cli.command("init")
@click.option(
    "--config",
    type=click.Path(exists=False),
    help="Chemin vers un fichier de configuration à utiliser comme base"
)
@add_options(global_options)
def init(config, verbose, quiet, **kwargs):
    """Initialise la configuration de gitmove pour le dépôt"""
    repo_path = get_current_git_repo()
    
    try:
        if verbose:
            console.print("[bold blue]Initialisation de la configuration GitMove...[/]")
        
        # Créer une nouvelle configuration
        config_obj = Config()
        
        # Si un fichier de config est spécifié, le charger comme base
        if config and os.path.exists(config):
            config_obj.load_from_file(config)
            if verbose:
                console.print(f"[blue]Configuration chargée depuis {config}[/]")
        
        # Obtenir la branche principale actuelle
        from gitmove.utils.git_commands import get_repo, get_main_branch
        repo = get_repo(repo_path)
        main_branch = get_main_branch(repo)
        
        config_obj.set_value("general.main_branch", main_branch)
        
        # Enregistrer la configuration au niveau du projet
        config_path = os.path.join(repo_path, ".gitmove.toml")
        config_obj.save(config_path)
        
        console.print(f"[green]Configuration initialisée avec succès dans {config_path}[/]")
        console.print(f"[blue]Branche principale détectée: {main_branch}[/]")
        
    except Exception as e:
        console.print(f"[bold red]Erreur lors de l'initialisation:[/] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

@cli.command("status")
@click.option("--detailed", is_flag=True, help="Affiche des informations détaillées")
@add_options(global_options)
def status(detailed, verbose, quiet, config):
    """Affiche l'état actuel des branches et recommandations"""
    repo_path = get_current_git_repo()
    
    try:
        managers = get_manager(repo_path)
        branch_manager = managers["branch_manager"]
        sync_manager = managers["sync_manager"]
        advisor = managers["strategy_advisor"]
        config_obj = managers["config"]
        
        if verbose:
            console.print("[bold blue]Analyse de l'état du dépôt...[/]")
        
        # Informations générales
        current_branch = branch_manager.get_current_branch()
        main_branch = config_obj.get_value("general.main_branch")
        
        console.print(f"[bold green]Branche courante:[/] {current_branch}")
        console.print(f"[bold blue]Branche principale:[/] {main_branch}")
        
        # Vérifier si la branche est à jour
        sync_status = sync_manager.check_sync_status(current_branch)
        
        if sync_status["is_synced"]:
            console.print("[green]La branche est à jour avec la branche principale.[/]")
        else:
            console.print("[yellow]La branche n'est pas à jour avec la branche principale.[/]")
            console.print(f"- {sync_status['behind_commits']} commits en retard")
            console.print(f"- {sync_status['ahead_commits']} commits en avance")
        
        # Recommandations
        if not sync_status["is_synced"]:
            advice_result = advisor.get_strategy_advice(current_branch, main_branch)
            console.print(f"\n[bold]Recommandation:[/] {advice_result['strategy']}")
            console.print(f"[blue]Raison:[/] {advice_result['reason']}")
        
        # Branches fusionnées
        if detailed:
            merged_branches = branch_manager.find_merged_branches()
            if merged_branches:
                console.print("\n[bold]Branches fusionnées qui peuvent être nettoyées:[/]")
                for branch in merged_branches[:5]:  # Limiter à 5 pour l'affichage
                    console.print(f"- {branch['name']}")
                
                if len(merged_branches) > 5:
                    console.print(f"...et {len(merged_branches) - 5} autres branches.")
            
            # Conflits potentiels
            conflict_detector = managers["conflict_detector"]
            conflicts = conflict_detector.detect_conflicts(current_branch, main_branch)
            
            if conflicts["has_conflicts"]:
                console.print("\n[bold red]Avertissement: conflits potentiels détectés![/]")
                console.print(f"- {len(conflicts['conflicting_files'])} fichiers potentiellement en conflit")
            
    except Exception as e:
        console.print(f"[bold red]Erreur lors de l'affichage du statut:[/] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

def main():
    """Point d'entrée principal pour l'outil en ligne de commande"""
    try:
        cli()
    except Exception as e:
        console.print(f"[bold red]Erreur inattendue:[/] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()