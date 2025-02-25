#!/usr/bin/env python
"""
Script d'installation pour GitMove.

Ce fichier est fourni pour la compatibilité avec les anciens outils et systèmes
qui ne supportent pas encore pleinement pyproject.toml (PEP 518).
Les métadonnées principales du projet sont définies dans pyproject.toml.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

from setuptools import find_packages, setup

# Fonction pour lire les métadonnées depuis pyproject.toml
def read_pyproject_toml():
    """Lit les principales métadonnées depuis pyproject.toml."""
    import toml
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            return toml.load(f)
    except ImportError:
        print("Le package toml est requis pour lire pyproject.toml.")
        print("Installez-le avec 'pip install toml'.")
        sys.exit(1)
    except FileNotFoundError:
        print("Fichier pyproject.toml introuvable. Exécutez setup.py depuis le répertoire racine du projet.")
        sys.exit(1)

# Lire le contenu du README pour la description longue
def read_readme():
    """Lit le contenu du fichier README.md."""
    with open("README.md", encoding="utf-8") as f:
        return f.read()

# Récupérer les métadonnées depuis pyproject.toml
try:
    pyproject = read_pyproject_toml()
    project_data = pyproject.get("project", {})
    tools_data = pyproject.get("tool", {}).get("setuptools", {})
except Exception as e:
    print(f"Erreur lors de la lecture de pyproject.toml: {e}")
    # Définir des valeurs par défaut si pyproject.toml ne peut pas être lu
    project_data = {
        "name": "gitmove",
        "version": "0.1.0",
        "description": "Gestionnaire de branches Git intelligent",
        "dependencies": [
            "gitpython>=3.1.0",
            "click>=8.0.0",
            "rich>=10.0.0",
            "toml>=0.10.0",
        ],
    }
    tools_data = {}

# Extraire les informations auteurs depuis project_data
authors = []
for author in project_data.get("authors", []):
    author_name = author.get("name", "")
    author_email = author.get("email", "")
    if author_name and author_email:
        authors.append(f"{author_name} <{author_email}>")
    elif author_name:
        authors.append(author_name)

# Configuration de setup()
setup(
    name=project_data.get("name", "gitmove"),
    version=project_data.get("version", "0.1.0"),
    description=project_data.get("description", "Gestionnaire de branches Git intelligent"),
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author=", ".join(authors) if authors else "GitMove Contributors",
    url=project_data.get("urls", {}).get("Homepage", "https://github.com/username/gitmove"),
    
    # Configuration des packages
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Configuration des scripts et points d'entrée
    entry_points={
        "console_scripts": [
            "gitmove=gitmove.cli:main",
        ],
    },
    
    # Dépendances
    python_requires=">=3.8",
    install_requires=[dep.split(">=")[0] for dep in project_data.get("dependencies", [])],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
            "pytest-cov>=4.0.0",
        ],
    },
    
    # Métadonnées supplémentaires
    classifiers=project_data.get("classifiers", [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Version Control :: Git",
    ]),
    license="MIT",
    keywords="git branch management workflow automation",
    project_urls=project_data.get("urls", {
        "Bug Tracker": "https://github.com/username/gitmove/issues",
        "Documentation": "https://github.com/thearchit3ct/gitmove/wiki",
    }),
    
    # Options supplémentaires
    zip_safe=False,
    include_package_data=True,
)