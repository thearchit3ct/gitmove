"""
Advanced CI/CD Integration Helpers for GitMove

Provides comprehensive tools for managing CI/CD workflows across different platforms.
"""

import os
import re
import sys
import json
import yaml
from typing import Dict, List, Optional, Any

import click
from rich.console import Console
from rich.table import Table

class CICDWorkflowGenerator:
    """
    Advanced workflow generator supporting multiple CI/CD platforms.
    """
    
    SUPPORTED_PLATFORMS = [
        'github_actions', 
        'gitlab_ci', 
        'jenkins', 
        'travis_ci', 
        'circleci'
    ]
    
    def __init__(self, project_type: str = 'python', repo_path: Optional[str] = None):
        """
        Initialize workflow generator.
        
        Args:
            project_type: Type of project (python, js, etc.)
            repo_path: Path to the Git repository
        """
        self.console = Console()
        self.project_type = project_type
        self.repo_path = repo_path or os.getcwd()
        self._detect_project_details()
    
    def _detect_project_details(self):
        """
        Detect project-specific details for more accurate workflow generation.
        """
        self.project_details = {
            'python_version': self._detect_python_version(),
            'dependencies': self._detect_dependencies(),
            'test_command': self._detect_test_command(),
            'linters': self._detect_linters()
        }
    
    def _detect_python_version(self) -> str:
        """
        Detect Python version from pyproject.toml or runtime.txt.
        
        Returns:
            Detected Python version
        """
        # Check pyproject.toml
        try:
            import toml
            with open(os.path.join(self.repo_path, 'pyproject.toml'), 'r') as f:
                config = toml.load(f)
                requires_python = config.get('project', {}).get('requires-python', '')
                if requires_python:
                    # Extract version
                    match = re.search(r'(\d+\.\d+)', requires_python)
                    return match.group(1) if match else '3.8'
        except (ImportError, FileNotFoundError):
            pass
        
        # Check runtime.txt (Heroku style)
        try:
            with open(os.path.join(self.repo_path, 'runtime.txt'), 'r') as f:
                content = f.read()
                match = re.search(r'python-(\d+\.\d+)', content)
                return match.group(1) if match else '3.8'
        except FileNotFoundError:
            pass
        
        return '3.8'  # Default
    
    def _detect_dependencies(self) -> List[str]:
        """
        Detect project dependencies.
        
        Returns:
            List of core dependencies
        """
        dependencies = []
        
        # Check pyproject.toml
        try:
            import toml
            with open(os.path.join(self.repo_path, 'pyproject.toml'), 'r') as f:
                config = toml.load(f)
                dependencies = config.get('project', {}).get('dependencies', [])
        except (ImportError, FileNotFoundError):
            pass
        
        # Fallback to requirements.txt
        if not dependencies:
            try:
                with open(os.path.join(self.repo_path, 'requirements.txt'), 'r') as f:
                    dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except FileNotFoundError:
                pass
        
        return dependencies
    
    def _detect_test_command(self) -> str:
        """
        Detect appropriate test command.
        
        Returns:
            Test command
        """
        # Check for specific test frameworks
        if os.path.exists(os.path.join(self.repo_path, 'pytest.ini')):
            return 'pytest'
        elif os.path.exists(os.path.join(self.repo_path, 'unittest')):
            return 'python -m unittest discover'
        elif os.path.exists(os.path.join(self.repo_path, 'tox.ini')):
            return 'tox'
        
        return 'python -m unittest'
    
    def _detect_linters(self) -> List[str]:
        """
        Detect linters and code quality tools.
        
        Returns:
            List of linters
        """
        linters = []
        
        # Check for common linting tools
        if os.path.exists(os.path.join(self.repo_path, '.flake8')):
            linters.append('flake8')
        if os.path.exists(os.path.join(self.repo_path, 'pyproject.toml')) and 'black' in self._detect_dependencies():
            linters.append('black')
        if os.path.exists(os.path.join(self.repo_path, '.mypy.ini')):
            linters.append('mypy')
        
        return linters
    
    def generate_workflow(self, platform: str = 'github_actions') -> Dict:
        """
        Generate workflow configuration for specified platform.
        
        Args:
            platform: Target CI/CD platform
        
        Returns:
            Workflow configuration dictionary
        """
        if platform not in self.SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Platform-specific workflow generation
        workflow_generators = {
            'github_actions': self._generate_github_actions_workflow,
            'gitlab_ci': self._generate_gitlab_ci_workflow,
            'jenkins': self._generate_jenkins_workflow,
            'travis_ci': self._generate_travis_ci_workflow,
            'circleci': self._generate_circleci_workflow
        }
        
        return workflow_generators[platform]()
    
    def _generate_github_actions_workflow(self) -> Dict:
        """
        Generate GitHub Actions workflow.
        
        Returns:
            GitHub Actions workflow configuration
        """
        return {
            'name': 'GitMove Workflow',
            'on': {
                'push': {'branches': ['main', 'develop']},
                'pull_request': {'branches': ['main', 'develop']}
            },
            'jobs': {
                'build-and-test': {
                    'runs-on': 'ubuntu-latest',
                    'strategy': {
                        'matrix': {
                            'python-version': [
                                self.project_details['python_version'],
                                f"{float(self.project_details['python_version']) + 0.1}"
                            ]
                        }
                    },
                    'steps': [
                        {'uses': 'actions/checkout@v3'},
                        {
                            'name': 'Set up Python ${{ matrix.python-version }}',
                            'uses': 'actions/setup-python@v3',
                            'with': {'python-version': '${{ matrix.python-version }}'}
                        },
                        {
                            'name': 'Install dependencies',
                            'run': '\n'.join([
                                'python -m pip install --upgrade pip',
                                'pip install -e ".[dev]"'
                            ])
                        },
                        {
                            'name': 'Run linters',
                            'run': ' && '.join([
                                f'{linter} .' for linter in self.project_details['linters']
                            ]) if self.project_details['linters'] else 'echo "No linters configured"'
                        },
                        {
                            'name': 'Run tests',
                            'run': self.project_details['test_command']
                        },
                        {
                            'name': 'GitMove Branch Validation',
                            'run': 'gitmove check-conflicts'
                        }
                    ]
                }
            }
        }
    
    def _generate_gitlab_ci_workflow(self) -> Dict:
        """
        Generate GitLab CI workflow.
        
        Returns:
            GitLab CI workflow configuration
        """
        return {
            'image': f'python:{self.project_details["python_version"]}',
            'stages': ['test', 'lint', 'validate'],
            'test': {
                'script': [
                    'pip install -e ".[dev]"',
                    self.project_details['test_command']
                ]
            },
            'lint': {
                'script': [
                    ' && '.join([
                        f'{linter} .' for linter in self.project_details['linters']
                    ]) if self.project_details['linters'] else 'echo "No linters configured"'
                ]
            },
            'validate': {
                'script': ['gitmove check-conflicts']
            }
        }
    
    def _generate_jenkins_workflow(self) -> Dict:
        """
        Generate Jenkins pipeline configuration.
        
        Returns:
            Jenkins pipeline configuration
        """
        return {
            'pipeline': {
                'agent': 'any',
                'stages': [
                    {
                        'stage': 'Build',
                        'steps': [
                            f'use Python {self.project_details["python_version"]}',
                            'pip install -e ".[dev]"'
                        ]
                    },
                    {
                        'stage': 'Lint',
                        'steps': [
                            ' && '.join([
                                f'{linter} .' for linter in self.project_details['linters']
                            ]) if self.project_details['linters'] else 'echo "No linters configured"'
                        ]
                    },
                    {
                        'stage': 'Test',
                        'steps': [self.project_details['test_command']]
                    },
                    {
                        'stage': 'Validate',
                        'steps': ['gitmove check-conflicts']
                    }
                ]
            }
        }
    
    def _generate_travis_ci_workflow(self) -> Dict:
        """
        Generate Travis CI configuration.
        
        Returns:
            Travis CI configuration
        """
        return {
            'language': 'python',
            'python': [
                self.project_details['python_version'],
                f"{float(self.project_details['python_version']) + 0.1}"
            ],
            'install': [
                'pip install -e ".[dev]"'
            ],
            'script': [
                *([' && '.join([f'{linter} .' for linter in self.project_details['linters']])
                   ] if self.project_details['linters'] else []),
                self.project_details['test_command'],
                'gitmove check-conflicts'
            ]
        }
    
    def _generate_circleci_workflow(self) -> Dict:
        """
        Generate CircleCI configuration.
        
        Returns:
            CircleCI configuration
        """
        return {
            'version': 2.1,
            'jobs': {
                'build-and-test': {
                    'docker': [
                        {'image': f'cimg/python:{self.project_details["python_version"]}'}
                    ],
                    'steps': [
                        'checkout',
                        {
                            'run': {
                                'name': 'Install dependencies',
                                'command': 'pip install -e ".[dev]"'
                            }
                        },
                        *([{
                            'run': {
                                'name': 'Run linters',
                                'command': ' && '.join([f'{linter} .' for linter in self.project_details['linters']])
                            }
                        }] if self.project_details['linters'] else []),
                        {
                            'run': {
                                'name': 'Run tests',
                                'command': self.project_details['test_command']
                            }
                        },
                        {
                            'run': {
                                'name': 'GitMove Branch Validation',
                                'command': 'gitmove check-conflicts'
                            }
                        }
                    ]
                }
            },
            'workflows': {
                'version': 2,
                'build-test': {
                    'jobs': ['build-and-test']
                }
            }
        }

