#!/bin/bash
# Install Miniforge on Ubuntu

# Install dependencies
sudo apt update
sudo apt install -y wget curl

# Download the Miniforge installer
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh

# Make the installer executable
chmod +x ~/miniforge.sh

# Run the installer
# -b flag runs in batch mode (no prompts)
# -p specifies the install location
bash ~/miniforge.sh -b -p $HOME/miniforge3

# Clean up the installer
rm ~/miniforge.sh

# Initialize Miniforge in your shell
$HOME/miniforge3/bin/conda init bash

# Add to current session (so you don't have to restart terminal)
export PATH="$HOME/miniforge3/bin:$PATH"

# Print success message
echo "Miniforge has been installed successfully!"
echo "Please restart your terminal or run 'source ~/.bashrc' to use conda commands."
echo "To verify installation, run: conda --version"