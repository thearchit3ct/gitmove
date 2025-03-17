# Set environment variables
export GITMOVE_GENERAL_VERBOSE=true
export GITMOVE_SYNC_DEFAULT_STRATEGY=rebase

# Generate environment variable template
gitmove env generate-template

# Validate current environment configuration
gitmove env validate

# List current GitMove environment variables
gitmove env list