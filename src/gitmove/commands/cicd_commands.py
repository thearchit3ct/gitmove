"""
CLI commands for CI/CD integration in GitMove.

This module provides CLI commands for CI/CD workflow management,
separating command registration from the core CICD functionality.
"""

import os
import sys
import json
import click
from rich.console import Console
from rich.table import Table

from gitmove.cicd import (
    CICDWorkflowGenerator, 
    BranchValidator, 
    detect_ci_environment
)

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
                import yaml
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
    
    return cicd  # Return the group for use in other modules

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