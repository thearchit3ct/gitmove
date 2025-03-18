"""
Fonctionnalités d'auto-complétion pour GitMove.

Ce module fournit des fonctionnalités d'auto-complétion pour les shells
et des suggestions intelligentes pour les commandes.
"""

import os
import sys
from typing import List, Dict, Optional, Any, Callable, Set, Tuple

def generate_bash_completion() -> str:
    """
    Génère un script d'auto-complétion pour Bash.
    
    Returns:
        Contenu du script d'auto-complétion
    """
    return """
# GitMove bash completion script

_gitmove_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Liste des commandes principales
    commands="clean sync advice check-conflicts init status config cicd env detect-ci"
    
    # Options globales
    global_opts="--verbose -v --quiet -q --config -c --help -h --version"
    
    # Options spécifiques aux commandes
    clean_opts="--remote --dry-run --force -f --exclude"
    sync_opts="--strategy --branch"
    advice_opts="--branch --target"
    check_conflicts_opts="--branch --target"
    init_opts="--config"
    status_opts="--detailed"
    config_opts="generate validate"
    cicd_opts="generate-workflow validate-branch workflow-report"
    env_opts="generate-template validate list"
    
    # Complétion selon le contexte
    case "${COMP_WORDS[1]}" in
        clean)
            case "$prev" in
                --exclude)
                    # Proposer les branches Git locales
                    local branches=$(git branch --format='%(refname:short)')
                    COMPREPLY=( $(compgen -W "${branches}" -- ${cur}) )
                    return 0
                    ;;
                --strategy)
                    COMPREPLY=( $(compgen -W "merge rebase auto" -- ${cur}) )
                    return 0
                    ;;
                *)
                    COMPREPLY=( $(compgen -W "${clean_opts}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        sync)
            case "$prev" in
                --strategy)
                    COMPREPLY=( $(compgen -W "merge rebase auto" -- ${cur}) )
                    return 0
                    ;;
                --branch)
                    # Proposer les branches Git locales
                    local branches=$(git branch --format='%(refname:short)')
                    COMPREPLY=( $(compgen -W "${branches}" -- ${cur}) )
                    return 0
                    ;;
                *)
                    COMPREPLY=( $(compgen -W "${sync_opts}" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        advice|check-conflicts)
            case "$prev" in
                --branch|--target)
                    # Proposer les branches Git locales
                    local branches=$(git branch --format='%(refname:short)')
                    COMPREPLY=( $(compgen -W "${branches}" -- ${cur}) )
                    return 0
                    ;;
                *)
                    if [[ ${COMP_WORDS[1]} == "advice" ]]; then
                        COMPREPLY=( $(compgen -W "${advice_opts}" -- ${cur}) )
                    else
                        COMPREPLY=( $(compgen -W "${check_conflicts_opts}" -- ${cur}) )
                    fi
                    return 0
                    ;;
            esac
            ;;
        config)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "${config_opts}" -- ${cur}) )
                return 0
            fi
            ;;
        cicd)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "${cicd_opts}" -- ${cur}) )
                return 0
            elif [[ ${COMP_CWORD} -eq 3 && ${COMP_WORDS[2]} == "generate-workflow" ]]; then
                COMPREPLY=( $(compgen -W "--platform --output" -- ${cur}) )
                return 0
            elif [[ ${prev} == "--platform" ]]; then
                COMPREPLY=( $(compgen -W "github_actions gitlab_ci jenkins travis_ci circleci" -- ${cur}) )
                return 0
            fi
            ;;
        env)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "${env_opts}" -- ${cur}) )
                return 0
            fi
            ;;
        *)
            # Complétion des commandes principales ou options globales
            if [[ ${COMP_CWORD} -eq 1 ]]; then
                COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "${global_opts}" -- ${cur}) )
            fi
            return 0
            ;;
    esac
}

# Enregistrement de la fonction de complétion
complete -F _gitmove_completion gitmove
"""

