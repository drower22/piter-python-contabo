# Use the official n8n image as base
FROM n8nio/n8n:latest

# Switch to the root user to install packages
USER root

# The n8n image is based on Alpine Linux, which uses 'apk' as its package manager.
# We add python3 and pip. The --no-cache flag updates the index, installs, and cleans up in one step.
RUN apk add --no-cache python3 py3-pip



# Create a directory for our application, copy files, and install dependencies.
# We use /opt/app to avoid conflicts with the /home/node directory, which is likely
# managed by a persistent volume at runtime.
RUN mkdir -p /opt/app/scripts

# Copy the python executable itself into our app folder. This makes our app self-contained
# and bypasses the n8n execution sandbox that seems to block access to /usr/bin.
RUN cp /usr/bin/python3.12 /opt/app/python

COPY requirements.txt /opt/app/
RUN pip3 install --no-cache-dir --break-system-packages -r /opt/app/requirements.txt
COPY --chown=node:node scripts/ /opt/app/scripts/

# Switch back to the default non-root n8n user
USER node
