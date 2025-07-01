# Use the official n8n image as base
FROM n8nio/n8n:latest

# Switch to the root user to install packages
USER root

# Update package lists and install python3 and pip.
# The --no-install-recommends flag avoids installing unnecessary packages.
# Clean up apt-get cache to keep the image size down.
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Switch back to the default non-root n8n user
USER node