def generate_zsh_completion() -> str:
    """
    Génère un script d'auto-complétion pour Zsh.
    
    Returns:
        Contenu du script d'auto-complétion
    """
    return """
#compdef gitmove

_gitmove() {
    local -a commands
    local -a options
    
    commands=(
        'clean:Nettoie les branches fusionnées'
        'sync:Synchronise la branche courante avec la principale'
        'advice:Suggère une stratégie pour fusionner/rebaser'
        'check-conflicts:Détecte les conflits potentiels'
        'init:Initialise la configuration de gitmove pour le dépôt'
        'status:Affiche l\'état actuel des branches et recommandations'
        'config:Commandes de gestion de configuration'
        'cicd:Commandes de gestion CI/CD'
        'env:Commandes de gestion des variables d\'environnement'
        'detect-ci:Détecte l\'environnement CI courant'
    )
    
    global_options=(
        '--verbose[Affiche des informations détaillées]'
        '-v[Affiche des informations détaillées]'
        '--quiet[Minimise les sorties]'
        '-q[Minimise les sorties]'
        '--config[Spécifie un fichier de configuration alternatif]:fichier:_files'
        '-c[Spécifie un fichier de configuration alternatif]:fichier:_files'
        '--help[Affiche l\'aide]'
        '-h[Affiche l\'aide]'
        '--version[Affiche la version]'
    )
    
    # Sous-commandes pour config
    local -a config_commands
    config_commands=(
        'generate:Génère un exemple de fichier de configuration'
        'validate:Valide le fichier de configuration'
    )
    
    # Sous-commandes pour cicd
    local -a cicd_commands
    cicd_commands=(
        'generate-workflow:Génère un workflow CI/CD'
        'validate-branch:Valide un nom de branche'
        'workflow-report:Génère un rapport sur les workflows'
    )
    
    # Sous-commandes pour env
    local -a env_commands
    env_commands=(
        'generate-template:Génère un modèle de variables d\'environnement'
        'validate:Valide les variables d\'environnement'
        'list:Liste les variables d\'environnement GitMove'
    )
    
    _arguments -C \\
        ${global_options[@]} \\
        ': :->command' \\
        '*:: :->option-or-argument'
        
    case $state in
        command)
            _describe -t commands "Commandes GitMove" commands
            ;;
        option-or-argument)
            case $words[1] in
                clean)
                    _arguments \\
                        '--remote[Nettoie également les branches distantes]' \\
                        '--dry-run[Simule l\'opération sans effectuer de changements]' \\
                        '--force[Ne pas demander de confirmation]' \\
                        '-f[Ne pas demander de confirmation]' \\
                        '*--exclude=[Branches à exclure du nettoyage]:branche:_git_branch_names'
                    ;;
                sync)
                    _arguments \\
                        '--strategy=[Stratégie de synchronisation à utiliser]:stratégie:(merge rebase auto)' \\
                        '--branch=[Branche à synchroniser]:branche:_git_branch_names'
                    ;;
                advice|check-conflicts)
                    _arguments \\
                        '--branch=[Branche à analyser]:branche:_git_branch_names' \\
                        '--target=[Branche cible]:branche:_git_branch_names'
                    ;;
                status)
                    _arguments \\
                        '--detailed[Affiche des informations détaillées]'
                    ;;
                init)
                    _arguments \\
                        '--config=[Chemin vers un fichier de configuration à utiliser comme base]:fichier:_files'
                    ;;
                config)
                    _describe -t config_commands "Commandes de configuration" config_commands
                    case $words[2] in
                        generate)
                            _arguments \\
                                '--output=[Chemin de sortie pour l\'exemple de configuration]:fichier:_files'
                            ;;
                        validate)
                            _arguments \\
                                '--config=[Chemin du fichier de configuration]:fichier:_files'
                            ;;
                    esac
                    ;;
                cicd)
                    _describe -t cicd_commands "Commandes CI/CD" cicd_commands
                    case $words[2] in
                        generate-workflow)
                            _arguments \\
                                '--platform=[Plateforme CI/CD cible]:plateforme:(github_actions gitlab_ci jenkins travis_ci circleci)' \\
                                '--output=[Chemin de sortie pour le fichier de workflow]:fichier:_files'
                            ;;
                        validate-branch)
                            _arguments \\
                                ': :_git_branch_names'
                            ;;
                        workflow-report)
                            _arguments \\
                                '--output=[Chemin de sortie pour le rapport]:fichier:_files'
                            ;;
                    esac
                    ;;
                env)
                    _describe -t env_commands "Commandes de gestion des variables d'environnement" env_commands
                    case $words[2] in
                        generate-template)
                            _arguments \\
                                '--output=[Chemin de sortie pour le modèle]:fichier:_files'
                            ;;
                        validate)
                            _arguments \\
                                '--prefix=[Préfixe des variables d\'environnement]:préfixe'
                            ;;
                    esac
                    ;;
            esac
            ;;
    esac
}

_gitmove
"""

