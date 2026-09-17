#!/usr/bin/env bash
# setup_github_ssh.sh
# ----------------------------------------------------------------------------
# One-time per-robot setup: generates an SSH key (if one doesn't already
# exist) and walks through adding it to GitHub, so this machine can
# git pull/push over SSH. Run this once before install_robot_service.sh
# on a freshly-imaged robot.
#
# Usage:
#   ./setup_github_ssh.sh
# ----------------------------------------------------------------------------

set -e

EMAIL="selvambharani100@gmail.com"
KEY="$HOME/.ssh/id_ed25519"

echo "===== GitHub SSH Setup ====="

# Create .ssh directory if needed
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# Generate SSH key if it doesn't exist
if [ ! -f "$KEY" ]; then
    echo "Generating new SSH key..."
    ssh-keygen -t ed25519 -C "$EMAIL" -f "$KEY" -N ""
else
    echo "SSH key already exists."
fi

# Start ssh-agent if needed
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
fi

# Add key to agent
ssh-add "$KEY"

echo
echo "===== Public Key ====="
cat "${KEY}.pub"

echo
echo "Copy the above key and add it to:"
echo "https://github.com/settings/keys"

echo
read -p "Press Enter after adding the key to GitHub..."

echo
echo "===== Testing GitHub Connection ====="

if ssh -T git@github.com; then
    echo
    echo "GitHub SSH setup successful!"
else
    echo
    echo "GitHub authentication completed (GitHub usually exits with status 1 after printing the greeting)."
fi
