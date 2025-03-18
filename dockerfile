FROM python:3.10-slim

LABEL org.opencontainers.image.source="https://github.com/thearchit3ct/gitmove"
LABEL org.opencontainers.image.description="GitMove - Gestionnaire de branches Git intelligent"
LABEL org.opencontainers.image.licenses="MIT"

# Installer Git
RUN apt-get update && apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configurer Git
RUN git config --global user.name "GitMove Docker" && \
    git config --global user.email "gitmove@docker.local"

# Créer un utilisateur non-root pour l'exécution
RUN useradd -m gitmove

# Créer les répertoires pour les données
RUN mkdir -p /app /data /home/gitmove/.config/gitmove && \
    chown -R gitmove:gitmove /app /data /home/gitmove/.config

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers du projet
COPY --chown=gitmove:gitmove . /app/

# Installer le package
RUN pip install --no-cache-dir -e .

# Utiliser l'utilisateur non-root
USER gitmove

# Définir le volume pour les dépôts Git
VOLUME ["/data"]

# Définir le répertoire de travail pour l'exécution
WORKDIR /data

# Commande par défaut
ENTRYPOINT ["gitmove"]
CMD ["--help"]