def generate_fish_completion() -> str:
    """
    Génère un script d'auto-complétion pour Fish.
    
    Returns:
        Contenu du script d'auto-complétion
    """
    return """
# GitMove fish completion

function __fish_gitmove_branches
    git branch --format="%(refname:short)" 2>/dev/null
end

function __fish_gitmove_needs_command
    set -l cmd (commandline -opc)
    if [ (count $cmd) -eq 1 ]
        return 0
    end
    return 1
end

function __fish_gitmove_using_command
    set -l cmd (commandline -opc)
    if [ (count $cmd) -gt 1 ]
        if [ $argv[1] = $cmd[2] ]
            return 0
        end
    end
    return 1
end

function __fish_gitmove_using_subcommand
    set -l cmd (commandline -opc)
    if [ (count $cmd) -gt 2 ]
        if [ $argv[1] = $cmd[2] -a $argv[2] = $cmd[3] ]
            return 0
        end
    end
    return 1
end

# Commandes principales
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "clean" -d "Nettoie les branches fusionnées"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "sync" -d "Synchronise la branche courante avec la principale"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "advice" -d "Suggère une stratégie pour fusionner/rebaser"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "check-conflicts" -d "Détecte les conflits potentiels"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "init" -d "Initialise la configuration de gitmove pour le dépôt"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "status" -d "Affiche l'état actuel des branches et recommandations"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "config" -d "Commandes de gestion de configuration"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "cicd" -d "Commandes de gestion CI/CD"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "env" -d "Commandes de gestion des variables d'environnement"
complete -f -c gitmove -n "__fish_gitmove_needs_command" -a "detect-ci" -d "Détecte l'environnement CI courant"

# Options globales
complete -f -c gitmove -s v -l verbose -d "Affiche des informations détaillées"
complete -f -c gitmove -s q -l quiet -d "Minimise les sorties"
complete -f -c gitmove -s c -l config -d "Spécifie un fichier de configuration alternatif" -r
complete -f -c gitmove -s h -l help -d "Affiche l'aide"
complete -f -c gitmove -l version -d "Affiche la version"

# Options pour 'clean'
complete -f -c gitmove -n "__fish_gitmove_using_command clean" -l remote -d "Nettoie également les branches distantes"
complete -f -c gitmove -n "__fish_gitmove_using_command clean" -l dry-run -d "Simule l'opération sans effectuer de changements"
complete -f -c gitmove -n "__fish_gitmove_using_command clean" -s f -l force -d "Ne pas demander de confirmation"
complete -f -c gitmove -n "__fish_gitmove_using_command clean" -l exclude -d "Branches à exclure du nettoyage" -a "(__fish_gitmove_branches)"

# Options pour 'sync'
complete -f -c gitmove -n "__fish_gitmove_using_command sync" -l strategy -d "Stratégie de synchronisation à utiliser" -a "merge rebase auto"
complete -f -c gitmove -n "__fish_gitmove_using_command sync" -l branch -d "Branche à synchroniser" -a "(__fish_gitmove_branches)"

# Options pour 'advice' et 'check-conflicts'
complete -f -c gitmove -n "__fish_gitmove_using_command advice" -l branch -d "Branche à analyser" -a "(__fish_gitmove_branches)"
complete -f -c gitmove -n "__fish_gitmove_using_command advice" -l target -d "Branche cible" -a "(__fish_gitmove_branches)"
complete -f -c gitmove -n "__fish_gitmove_using_command check-conflicts" -l branch -d "Branche à vérifier" -a "(__fish_gitmove_branches)"
complete -f -c gitmove -n "__fish_gitmove_using_command check-conflicts" -l target -d "Branche cible" -a "(__fish_gitmove_branches)"

# Options pour 'status'
complete -f -c gitmove -n "__fish_gitmove_using_command status" -l detailed -d "Affiche des informations détaillées"

# Options pour 'init'
complete -f -c gitmove -n "__fish_gitmove_using_command init" -l config -d "Chemin vers un fichier de configuration à utiliser comme base" -r

# Sous-commandes et options pour 'config'
complete -f -c gitmove -n "__fish_gitmove_using_command config" -a "generate" -d "Génère un exemple de fichier de configuration"
complete -f -c gitmove -n "__fish_gitmove_using_command config" -a "validate" -d "Valide le fichier de configuration"
complete -f -c gitmove -n "__fish_gitmove_using_subcommand config generate" -s o -l output -d "Chemin de sortie pour l'exemple de configuration" -r
complete -f -c gitmove -n "__fish_gitmove_using_subcommand config validate" -s c -l config -d "Chemin du fichier de configuration" -r

# Sous-commandes et options pour 'cicd'
complete -f -c gitmove -n "__fish_gitmove_using_command cicd" -a "generate-workflow" -d "Génère un workflow CI/CD"
complete -f -c gitmove -n "__fish_gitmove_using_command cicd" -a "validate-branch" -d "Valide un nom de branche"
complete -f -c gitmove -n "__fish_gitmove_using_command cicd" -a "workflow-report" -d "Génère un rapport sur les workflows"
complete -f -c gitmove -n "__fish_gitmove_using_subcommand cicd generate-workflow" -l platform -d "Plateforme CI/CD cible" -a "github_actions gitlab_ci jenkins travis_ci circleci"
complete -f -c gitmove -n "__fish_gitmove_using_subcommand cicd generate-workflow" -s o -l output -d "Chemin de sortie pour le fichier de workflow" -r
complete -f -c gitmove -n "__fish_gitmove_using_subcommand cicd validate-branch" -a "(__fish_gitmove_branches)"
complete -f -c gitmove -n "__fish_gitmove_using_subcommand cicd workflow-report" -s o -l output -d "Chemin de sortie pour le rapport" -r

# Sous-commandes et options pour 'env'
complete -f -c gitmove -n "__fish_gitmove_using_command env" -a "generate-template" -d "Génère un modèle de variables d'environnement"
complete -f -c gitmove -n "__fish_gitmove_using_command env" -a "validate" -d "Valide les variables d'environnement"
complete -f -c gitmove -n "__fish_gitmove_using_command env" -a "list" -d "Liste les variables d'environnement GitMove"
complete -f -c gitmove -n "__fish_gitmove_using_subcommand env generate-template" -s o -l output -d "Chemin de sortie pour le modèle" -r
complete -f -c gitmove -n "__fish_gitmove_using_subcommand env validate" -l prefix -d "Préfixe des variables d'environnement"
"""