class BranchValidator:
    """
    Advanced branch validation and naming convention checker.
    """
    
    DEFAULT_PATTERNS = {
        'feature': r'^feature/([\w-]+)$',
        'bugfix': r'^(bugfix|fix)/([\w-]+)$',
        'hotfix': r'^hotfix/([\w-]+)$',
        'release': r'^release/([\w-]+)$',
        'docs': r'^docs/([\w-]+)$',
        'chore': r'^chore/([\w-]+)$',
        'test': r'^test/([\w-]+)$'
    }
    
    @classmethod
    def validate_branch_name(
        cls, 
        branch_name: str, 
        patterns: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Validate branch name against naming conventions.
        
        Args:
            branch_name: Name of the branch to validate
            patterns: Custom branch naming patterns
        
        Returns:
            Validation result dictionary
        """
        patterns = patterns or cls.DEFAULT_PATTERNS
        
        # Special cases for main branches
        if branch_name in ['main', 'master', 'develop']:
            return {
                'is_valid': True,
                'type': 'main',
                'details': 'Standard main branch'
            }
        
        # Check against patterns
        for branch_type, pattern in patterns.items():
            match = re.match(pattern, branch_name)
            if match:
                return {
                    'is_valid': True,
                    'type': branch_type,
                    'details': match.group(1) if match.groups() else branch_name
                }
        
        return {
            'is_valid': False,
            'type': 'invalid',
            'details': 'Does not match any known branch naming convention'
        }

def register_cicd_commands(cli):
    """
    Register CI/CD related commands to GitMove CLI.
    
    Args:
        cli: Click CLI object
    """
    @cli.group()
    def cicd():
        """CI/CD workflow management commands."""
        pass
    
    @cicd.command('generate-workflow')
    @click.option(
        '--platform', 
        type=click.Choice(['github_actions', 'gitlab_ci', 'jenkins', 'travis_ci', 'circleci']), 
        default='github_actions',
        help='Target CI/CD platform'
    )
    @click.option('--output', '-o', type=click.Path(), help='Output path for workflow file')
    def generate_workflow(platform, output):
        """Generate CI/CD workflow configuration."""
        console = Console()
        generator = CICDWorkflowGenerator()
        
        try:
            workflow = generator.generate_workflow(platform)
            
            # Determine output format and path
            if platform == 'github_actions':
                output_path = output or os.path.join(os.getcwd(), '.github', 'workflows', 'gitmove.yml')
                output_format = 'yaml'
            elif platform == 'gitlab_ci':
                output_path = output or os.path.join(os.getcwd(), '.gitlab-ci.yml')
                output_format = 'yaml'
            elif platform == 'jenkins':
                output_path = output or os.path.join(os.getcwd(), 'Jenkinsfile')
                output_format = 'json'
            elif platform == 'travis_ci':
                output_path = output or os.path.join(os.getcwd(), '.travis.yml')
                output_format = 'yaml'
            elif platform == 'circleci':
                output_path = output or os.path.join(os.getcwd(), '.circleci', 'config.yml')
                output_format = 'yaml'
            else:
                output_path = output or f'workflow_{platform}.json'
                output_format = 'json'
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write workflow configuration
            if output_format == 'yaml':
                with open(output_path, 'w') as f:
                    yaml.dump(workflow, f, default_flow_style=False)
            else:
                with open(output_path, 'w') as f:
                    json.dump(workflow, f, indent=2)
            
            console.print(f"[green]Workflow generated at {output_path}[/green]")
        
        except Exception as e:
            console.print(f"[red]Error generating workflow: {e}[/red]")
            sys.exit(1)
    
    @cicd.command('validate-branch')
    @click.argument('branch_name')
    def validate_branch(branch_name):
        """Validate branch name against naming conventions."""
        console = Console()
        validator = BranchValidator()
        
        result = validator.validate_branch_name(branch_name)
        
        # Create a rich table for display
        table = Table(title="Branch Validation Result")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Branch Name", branch_name)
        table.add_row("Is Valid", "✅ Yes" if result['is_valid'] else "❌ No")
        table.add_row("Branch Type", result['type'])
        table.add_row("Details", result['details'])
        
        console.print(table)
        
        # Exit with appropriate status code
        sys.exit(0 if result['is_valid'] else 1)
    
    @cicd.command('workflow-report')
    @click.option('--output', '-o', type=click.Path(), help='Output path for the report')
    def workflow_report(output):
        """Generate a comprehensive workflow readiness report."""
        console = Console()
        generator = CICDWorkflowGenerator()
        
        # Generate reports for all supported platforms
        report = {}
        for platform in CICDWorkflowGenerator.SUPPORTED_PLATFORMS:
            try:
                workflow = generator.generate_workflow(platform)
                report[platform] = {
                    'workflow_generated': True,
                    'details': {
                        'python_version': generator.project_details['python_version'],
                        'test_command': generator.project_details['test_command'],
                        'linters': generator.project_details['linters'],
                        'dependencies': generator.project_details['dependencies']
                    }
                }
            except Exception as e:
                report[platform] = {
                    'workflow_generated': False,
                    'error': str(e)
                }
        
        # Output the report
        if output:
            with open(output, 'w') as f:
                json.dump(report, f, indent=2)
            console.print(f"[green]Workflow report saved to {output}[/green]")
        else:
            console.print(json.dumps(report, indent=2))

# Utility functions
def detect_ci_environment() -> Optional[Dict]:
    """
    Detect the current CI/CD environment.
    
    Returns:
        Dictionary with CI environment details or None
    """
    ci_env_vars = {
        'github_actions': 'GITHUB_ACTIONS',
        'gitlab_ci': 'GITLAB_CI',
        'travis_ci': 'TRAVIS',
        'circleci': 'CIRCLECI',
        'jenkins': 'JENKINS_HOME',
        'azure_pipelines': 'SYSTEM_TEAMFOUNDATIONCOLLECTIONURI',
        'bitbucket_pipelines': 'BITBUCKET_COMMIT'
    }
    
    detected_ci = {}
    for name, var in ci_env_vars.items():
        if os.environ.get(var):
            detected_ci[name] = {
                'environment': name,
                'branch': os.environ.get('BRANCH_NAME', 'unknown'),
                'commit': os.environ.get('COMMIT', 'unknown')
            }
    
    return detected_ci or None

def generate_ci_config(cli):
    """
    CLI command to detect and generate CI configuration.
    
    Args:
        cli: Click CLI group
    """
    @cli.command('detect-ci')
    def detect_ci():
        """Detect current CI/CD environment."""
        console = Console()
        ci_env = detect_ci_environment()
        
        if ci_env:
            console.print("[green]CI Environment Detected:[/green]")
            for name, details in ci_env.items():
                console.print(f"[blue]{name.replace('_', ' ').title()}:[/blue]")
                for key, value in details.items():
                    console.print(f"  {key}: {value}")
        else:
            console.print("[yellow]No CI environment detected.[/yellow]")

# Optional configuration for handling CI/CD specific workflows
class CICDWorkflowHandler:
    """
    Advanced handler for CI/CD specific workflow operations.
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize CICD Workflow Handler.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = repo_path or os.getcwd()
        self.ci_env = detect_ci_environment()
    
    def run_ci_specific_checks(self):
        """
        Run CI/CD specific checks and validations.
        
        Returns:
            Dictionary of check results
        """
        results = {}
        
        # Branch validation
        current_branch = os.environ.get('BRANCH_NAME', 'unknown')
        branch_validation = BranchValidator.validate_branch_name(current_branch)
        results['branch_validation'] = branch_validation
        
        # Additional checks can be added here
        
        return results