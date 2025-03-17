"""
Composants d'interface utilisateur avancés pour GitMove.

Ce module fournit des composants d'interface utilisateur améliorés
pour une meilleure expérience utilisateur, notamment:
- Barres de progression
- Visualisations de branches Git (arbres ASCII)
- Messages d'erreur informatifs
- Formatage avancé des résultats
"""

import os
import time
import threading
from typing import Any, Dict, List, Optional, Callable, Tuple, Union

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskID, SpinnerColumn, TimeElapsedColumn
from rich.status import Status
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.syntax import Syntax
from rich.box import Box, ROUNDED, HEAVY, SIMPLE
from rich.prompt import Confirm

class ProgressManager:
    """
    Gestionnaire de barres de progression pour les opérations longues.
    
    Utilise Rich pour afficher des barres de progression informatives
    avec le temps écoulé et l'état actuel.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialise un gestionnaire de progression.
        
        Args:
            console: Console Rich à utiliser. Si None, en crée une nouvelle.
        """
        self.console = console or Console()
        self.progress = None
        self.active = False
        self.tasks = {}
    
    def start_progress(self, tasks: Optional[List[str]] = None) -> Dict[str, TaskID]:
        """
        Démarre un groupe de barres de progression.
        
        Args:
            tasks: Liste des tâches à afficher. Si None, aucune tâche n'est créée.
            
        Returns:
            Dictionnaire des identifiants de tâches par nom
        """
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=self.console
        )
        
        task_ids = {}
        
        if tasks:
            with self.progress:
                for task_name in tasks:
                    task_id = self.progress.add_task(task_name, total=100)
                    task_ids[task_name] = task_id
                    
                # Conserver la référence aux tâches
                self.tasks = task_ids
                
                # Rendre la progression active
                self.active = True
                
                # Attendre la fin du contexte
                self.progress.refresh()
        
        return task_ids
    
    def update_progress(self, task_name: str, advance: float = 1.0, status: Optional[str] = None):
        """
        Met à jour la progression d'une tâche.
        
        Args:
            task_name: Nom de la tâche à mettre à jour
            advance: Valeur de progression à ajouter
            status: Nouveau statut à afficher (optionnel)
        """
        if not self.active or not self.progress:
            return
            
        task_id = self.tasks.get(task_name)
        if task_id is not None:
            if status:
                self.progress.update(task_id, description=f"{task_name} - {status}", advance=advance)
            else:
                self.progress.update(task_id, advance=advance)
    
    def finish_progress(self, task_name: Optional[str] = None):
        """
        Termine une tâche de progression.
        
        Args:
            task_name: Nom de la tâche à terminer. Si None, termine toutes les tâches.
        """
        if not self.active or not self.progress:
            return
            
        if task_name:
            task_id = self.tasks.get(task_name)
            if task_id is not None:
                self.progress.update(task_id, completed=100)
        else:
            # Terminer toutes les tâches
            for task_id in self.tasks.values():
                self.progress.update(task_id, completed=100)
                
    def show_spinner(self, message: str, func: Callable, *args, **kwargs) -> Any:
        """
        Exécute une fonction avec un spinner pendant son exécution.
        
        Args:
            message: Message à afficher
            func: Fonction à exécuter
            *args: Arguments positionnels pour la fonction
            **kwargs: Arguments nommés pour la fonction
            
        Returns:
            Résultat de la fonction
        """
        with Status(message, console=self.console) as status:
            result = func(*args, **kwargs)
            return result
    
    def __enter__(self):
        """Permet l'utilisation avec un gestionnaire de contexte."""
        if self.progress:
            self.progress.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sortie du gestionnaire de contexte."""
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)
            self.active = False

class BranchVisualizer:
    """
    Visualiseur de branches Git en ASCII art.
    
    Génère des représentations visuelles de l'état des branches
    et des relations entre elles.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialise un visualiseur de branches.
        
        Args:
            console: Console Rich à utiliser. Si None, en crée une nouvelle.
        """
        self.console = console or Console()
    
    def show_branch_tree(self, branches: List[Dict], current_branch: str, main_branch: str):
        """
        Affiche un arbre des branches Git.
        
        Args:
            branches: Liste des informations de branches
            current_branch: Nom de la branche courante
            main_branch: Nom de la branche principale
        """
        # Créer un arbre avec la branche principale comme racine
        tree = Tree(f"[bold green]{main_branch}[/] (principale)")
        
        # Organiser les branches par catégorie
        feature_branches = []
        fix_branches = []
        other_branches = []
        
        for branch in branches:
            branch_name = branch["name"]
            
            # Ignorer la branche principale
            if branch_name == main_branch:
                continue
                
            # Classifier les branches
            if branch_name.startswith(("feature/", "feat/")):
                feature_branches.append(branch)
            elif branch_name.startswith(("fix/", "bugfix/", "hotfix/")):
                fix_branches.append(branch)
            else:
                other_branches.append(branch)
        
        # Ajouter les branches de fonctionnalités
        if feature_branches:
            feature_node = tree.add("[bold blue]Fonctionnalités[/]")
            for branch in feature_branches:
                self._add_branch_node(feature_node, branch, current_branch)
        
        # Ajouter les branches de correction
        if fix_branches:
            fix_node = tree.add("[bold red]Corrections[/]")
            for branch in fix_branches:
                self._add_branch_node(fix_node, branch, current_branch)
        
        # Ajouter les autres branches
        if other_branches:
            other_node = tree.add("[bold yellow]Autres[/]")
            for branch in other_branches:
                self._add_branch_node(other_node, branch, current_branch)
        
        # Afficher l'arbre
        self.console.print(tree)
    
    def _add_branch_node(self, parent_node, branch: Dict, current_branch: str):
        """
        Ajoute un nœud de branche à un parent.
        
        Args:
            parent_node: Nœud parent dans l'arbre
            branch: Informations de la branche
            current_branch: Nom de la branche courante
        """
        branch_name = branch["name"]
        is_current = branch_name == current_branch
        is_merged = branch.get("is_merged", False)
        
        # Formater le nom de la branche
        if is_current:
            style = "[bold green]"
            suffix = " [white]<- branche courante[/]"
        elif is_merged:
            style = "[dim]"
            suffix = " [dim](fusionnée)[/]"
        else:
            style = "[yellow]" if branch.get("behind_commits", 0) > 0 else "[blue]"
            suffix = ""
        
        # Ajouter la date de dernier commit
        last_commit = branch.get("last_commit_date", "inconnue")
        date_info = f"[dim]({last_commit})[/]"
        
        # Ajouter des infos supplémentaires
        ahead = branch.get("ahead_commits", 0)
        behind = branch.get("behind_commits", 0)
        sync_info = ""
        if ahead > 0 or behind > 0:
            sync_info = f" [dim](avance: {ahead}, retard: {behind})[/]"
        
        # Créer le nœud
        label = f"{style}{branch_name}[/] {date_info}{suffix}{sync_info}"
        parent_node.add(label)
    
    def show_branch_comparison(
        self, 
        source_branch: Dict, 
        target_branch: Dict, 
        common_ancestor: Optional[str] = None
    ):
        """
        Affiche une comparaison visuelle entre deux branches.
        
        Args:
            source_branch: Informations sur la branche source
            target_branch: Informations sur la branche cible
            common_ancestor: SHA de l'ancêtre commun
        """
        # Créer une table de comparaison
        table = Table(title="Comparaison de branches", box=ROUNDED)
        
        table.add_column("Propriété", style="cyan")
        table.add_column(f"Branche: {source_branch['name']}", style="green")
        table.add_column(f"Branche: {target_branch['name']}", style="blue")
        
        # Ajouter les informations de base
        table.add_row(
            "Dernier commit",
            source_branch.get("last_commit_date", "inconnue"),
            target_branch.get("last_commit_date", "inconnue")
        )
        
        # Ajouter les informations de divergence
        source_ahead = source_branch.get("ahead_commits", 0)
        source_behind = source_branch.get("behind_commits", 0)
        target_ahead = target_branch.get("ahead_commits", 0)
        target_behind = target_branch.get("behind_commits", 0)
        
        table.add_row(
            "Commits en avance",
            str(source_ahead),
            str(target_ahead)
        )
        
        table.add_row(
            "Commits en retard",
            str(source_behind),
            str(target_behind)
        )
        
        # Ajouter l'information sur l'ancêtre commun
        if common_ancestor:
            table.add_row(
                "Ancêtre commun", 
                common_ancestor[:8] + "...", 
                common_ancestor[:8] + "..."
            )
        
        # Ajouter l'état de fusion
        table.add_row(
            "État de fusion",
            "✅ Fusionnée" if source_branch.get("is_merged", False) else "❌ Non fusionnée",
            "✅ Fusionnée" if target_branch.get("is_merged", False) else "❌ Non fusionnée"
        )
        
        # Afficher la table
        self.console.print(table)
        
        # Visualisation ASCII
        self.console.print()
        self.console.print("Relation des branches:")
        
        # Créer une visualisation ASCII simple
        ancestor_line = " " * 20 + "o Ancêtre commun"
        source_line = " " * 10 + "o" + "-" * 9 + "\\"
        target_line = " " * 30 + "/" + "-" * 9 + "o"
        source_label = " " * 10 + source_branch['name']
        target_label = " " * 30 + target_branch['name']
        
        self.console.print(ancestor_line)
        self.console.print(source_line)
        self.console.print(target_line)
        self.console.print(source_label)
        self.console.print(target_label)

class ErrorFormatter:
    """
    Formateur d'erreurs avancé pour GitMove.
    
    Permet d'afficher des messages d'erreur informatifs avec des
    suggestions de résolution.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialise un formateur d'erreurs.
        
        Args:
            console: Console Rich à utiliser. Si None, en crée une nouvelle.
        """
        self.console = console or Console()
        
        # Base de connaissances pour les erreurs courantes
        self.error_knowledge_base = {
            "git.exc.GitCommandError": {
                "patterns": {
                    "cannot lock ref": {
                        "title": "Erreur de verrouillage de référence Git",
                        "description": "Git ne peut pas verrouiller la référence pour effectuer l'opération.",
                        "suggestions": [
                            "Vérifier si une autre opération Git est en cours",
                            "Supprimer manuellement les fichiers .lock dans .git/refs/",
                            "Redémarrer le daemon Git (si applicable)"
                        ]
                    },
                    "error: failed to push some refs": {
                        "title": "Échec de push des références",
                        "description": "Git n'a pas pu pousser certaines références vers le dépôt distant.",
                        "suggestions": [
                            "Récupérer les dernières modifications avec git pull",
                            "Résoudre les conflits éventuels",
                            "Essayer de forcer le push avec --force (attention aux conséquences)"
                        ]
                    },
                    "refusing to merge unrelated histories": {
                        "title": "Refus de fusionner des historiques non liés",
                        "description": "Git refuse de fusionner deux historiques qui n'ont pas d'ancêtre commun.",
                        "suggestions": [
                            "Utiliser git pull --allow-unrelated-histories",
                            "Vérifier que vous utilisez le bon dépôt distant",
                            "Initialiser le dépôt local avec git clone plutôt que git init"
                        ]
                    }
                },
                "default": {
                    "title": "Erreur de commande Git",
                    "description": "Une erreur s'est produite lors de l'exécution d'une commande Git.",
                    "suggestions": [
                        "Vérifier les permissions des fichiers",
                        "S'assurer que Git est correctement installé",
                        "Vérifier la configuration de Git"
                    ]
                }
            },
            "ValueError": {
                "patterns": {
                    "Invalid configuration": {
                        "title": "Configuration invalide",
                        "description": "La configuration de GitMove contient des erreurs.",
                        "suggestions": [
                            "Vérifier le fichier de configuration (.gitmove.toml)",
                            "Exécuter gitmove config validate pour plus de détails",
                            "Générer un nouveau fichier de configuration avec gitmove config generate"
                        ]
                    }
                },
                "default": {
                    "title": "Erreur de valeur",
                    "description": "Une valeur invalide a été fournie.",
                    "suggestions": [
                        "Vérifier les arguments passés à la commande",
                        "Consulter la documentation pour les valeurs acceptables"
                    ]
                }
            },
            "default": {
                "title": "Erreur inattendue",
                "description": "Une erreur inattendue s'est produite.",
                "suggestions": [
                    "Consulter les journaux pour plus de détails",
                    "Vérifier la configuration de GitMove",
                    "Exécuter la commande avec l'option --verbose pour plus d'informations"
                ]
            }
        }
    
    def format_error(self, error: Exception, verbose: bool = False) -> None:
        """
        Formate et affiche une erreur de manière informative.
        
        Args:
            error: Exception à formater
            verbose: Si True, affiche des informations détaillées
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Chercher les informations d'erreur
        error_info = self._get_error_info(error_type, error_message)
        
        # Créer un panel d'erreur
        error_panel = Panel(
            Text(error_message, style="bold red"),
            title=f"[bold red]{error_info['title']}[/]",
            subtitle=error_type if verbose else None,
            border_style="red"
        )
        
        # Afficher le panel
        self.console.print(error_panel)
        
        # Afficher la description
        self.console.print(f"[yellow]{error_info['description']}[/]")
        
        # Afficher les suggestions
        if error_info['suggestions']:
            self.console.print("\n[bold green]Suggestions:[/]")
            for i, suggestion in enumerate(error_info['suggestions'], 1):
                self.console.print(f"  {i}. {suggestion}")
        
        # Afficher la trace en mode verbeux
        if verbose:
            import traceback
            self.console.print("\n[bold]Trace d'erreur détaillée:[/]")
            trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            syntax = Syntax(trace, "python", theme="monokai", line_numbers=True)
            self.console.print(syntax)
    
    def _get_error_info(self, error_type: str, error_message: str) -> Dict:
        """
        Obtient les informations sur une erreur.
        
        Args:
            error_type: Type d'erreur
            error_message: Message d'erreur
            
        Returns:
            Informations sur l'erreur
        """
        # Obtenir les informations pour ce type d'erreur
        type_info = self.error_knowledge_base.get(error_type, self.error_knowledge_base["default"])
        
        # Vérifier si le message correspond à un modèle connu
        if "patterns" in type_info:
            for pattern, info in type_info["patterns"].items():
                if pattern.lower() in error_message.lower():
                    return info
        
        # Utiliser les informations par défaut pour ce type
        return type_info.get("default", self.error_knowledge_base["default"])
    
    def show_warning(self, message: str, title: str = "Avertissement") -> None:
        """
        Affiche un avertissement.
        
        Args:
            message: Message d'avertissement
            title: Titre de l'avertissement
        """
        warning_panel = Panel(
            Text(message, style="yellow"),
            title=f"[bold yellow]{title}[/]",
            border_style="yellow"
        )
        self.console.print(warning_panel)
    
    def ask_confirmation(self, message: str, default: bool = False) -> bool:
        """
        Demande une confirmation à l'utilisateur.
        
        Args:
            message: Message de confirmation
            default: Valeur par défaut
            
        Returns:
            True si confirmé, False sinon
        """
        return Confirm.ask(message, default=default, console=self.console)