def install_completion(shell_type: str = 'auto') -> Tuple[bool, str]:
    """
    Installe le script d'auto-complétion pour le shell spécifié.
    
    Args:
        shell_type: Type de shell ('bash', 'zsh', 'fish', 'auto')
        
    Returns:
        Tuple (succès, message)
    """
    # Détection automatique du shell
    if shell_type == 'auto':
        shell_path = os.environ.get('SHELL', '')
        if 'bash' in shell_path:
            shell_type = 'bash'
        elif 'zsh' in shell_path:
            shell_type = 'zsh'
        elif 'fish' in shell_path:
            shell_type = 'fish'
        else:
            return False, f"Shell non reconnu: {shell_path}"
    
    # Générer le contenu du script d'auto-complétion
    if shell_type == 'bash':
        completion_content = generate_bash_completion()
        completion_path = os.path.expanduser("~/.bash_completion.d/gitmove")
        source_line = "[[ -f ~/.bash_completion.d/gitmove ]] && source ~/.bash_completion.d/gitmove"
        rc_file = os.path.expanduser("~/.bashrc")
    elif shell_type == 'zsh':
        completion_content = generate_zsh_completion()
        completion_path = os.path.expanduser("~/.zsh/completions/_gitmove")
        source_line = "fpath=(~/.zsh/completions $fpath)"
        rc_file = os.path.expanduser("~/.zshrc")
    elif shell_type == 'fish':
        completion_content = generate_fish_completion()
        completion_path = os.path.expanduser("~/.config/fish/completions/gitmove.fish")
        source_line = None  # Fish détecte automatiquement les nouveaux scripts
        rc_file = None
    else:
        return False, f"Type de shell non supporté: {shell_type}"
    
    # Créer le répertoire si nécessaire
    os.makedirs(os.path.dirname(completion_path), exist_ok=True)
    
    # Écrire le script d'auto-complétion
    try:
        with open(completion_path, 'w') as f:
            f.write(completion_content)
    except Exception as e:
        return False, f"Erreur lors de l'écriture du script d'auto-complétion: {str(e)}"
    
    # Ajouter la ligne d'importation dans le fichier RC si nécessaire
    if source_line and rc_file:
        try:
            # Vérifier si la ligne existe déjà
            if os.path.exists(rc_file):
                with open(rc_file, 'r') as f:
                    content = f.read()
                if source_line not in content:
                    with open(rc_file, 'a') as f:
                        f.write(f"\n# GitMove auto-completion\n{source_line}\n")
            else:
                with open(rc_file, 'w') as f:
                    f.write(f"# GitMove auto-completion\n{source_line}\n")
        except Exception as e:
            return False, f"Erreur lors de la mise à jour du fichier RC: {str(e)}"
    
    return True, f"Script d'auto-complétion installé pour {shell_type} dans {completion_path}"

