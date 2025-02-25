"""
Configuration du système de journalisation pour GitMove.

Ce module fournit des fonctions pour configurer et obtenir des loggers.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

# Configuration par défaut
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Dossier pour les logs
LOG_DIR = os.path.expanduser("~/.gitmove/logs")

def setup_logger(
    level: Optional[int] = None, 
    log_to_file: bool = True, 
    log_to_console: bool = True
) -> logging.Logger:
    """
    Configure le logger principal de l'application.
    
    Args:
        level: Niveau de log (DEBUG, INFO, etc.). Si None, utilise le niveau par défaut.
        log_to_file: Si True, journalise dans un fichier
        log_to_console: Si True, journalise dans la console
        
    Returns:
        Logger configuré
    """
    if level is None:
        level = DEFAULT_LOG_LEVEL
    
    # Créer le logger racine
    logger = logging.getLogger("gitmove")
    logger.setLevel(level)
    
    # Éviter les gestionnaires en double
    if logger.handlers:
        return logger
    
    # Formatter pour les logs
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_LOG_DATE_FORMAT)
    
    # Journalisation dans la console
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    # Journalisation dans un fichier
    if log_to_file:
        try:
            # Créer le dossier des logs s'il n'existe pas
            os.makedirs(LOG_DIR, exist_ok=True)
            
            # Fichier de log
            log_file = os.path.join(LOG_DIR, "gitmove.log")
            
            # Handler avec rotation des fichiers
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=1024 * 1024,  # 1 MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except Exception as e:
            # En cas d'erreur, on continue avec uniquement la console
            logger.warning(f"Impossible de configurer la journalisation dans le fichier: {str(e)}")
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Obtient un logger pour un module spécifique.
    
    Args:
        name: Nom du module. Si None, renvoie le logger racine.
        
    Returns:
        Logger pour le module spécifié
    """
    if name is None:
        return logging.getLogger("gitmove")
    
    # Obtenir un logger pour un sous-module
    return logging.getLogger(f"gitmove.{name}")

def set_verbose_mode(verbose: bool = True):
    """
    Active ou désactive le mode verbeux pour les logs.
    
    Args:
        verbose: Si True, active le mode DEBUG
    """
    logger = logging.getLogger("gitmove")
    
    if verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(DEFAULT_LOG_LEVEL)
        for handler in logger.handlers:
            handler.setLevel(DEFAULT_LOG_LEVEL)

def set_quiet_mode(quiet: bool = True):
    """
    Active ou désactive le mode silencieux pour les logs.
    
    Args:
        quiet: Si True, désactive tous les logs sauf les erreurs
    """
    logger = logging.getLogger("gitmove")
    
    if quiet:
        logger.setLevel(logging.ERROR)
        for handler in logger.handlers:
            handler.setLevel(logging.ERROR)
    else:
        logger.setLevel(DEFAULT_LOG_LEVEL)
        for handler in logger.handlers:
            handler.setLevel(DEFAULT_LOG_LEVEL)