class ResultFormatter:
    """
    Formateur de résultats pour GitMove.
    
    Permet d'afficher les résultats des commandes de manière
    claire et informative.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialise un formateur de résultats.
        
        Args:
            console: Console Rich à utiliser. Si None, en crée une nouvelle.
        """
        self.console = console or Console()
    
    def show_table(
        self, 
        data: List[Dict], 
        columns: List[Tuple[str, str]], 
        title: Optional[str] = None, 
        box: Box = ROUNDED
    ) -> None:
        """
        Affiche un tableau de données.
        
        Args:
            data: Liste de dictionnaires contenant les données
            columns: Liste de tuples (nom_colonne, clé_dans_data)
            title: Titre du tableau
            box: Style de bordure du tableau
        """
        table = Table(title=title, box=box)
        
        # Ajouter les colonnes
        for col_name, _ in columns:
            table.add_column(col_name)
        
        # Ajouter les lignes
        for item in data:
            row = []
            for _, key in columns:
                # Gestion des clés imbriquées avec la notation par points
                if "." in key:
                    parts = key.split(".")
                    value = item
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = "-"
                            break
                else:
                    value = item.get(key, "-")
                
                # Convertir en chaîne
                row.append(str(value))
            
            table.add_row(*row)
        
        # Afficher le tableau
        self.console.print(table)
    
    def show_summary(self, title: str, data: Dict, show_empty: bool = False) -> None:
        """
        Affiche un résumé des résultats.
        
        Args:
            title: Titre du résumé
            data: Dictionnaire de données à afficher
            show_empty: Si True, affiche aussi les valeurs vides
        """
        panel_lines = []
        
        for key, value in data.items():
            # Ignorer les valeurs vides si show_empty est False
            if not show_empty and (value is None or value == "" or value == [] or value == {}):
                continue
                
            # Formater la clé
            formatted_key = key.replace("_", " ").title()
            
            # Formater la valeur
            if isinstance(value, bool):
                formatted_value = "✅ Oui" if value else "❌ Non"
            elif isinstance(value, list):
                if not value:
                    formatted_value = "Aucun"
                else:
                    formatted_value = ", ".join(str(item) for item in value[:5])
                    if len(value) > 5:
                        formatted_value += f" et {len(value) - 5} autres"
            elif isinstance(value, dict):
                if not value:
                    formatted_value = "Aucun"
                else:
                    formatted_value = ", ".join(f"{k}: {v}" for k, v in list(value.items())[:3])
                    if len(value) > 3:
                        formatted_value += f" et {len(value) - 3} autres"
            else:
                formatted_value = str(value)
            
            panel_lines.append(f"[bold]{formatted_key}:[/] {formatted_value}")
        
        # Créer un panel avec le résumé
        panel = Panel(
            "\n".join(panel_lines),
            title=f"[bold]{title}[/]",
            border_style="blue"
        )
        
        # Afficher le panel
        self.console.print(panel)
    
    def show_success(self, message: str, title: str = "Succès") -> None:
        """
        Affiche un message de succès.
        
        Args:
            message: Message de succès
            title: Titre du message
        """
        success_panel = Panel(
            Text(message, style="green"),
            title=f"[bold green]{title}[/]",
            border_style="green"
        )
        self.console.print(success_panel)
    
    def show_code(self, code: str, language: str = "python") -> None:
        """
        Affiche du code formaté avec coloration syntaxique.
        
        Args:
            code: Code à afficher
            language: Langage du code
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

# Classe d'interface principale
class UIManager:
    """
    Gestionnaire d'interface utilisateur pour GitMove.
    
    Coordonne les différents composants d'interface.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialise un gestionnaire d'interface.
        
        Args:
            console: Console Rich à utiliser. Si None, en crée une nouvelle.
        """
        self.console = console or Console()
        self.progress = ProgressManager(self.console)
        self.branch_viz = BranchVisualizer(self.console)
        self.error_fmt = ErrorFormatter(self.console)
        self.result_fmt = ResultFormatter(self.console)
    
    def header(self, title: str, subtitle: Optional[str] = None) -> None:
        """
        Affiche un en-tête de commande.
        
        Args:
            title: Titre principal
            subtitle: Sous-titre optionnel
        """
        self.console.print()
        self.console.print(f"[bold blue]{'=' * 50}[/]")
        self.console.print(f"[bold blue]{title.center(50)}[/]")
        if subtitle:
            self.console.print(f"[blue]{subtitle.center(50)}[/]")
        self.console.print(f"[bold blue]{'=' * 50}[/]")
        self.console.print()
    
    def section(self, title: str) -> None:
        """
        Affiche un titre de section.
        
        Args:
            title: Titre de la section
        """
        self.console.print()
        self.console.print(f"[bold cyan]{title}[/]")
        self.console.print(f"[cyan]{'-' * len(title)}[/]")
    
    def print(self, *args, **kwargs) -> None:
        """
        Affiche du texte.
        
        Args:
            *args: Arguments positionnels pour console.print
            **kwargs: Arguments nommés pour console.print
        """
        self.console.print(*args, **kwargs)