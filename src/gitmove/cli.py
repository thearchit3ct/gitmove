"""
Interface en ligne de commande pour GitMove
"""

import os
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from gitmove import __version__, get_manager
from gitmove.config import Config
from gitmove.utils.logger import setup_logger
# Import UI components
from gitmove.ui import UIManager

# Import command registration functions
from gitmove.commands import (
    register_config_commands,
    register_cicd_commands,
    generate_ci_config,
    register_env_config_commands
)

# Initialisation de la console rich pour un affichage amélioré
console = Console()
logger = setup_logger()

# Initialisation du gestionnaire d'interface utilisateur
ui_manager = UIManager(console)

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
        # Afficher l'en-tête
        ui_manager.header("Nettoyage des branches Git", "Identification et suppression des branches fusionnées")
        
        # Utiliser le gestionnaire de progression
        with ui_manager.progress as progress:
            # Créer une tâche de progression
            task_id = progress.start_progress(["Recherche des branches fusionnées"])
            
            # Obtenir les gestionnaires
            managers = get_manager(repo_path)
            branch_manager = managers["branch_manager"]
            
            if verbose:
                ui_manager.print("[bold blue]Analyse du dépôt...[/]")
            
            # Mettre à jour la progression
            progress.update_progress("Recherche des branches fusionnées", advance=30)
            
            # Trouver les branches fusionnées
            merged_branches = branch_manager.find_merged_branches(
                include_remote=remote,
                excluded_branches=exclude
            )
            
            # Mettre à jour la progression
            progress.update_progress("Recherche des branches fusionnées", advance=70, status="terminée")
        
        if not merged_branches:
            ui_manager.result_fmt.show_success("Aucune branche fusionnée à nettoyer.", "Dépôt propre")
            return
        
        # Afficher les branches à nettoyer
        ui_manager.section("Branches fusionnées détectées")
        
        # Utiliser le formateur de résultats pour afficher un tableau
        columns = [
            ("Branche", "name"),
            ("Type", lambda b: "Distante" if b["is_remote"] else "Locale"),
            ("Dernière modification", "last_commit_date")
        ]
        
        ui_manager.result_fmt.show_table(
            merged_branches,
            [("Branche", "name"), 
             ("Type", lambda b: "Distante" if b["is_remote"] else "Locale"),
             ("Dernière modification", "last_commit_date")],
            title="Branches fusionnées à nettoyer"
        )
        
        if dry_run:
            ui_manager.error_fmt.show_warning(
                "Mode dry-run: aucune branche ne sera supprimée.",
                "Simulation"
            )
            return
        
        if not force:
            # Utiliser l'assistant de confirmation
            confirm = ui_manager.error_fmt.ask_confirmation(
                "Voulez-vous supprimer ces branches?", 
                default=False
            )
            
            if not confirm:
                ui_manager.print("[yellow]Opération annulée.[/]")
                return
        
        # Afficher la progression de la suppression
        with ui_manager.progress as progress:
            # Créer une tâche de progression
            tasks = progress.start_progress(["Suppression des branches"])
            
            # Effectuer le nettoyage
            result = branch_manager.clean_merged_branches(
                branches=merged_branches,
                include_remote=remote
            )
            
            # Mettre à jour la progression
            progress.finish_progress("Suppression des branches")
        
        # Afficher un résumé du résultat
        ui_manager.result_fmt.show_summary(
            "Résultat du nettoyage",
            {
                "branches_nettoyées": result["cleaned_count"],
                "branches_échouées": result["failed_count"],
                "branches_distantes": sum(1 for b in result["cleaned_branches"] if "/" in b),
                "branches_locales": sum(1 for b in result["cleaned_branches"] if "/" not in b),
            }
        )
        
        # Afficher un message de succès
        ui_manager.result_fmt.show_success(
            f"{result['cleaned_count']} branches ont été supprimées avec succès.",
            "Nettoyage terminé"
        )
        
    except Exception as e:
        # Utiliser le formateur d'erreurs
        ui_manager.error_fmt.format_error(e, verbose=verbose)
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
        # Afficher l'en-tête
        ui_manager.header("Synchronisation de branches", "Mise à jour avec la branche principale")
        
        # Utiliser le gestionnaire de progression
        with ui_manager.progress as progress:
            # Créer des tâches de progression
            tasks = progress.start_progress([
                "Vérification des mises à jour",
                "Analyse de la stratégie",
                "Synchronisation"
            ])
            
            # Obtenir les gestionnaires
            managers = get_manager(repo_path)
            sync_manager = managers["sync_manager"]
            advisor = managers["strategy_advisor"]
            
            # Mettre à jour la progression
            progress.update_progress("Vérification des mises à jour", advance=50)
            
            if verbose:
                ui_manager.print("[bold blue]Recherche des mises à jour...[/]")
            
            # Déterminer la branche à synchroniser
            from gitmove.utils.git_commands import get_current_branch
            current_branch = branch or get_current_branch(managers["repo"])
            main_branch = managers["config"].get_value("general.main_branch")
            
            # Vérifier l'état de synchronisation
            sync_status = sync_manager.check_sync_status(current_branch)
            
            # Mettre à jour la progression
            progress.update_progress("Vérification des mises à jour", advance=50, status="terminée")
            
            # Afficher l'état initial
            ui_manager.section("État actuel")
            
            if sync_status["is_synced"]:
                ui_manager.result_fmt.show_success(
                    f"La branche '{current_branch}' est déjà à jour avec '{main_branch}'.",
                    "Déjà synchronisée"
                )
                return
            
            # Afficher les informations de désynchronisation
            ui_manager.print(f"[bold]Branche:[/] [cyan]{current_branch}[/]")
            ui_manager.print(f"[bold]Cible:[/] [cyan]{main_branch}[/]")
            ui_manager.print(f"[bold]Commits en avance:[/] [yellow]{sync_status['ahead_commits']}[/]")
            ui_manager.print(f"[bold]Commits en retard:[/] [yellow]{sync_status['behind_commits']}[/]")
            
            # Déterminer la stratégie si 'auto'
            if strategy == "auto":
                progress.update_progress("Analyse de la stratégie", advance=50)
                
                # Obtenir un conseil de stratégie
                advice_result = advisor.get_strategy_advice(current_branch, main_branch)
                strategy = advice_result["strategy"]
                
                ui_manager.print(f"\n[bold]Stratégie recommandée:[/] [green]{strategy}[/]")
                ui_manager.print(f"[bold]Raison:[/] [blue]{advice_result['reason']}[/]")
                
                progress.update_progress("Analyse de la stratégie", advance=50, status="terminée")
            else:
                progress.update_progress("Analyse de la stratégie", advance=100, status="terminée")
                ui_manager.print(f"\n[bold]Stratégie sélectionnée:[/] [green]{strategy}[/]")
            
            # Demander confirmation
            confirm = ui_manager.error_fmt.ask_confirmation(
                f"Voulez-vous synchroniser '{current_branch}' avec '{main_branch}' via {strategy}?",
                default=True
            )
            
            if not confirm:
                ui_manager.print("[yellow]Opération annulée.[/]")
                return
            
            # Effectuer la synchronisation
            progress.update_progress("Synchronisation", advance=30, status="en cours")
            
            sync_result = sync_manager.sync_with_main(
                branch_name=current_branch,
                strategy=strategy
            )
            
            progress.update_progress("Synchronisation", advance=70, status="terminée")
        
        # Afficher le résultat
        ui_manager.section("Résultat de la synchronisation")
        
        if sync_result["status"] == "up-to-date":
            ui_manager.result_fmt.show_success(
                f"La branche '{current_branch}' était déjà à jour avec '{main_branch}'.",
                "Déjà à jour"
            )
        elif sync_result["status"] == "synchronized":
            ui_manager.result_fmt.show_success(
                f"Synchronisation de '{current_branch}' avec '{main_branch}' réussie via {sync_result['strategy']}.",
                "Synchronisation réussie"
            )
            
            # Afficher plus de détails si disponibles
            if "details" in sync_result:
                ui_manager.print("\n[bold]Détails:[/]")
                for key, value in sync_result["details"].items():
                    ui_manager.print(f"- [blue]{key}:[/] {value}")
        elif sync_result["status"] == "conflicts":
            ui_manager.error_fmt.show_warning(
                f"La synchronisation a rencontré {len(sync_result['conflicts']['conflicting_files'])} conflits potentiels.",
                "Conflits détectés"
            )
            
            # Afficher les fichiers en conflit
            ui_manager.print("\n[bold]Fichiers en conflit:[/]")
            for conflict in sync_result["conflicts"]["conflicting_files"][:5]:
                ui_manager.print(f"- [red]{conflict['file_path']}[/] ({conflict['severity']})")
            
            if len(sync_result["conflicts"]["conflicting_files"]) > 5:
                ui_manager.print(f"...et {len(sync_result['conflicts']['conflicting_files']) - 5} autres fichiers.")
            
            # Afficher des suggestions pour résoudre les conflits
            ui_manager.print("\n[bold]Suggestions:[/]")
            ui_manager.print("1. [cyan]Utilisez la commande 'check-conflicts' pour analyser les conflits en détail[/]")
            ui_manager.print("   [dim]gitmove check-conflicts[/]")
            ui_manager.print("2. [cyan]Résolvez manuellement les conflits avant de réessayer[/]")
        else:
            ui_manager.error_fmt.show_warning(
                f"Synchronisation incomplète: {sync_result['message']}",
                "Problème rencontré"
            )
            
            if "error" in sync_result:
                ui_manager.print(f"\n[bold red]Erreur:[/] {sync_result['error']}")
        
    except Exception as e:
        # Utiliser le formateur d'erreurs
        ui_manager.error_fmt.format_error(e, verbose=verbose)
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
@click.option(
    "--export", 
    type=click.Path(), 
    help="Exporter les résultats dans un fichier JSON"
)
@click.option(
    "--interactive", "-i", 
    is_flag=True, 
    help="Mode interactif pour explorer les conflits"
)
@add_options(global_options)
def check_conflicts(branch, target, export, interactive, verbose, quiet, config):
    """Détecte les conflits potentiels entre branches"""
    repo_path = get_current_git_repo()
    
    try:
        # Afficher l'en-tête
        ui_manager.header("Détection de conflits", "Analyse des conflits potentiels entre branches")
        
        # Utiliser le gestionnaire de progression
        with ui_manager.progress as progress:
            # Créer des tâches de progression
            tasks = progress.start_progress([
                "Initialisation",
                "Analyse des branches",
                "Détection des conflits"
            ])
            
            # Obtenir les gestionnaires
            managers = get_manager(repo_path)
            conflict_detector = managers["conflict_detector"]
            
            # Mettre à jour la progression
            progress.update_progress("Initialisation", advance=100, status="terminée")
            
            if verbose:
                ui_manager.print("[bold blue]Analyse des branches...[/]")
                
            # Déterminer les branches à comparer
            from gitmove.utils.git_commands import get_current_branch
            current_branch = branch or get_current_branch(managers["repo"])
            main_branch = target or managers["config"].get_value("general.main_branch")
            
            # Mettre à jour la progression
            progress.update_progress("Analyse des branches", advance=100, status="terminée")
            
            if verbose:
                ui_manager.print(f"[bold]Comparaison de [cyan]{current_branch}[/] avec [cyan]{main_branch}[/][/]")
            
            # Mettre à jour la progression
            progress.update_progress("Détection des conflits", advance=50)
            
            # Détecter les conflits
            conflicts = conflict_detector.detect_conflicts(
                branch_name=current_branch,
                target_branch=main_branch
            )
            
            # Mettre à jour la progression
            progress.update_progress("Détection des conflits", advance=50, status="terminée")
        
        # Exporter les résultats si demandé
        if export:
            import json
            try:
                with open(export, 'w') as f:
                    # Nettoyer les données pour l'export (supprimer les champs "diff" volumineux)
                    export_data = conflicts.copy()
                    if "conflicting_files" in export_data:
                        for file_info in export_data["conflicting_files"]:
                            if "diff" in file_info:
                                file_info["diff"] = "... (diff omis pour la lisibilité) ..."
                    
                    json.dump(export_data, f, indent=2)
                
                ui_manager.result_fmt.show_success(
                    f"Résultats de l'analyse exportés dans {export}",
                    "Export réussi"
                )
            except Exception as e:
                ui_manager.error_fmt.show_warning(
                    f"Erreur lors de l'export des résultats: {str(e)}",
                    "Problème d'export"
                )
        
        # Afficher les résultats
        ui_manager.section("Résultat de l'analyse")
        
        if not conflicts["has_conflicts"]:
            ui_manager.result_fmt.show_success(
                "Aucun conflit potentiel détecté. Les branches peuvent être fusionnées sans problème.",
                "Pas de conflits"
            )
            
            # Afficher des détails supplémentaires 
            if "common_modified_files" in conflicts and conflicts["common_modified_files"]:
                ui_manager.print("\n[bold yellow]Fichiers modifiés en commun (sans conflits):[/]")
                for file in conflicts["common_modified_files"][:5]:
                    ui_manager.print(f"  - {file}")
                
                if len(conflicts["common_modified_files"]) > 5:
                    ui_manager.print(f"  ... et {len(conflicts['common_modified_files']) - 5} autres fichiers")
                
                ui_manager.print("\n[green]Ces fichiers ont été modifiés dans les deux branches mais peuvent être fusionnés automatiquement.[/]")
            
            # Afficher la visualisation des branches
            ui_manager.section("Visualisation des branches")
            
            # Récupérer les informations sur les branches
            from gitmove.utils.git_commands import get_branch_divergence, get_common_ancestor
            repo = managers["repo"]
            
            # Obtenir les informations de divergence
            ahead, behind = get_branch_divergence(repo, current_branch, main_branch)
            
            # Créer des objets de branche simplifiés pour la visualisation
            source_branch = {
                "name": current_branch,
                "ahead_commits": ahead,
                "behind_commits": behind
            }
            
            target_branch = {
                "name": main_branch,
                "ahead_commits": behind,
                "behind_commits": ahead
            }
            
            # Obtenir l'ancêtre commun
            common_ancestor = get_common_ancestor(repo, current_branch, main_branch)
            
            # Afficher la comparaison
            ui_manager.branch_viz.show_branch_comparison(
                source_branch,
                target_branch,
                common_ancestor
            )
            
            return
        
        # Afficher le tableau des conflits
        ui_manager.print("[bold red]Conflits potentiels détectés![/]\n")
        
        # Utiliser le formateur de résultats pour afficher un tableau des conflits
        ui_manager.result_fmt.show_table(
            conflicts["conflicting_files"],
            [
                ("Fichier", "file_path"),
                ("Type de conflit", "conflict_type"),
                ("Sévérité", "severity"),
                ("Lignes modifiées", "modified_lines")
            ],
            title="Fichiers en conflit"
        )
        
        # Afficher des statistiques sur les conflits
        ui_manager.section("Statistiques des conflits")
        
        # Calculer des statistiques
        severity_counts = {
            "Élevée": sum(1 for f in conflicts["conflicting_files"] if f["severity"] == "Élevée"),
            "Moyenne": sum(1 for f in conflicts["conflicting_files"] if f["severity"] == "Moyenne"),
            "Faible": sum(1 for f in conflicts["conflicting_files"] if f["severity"] == "Faible")
        }
        
        # Calculer les types de fichiers en conflit
        file_types = {}
        for conflict in conflicts["conflicting_files"]:
            file_type = conflict.get("conflict_type", "Autre")
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        # Calculer le nombre total de lignes modifiées
        total_modified_lines = sum(conflict.get("modified_lines", 0) for conflict in conflicts["conflicting_files"])
        
        # Afficher le résumé
        ui_manager.result_fmt.show_summary(
            "Statistiques des conflits",
            {
                "fichiers_en_conflit": len(conflicts["conflicting_files"]),
                "sévérité": severity_counts,
                "types_de_fichiers": file_types,
                "lignes_modifiées": total_modified_lines,
                "risque_global": (
                    "Élevé" if severity_counts["Élevée"] > 0 else 
                    "Moyen" if severity_counts["Moyenne"] > 2 else 
                    "Faible"
                )
            }
        )
        
        # Mode interactif pour explorer les conflits
        if interactive:
            ui_manager.section("Exploration interactive des conflits")
            
            # Trier les fichiers par sévérité (du plus grave au moins grave)
            sorted_files = sorted(
                conflicts["conflicting_files"], 
                key=lambda x: {"Élevée": 0, "Moyenne": 1, "Faible": 2}.get(x["severity"], 3)
            )
            
            # Permettre à l'utilisateur d'explorer chaque conflit
            for i, conflict in enumerate(sorted_files, 1):
                ui_manager.print(f"\n[bold cyan]Conflit {i}/{len(sorted_files)}:[/] [yellow]{conflict['file_path']}[/]")
                ui_manager.print(f"[bold]Type:[/] {conflict['conflict_type']}")
                ui_manager.print(f"[bold]Sévérité:[/] {conflict['severity']}")
                ui_manager.print(f"[bold]Lignes modifiées:[/] {conflict.get('modified_lines', 'N/A')}")
                
                # Afficher un extrait du diff si disponible
                if "diff" in conflict and conflict["diff"]:
                    ui_manager.print("\n[bold]Aperçu des modifications:[/]")
                    
                    # Limiter la taille du diff affiché
                    diff_preview = conflict["diff"][:500]
                    if len(conflict["diff"]) > 500:
                        diff_preview += "\n... (diff tronqué pour la lisibilité) ..."
                    
                    ui_manager.result_fmt.show_code(diff_preview, "diff")
                
                # Si ce n'est pas le dernier conflit, demander à l'utilisateur s'il veut continuer
                if i < len(sorted_files):
                    continue_exploring = ui_manager.error_fmt.ask_confirmation(
                        "Passer au conflit suivant?", 
                        default=True
                    )
                    
                    if not continue_exploring:
                        ui_manager.print("[yellow]Exploration des conflits interrompue.[/]")
                        break
        
        # Afficher les suggestions
        if conflicts.get("suggestions"):
            ui_manager.section("Suggestions pour minimiser les conflits")
            
            for i, suggestion in enumerate(conflicts["suggestions"], 1):
                ui_manager.print(f"[green]{i}.[/] {suggestion}")
        
        # Afficher la visualisation des branches
        ui_manager.section("Visualisation des branches")
        
        # Récupérer les informations sur les branches
        from gitmove.utils.git_commands import get_branch_divergence, get_common_ancestor
        repo = managers["repo"]
        
        # Obtenir les informations de divergence
        ahead, behind = get_branch_divergence(repo, current_branch, main_branch)
        
        # Créer des objets de branche simplifiés pour la visualisation
        source_branch = {
            "name": current_branch,
            "ahead_commits": ahead,
            "behind_commits": behind,
            "has_conflicts": True
        }
        
        target_branch = {
            "name": main_branch,
            "ahead_commits": behind,
            "behind_commits": ahead,
            "has_conflicts": True
        }
        
        # Obtenir l'ancêtre commun
        common_ancestor = get_common_ancestor(repo, current_branch, main_branch)
        
        # Afficher la comparaison
        ui_manager.branch_viz.show_branch_comparison(
            source_branch,
            target_branch,
            common_ancestor
        )
        
        # Afficher les prochaines étapes
        ui_manager.section("Prochaines étapes recommandées")
        
        if severity_counts["Élevée"] > 0:
            ui_manager.print("[bold]⚠️  Conflits graves détectés[/]")
            ui_manager.print("Il est recommandé de :")
            ui_manager.print("1. [cyan]Synchroniser d'abord avec une stratégie de fusion simple[/]")
            ui_manager.print("   [dim]gitmove sync --strategy merge[/]")
            ui_manager.print("2. [cyan]Résoudre les conflits manuellement[/]")
            ui_manager.print("3. [cyan]Valider les résolutions de conflit[/]")
            
            # Suggérer une approche pour résoudre les conflits critiques
            critical_files = [f["file_path"] for f in conflicts["conflicting_files"] if f["severity"] == "Élevée"]
            if critical_files:
                ui_manager.print("\n[bold]Fichiers critiques à résoudre en priorité:[/]")
                for file in critical_files:
                    ui_manager.print(f"  - [red]{file}[/]")
        else:
            ui_manager.print("[bold]✅ Conflits mineurs détectés[/]")
            ui_manager.print("Il est recommandé de :")
            ui_manager.print("1. [cyan]Synchroniser avec rebase pour maintenir un historique propre[/]")
            ui_manager.print("   [dim]gitmove sync --strategy rebase[/]")
            ui_manager.print("2. [cyan]Résoudre les éventuels conflits[/]")
            
        # Afficher un récapitulatif des commandes disponibles
        ui_manager.print("\n[bold]Commandes utiles:[/]")
        ui_manager.print("- [cyan]gitmove sync --strategy merge[/] - Synchroniser avec merge (plus sûr pour les conflits)")
        ui_manager.print("- [cyan]gitmove sync --strategy rebase[/] - Synchroniser avec rebase (meilleur historique)")
        ui_manager.print("- [cyan]gitmove check-conflicts --interactive[/] - Explorer les conflits en détail")
        ui_manager.print("- [cyan]gitmove advice[/] - Obtenir une recommandation de stratégie")
        
    except Exception as e:
        # Utiliser le formateur d'erreurs
        ui_manager.error_fmt.format_error(e, verbose=verbose)
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
        # Afficher l'en-tête
        ui_manager.header("Statut Git", "État des branches et recommandations")
        
        # Utiliser le gestionnaire de progression
        with ui_manager.progress as progress:
            # Créer des tâches de progression
            tasks = progress.start_progress([
                "Analyse du dépôt",
                "Vérification de la synchronisation",
                "Génération des recommandations"
            ])
            
            # Obtenir les gestionnaires
            managers = get_manager(repo_path)
            branch_manager = managers["branch_manager"]
            sync_manager = managers["sync_manager"]
            advisor = managers["strategy_advisor"]
            config_obj = managers["config"]
            conflict_detector = managers["conflict_detector"]
            
            if verbose:
                ui_manager.print("[bold blue]Analyse en cours...[/]")
            
            # Mettre à jour la progression
            progress.update_progress("Analyse du dépôt", advance=100, status="terminée")
            
            # Informations générales
            current_branch = branch_manager.get_current_branch()
            main_branch = config_obj.get_value("general.main_branch")
            
            # Vérifier si la branche est à jour
            progress.update_progress("Vérification de la synchronisation", advance=50)
            sync_status = sync_manager.check_sync_status(current_branch)
            progress.update_progress("Vérification de la synchronisation", advance=50, status="terminée")
            
            # Recommandations
            progress.update_progress("Génération des recommandations", advance=30)
            
            recommendations = []
            
            if not sync_status["is_synced"]:
                advice_result = advisor.get_strategy_advice(current_branch, main_branch)
                recommendations.append({
                    "title": "Synchronisation recommandée",
                    "description": f"Stratégie recommandée: {advice_result['strategy']}",
                    "reason": advice_result['reason']
                })
                
                # Vérifier les conflits potentiels
                conflicts = conflict_detector.detect_conflicts(current_branch, main_branch)
                if conflicts["has_conflicts"]:
                    recommendations.append({
                        "title": "Conflits potentiels détectés",
                        "description": f"{len(conflicts['conflicting_files'])} fichiers pourraient être en conflit",
                        "files": [f["file_path"] for f in conflicts["conflicting_files"][:3]]
                    })
            
            # Trouver les branches fusionnées
            if detailed:
                merged_branches = branch_manager.find_merged_branches()
                if merged_branches:
                    recommendations.append({
                        "title": "Branches à nettoyer",
                        "description": f"{len(merged_branches)} branches fusionnées peuvent être nettoyées",
                        "branches": [b["name"] for b in merged_branches[:3]]
                    })
            
            progress.update_progress("Génération des recommandations", advance=70, status="terminée")
        
        # Afficher la section d'informations générales
        ui_manager.section("Informations générales")
        
        # Afficher un résumé de l'état
        general_info = {
            "branche_courante": current_branch,
            "branche_principale": main_branch,
            "synchronisé": sync_status["is_synced"],
            "commits_en_retard": sync_status["behind_commits"],
            "commits_en_avance": sync_status["ahead_commits"],
        }
        
        ui_manager.result_fmt.show_summary("État du dépôt", general_info)
        
        # Utiliser le visualiseur de branches si mode détaillé
        if detailed:
            ui_manager.section("Visualisation des branches")
            
            # Récupérer les informations sur toutes les branches
            all_branches = branch_manager.list_branches(include_remote=False)
            
            # Ajouter des informations de synchronisation
            for branch in all_branches:
                if branch["name"] != main_branch:
                    ahead, behind = branch_manager._get_branch_divergence(branch["name"], main_branch)
                    branch["ahead_commits"] = ahead
                    branch["behind_commits"] = behind
            
            # Afficher l'arbre des branches
            ui_manager.branch_viz.show_branch_tree(all_branches, current_branch, main_branch)
        
        # Afficher les recommandations
        if recommendations:
            ui_manager.section("Recommandations")
            
            for i, recommendation in enumerate(recommendations, 1):
                ui_manager.print(f"[bold green]{i}. {recommendation['title']}[/]")
                ui_manager.print(f"   [yellow]{recommendation['description']}[/]")
                
                if "reason" in recommendation:
                    ui_manager.print(f"   [blue]Raison:[/] {recommendation['reason']}")
                
                if "files" in recommendation and recommendation["files"]:
                    ui_manager.print(f"   [cyan]Fichiers concernés:[/] {', '.join(recommendation['files'])}")
                
                if "branches" in recommendation and recommendation["branches"]:
                    ui_manager.print(f"   [cyan]Branches concernées:[/] {', '.join(recommendation['branches'])}")
                
                ui_manager.print("")  # Ligne vide pour séparer les recommandations
        else:
            ui_manager.print("\n[green]Aucune recommandation particulière. Tout semble en ordre ![/]")
        
        # Afficher des suggestions de commandes
        ui_manager.section("Commandes suggérées")
        
        if not sync_status["is_synced"]:
            ui_manager.print("[bold]Pour synchroniser la branche:[/] [cyan]gitmove sync[/]")
            ui_manager.print("[bold]Pour vérifier les conflits:[/] [cyan]gitmove check-conflicts[/]")
        
        if detailed and recommendations and any("Branches à nettoyer" in r["title"] for r in recommendations):
            ui_manager.print("[bold]Pour nettoyer les branches fusionnées:[/] [cyan]gitmove clean[/]")
        
    except Exception as e:
        # Utiliser le formateur d'erreurs
        ui_manager.error_fmt.format_error(e, verbose=verbose)
        sys.exit(1)