class SuggestionEngine:
    """
    Moteur de suggestions pour les commandes GitMove.
    
    Fournit des suggestions intelligentes basées sur l'état du dépôt.
    """
    
    def __init__(self):
        """Initialise le moteur de suggestions."""
        self.suggestions_cache = {}
    
    def get_suggestions(self, context: Dict) -> List[Dict]:
        """
        Obtient des suggestions dans un contexte donné.
        
        Args:
            context: Dictionnaire avec des informations contextuelles
            
        Returns:
            Liste de suggestions (dictionnaires avec title, description, command)
        """
        suggestions = []
        
        # Utiliser le cache si disponible et récent
        if self._is_cache_valid(context):
            return self.suggestions_cache.get('suggestions', [])
        
        repo_state = context.get('repo_state', {})
        current_branch = repo_state.get('current_branch')
        is_clean = repo_state.get('is_clean', True)
        ahead_commits = repo_state.get('ahead_commits', 0)
        behind_commits = repo_state.get('behind_commits', 0)
        
        # Suggestion de nettoyage
        if context.get('merged_branches_count', 0) > 0:
            suggestions.append({
                'title': 'Nettoyage des branches fusionnées',
                'description': f"Il y a {context['merged_branches_count']} branches fusionnées qui pourraient être nettoyées.",
                'command': 'gitmove clean',
            })
        
        # Suggestion de synchronisation
        if behind_commits > 0:
            suggestions.append({
                'title': 'Mettre à jour la branche',
                'description': f"La branche '{current_branch}' est en retard de {behind_commits} commits.",
                'command': 'gitmove sync',
            })
        
        # Suggestion de conflits
        if behind_commits > 0 and ahead_commits > 0:
            suggestions.append({
                'title': 'Vérifier les conflits potentiels',
                'description': f"Votre branche et la branche principale ont divergé ({ahead_commits} et {behind_commits} commits).",
                'command': 'gitmove check-conflicts',
            })
        
        # Suggestion de conseil pour la stratégie
        if ahead_commits > 0:
            suggestions.append({
                'title': 'Obtenir un conseil de stratégie',
                'description': f"Vous avez {ahead_commits} commits locaux. Quelle stratégie utiliser pour les intégrer ?",
                'command': 'gitmove advice',
            })
        
        # Suggestion de statut détaillé
        suggestions.append({
            'title': 'Afficher un statut détaillé',
            'description': "Obtenez une vue détaillée de l'état des branches.",
            'command': 'gitmove status --detailed',
        })
        
        # Mettre à jour le cache
        self._update_cache(context, suggestions)
        
        return suggestions
    
    def _is_cache_valid(self, context: Dict) -> bool:
        """
        Vérifie si le cache est valide pour le contexte actuel.
        
        Args:
            context: Contexte actuel
            
        Returns:
            True si le cache est valide, False sinon
        """
        if not self.suggestions_cache:
            return False
            
        # Vérifier que le contexte n'a pas changé
        cache_context = self.suggestions_cache.get('context', {})
        
        # Comparer les éléments clés
        for key in ['repo_state', 'merged_branches_count']:
            if context.get(key) != cache_context.get(key):
                return False
        
        # Vérifier l'âge du cache (30 secondes max)
        cache_time = self.suggestions_cache.get('timestamp', 0)
        current_time = time.time()
        if current_time - cache_time > 30:
            return False
        
        return True
    
    def _update_cache(self, context: Dict, suggestions: List[Dict]):
        """
        Met à jour le cache de suggestions.
        
        Args:
            context: Contexte actuel
            suggestions: Suggestions générées
        """
        import time
        self.suggestions_cache = {
            'context': context,
            'suggestions': suggestions,
            'timestamp': time.time()
        }