@cli.command("completion")
@click.option(
    "--shell", 
    type=click.Choice(["bash", "zsh", "fish", "auto"]), 
    default="auto",
    help="Type de shell pour lequel générer le script de complétion"
)
@click.option(
    "--install", 
    is_flag=True, 
    help="Installer le script de complétion"
)
@click.option(
    "--output", "-o", 
    type=click.Path(), 
    help="Chemin de sortie pour le script de complétion"
)
@add_options(global_options)
def completion(shell, install, output, verbose, quiet, config):
    """Génère ou installe des scripts d'auto-complétion pour les shells"""
    try:
        # Importer le module d'auto-complétion
        from gitmove.ui.autocomplete import (
            generate_bash_completion,
            generate_zsh_completion,
            generate_fish_completion,
            install_completion
        )
        
        # Afficher l'en-tête
        ui_manager.header("Auto-complétion GitMove", "Génération de scripts pour les shells")
        
        # Déterminer le contenu en fonction du type de shell
        if shell == "auto":
            # Détection automatique du shell
            shell_path = os.environ.get('SHELL', '')
            if 'bash' in shell_path:
                shell = 'bash'
            elif 'zsh' in shell_path:
                shell = 'zsh'
            elif 'fish' in shell_path:
                shell = 'fish'
            else:
                ui_manager.error_fmt.show_warning(
                    f"Shell non reconnu: {shell_path}. Utilisation de bash par défaut.",
                    "Détection automatique"
                )
                shell = 'bash'
        
        # Générer le contenu
        if shell == "bash":
            content = generate_bash_completion()
        elif shell == "zsh":
            content = generate_zsh_completion()
        elif shell == "fish":
            content = generate_fish_completion()
        
        # Installer le script si demandé
        if install:
            ui_manager.section(f"Installation du script pour {shell}")
            
            with ui_manager.progress as progress:
                tasks = progress.start_progress([f"Installation pour {shell}"])
                
                # Installer le script
                success, message = install_completion(shell)
                
                progress.finish_progress(f"Installation pour {shell}")
            
            # Afficher le résultat
            if success:
                ui_manager.result_fmt.show_success(
                    message,
                    "Installation réussie"
                )
                
                # Afficher des instructions supplémentaires
                ui_manager.print("\n[bold]Pour activer la complétion immédiatement :[/]")
                
                if shell == "bash":
                    ui_manager.print("    [cyan]source ~/.bashrc[/]")
                elif shell == "zsh":
                    ui_manager.print("    [cyan]source ~/.zshrc[/]")
                    ui_manager.print("    [cyan]autoload -Uz compinit && compinit[/]")
                elif shell == "fish":
                    ui_manager.print("    [cyan]source ~/.config/fish/config.fish[/]")
                
                ui_manager.print("\n[bold]Ou redémarrez votre terminal.[/]")
            else:
                ui_manager.error_fmt.show_warning(
                    message,
                    "Installation échouée"
                )
        # Écrire dans un fichier si demandé
        elif output:
            ui_manager.section(f"Génération du script pour {shell}")
            
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
            
            # Écrire le script
            with open(output, 'w') as f:
                f.write(content)
            
            ui_manager.result_fmt.show_success(
                f"Script d'auto-complétion généré dans {output}",
                "Génération réussie"
            )
            
            # Afficher des instructions d'utilisation
            ui_manager.print("\n[bold]Pour utiliser ce script :[/]")
            
            if shell == "bash":
                ui_manager.print(f"    [cyan]source {output}[/]")
                ui_manager.print(f"    [cyan]echo 'source {output}' >> ~/.bashrc[/]")
            elif shell == "zsh":
                ui_manager.print(f"    [cyan]source {output}[/]")
                ui_manager.print(f"    [cyan]echo 'source {output}' >> ~/.zshrc[/]")
            elif shell == "fish":
                ui_manager.print(f"    [cyan]cp {output} ~/.config/fish/completions/gitmove.fish[/]")
        # Afficher à l'écran
        else:
            ui_manager.section(f"Script d'auto-complétion pour {shell}")
            
            # Afficher le script avec coloration syntaxique
            ui_manager.result_fmt.show_code(content, "bash")
            
            # Afficher des instructions d'utilisation
            ui_manager.print("\n[bold]Pour utiliser ce script :[/]")
            ui_manager.print("    [cyan]1. Enregistrez ce contenu dans un fichier[/]")
            ui_manager.print("    [cyan]2. Utilisez 'source' pour le charger dans votre shell[/]")
            ui_manager.print("    [cyan]3. Ou utilisez l'option --install pour l'installer automatiquement[/]")
        
    except Exception as e:
        # Utiliser le formateur d'erreurs
        ui_manager.error_fmt.format_error(e, verbose=verbose)
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