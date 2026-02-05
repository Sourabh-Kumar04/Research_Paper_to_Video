#!/bin/bash
echo "Setting up /etc/wsl.conf..."

# Create wsl.conf to stop auto-generation of resolv.conf
sudo tee /etc/wsl.conf <<EOF
[network]
generateResolvConf = false
EOF

echo "Created /etc/wsl.conf"

# Force DNS again just in case
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf > /dev/null
echo "DNS reset to 8.8.8.8"

echo "diagnostic: local IP check"
ip addr | grep eth0

echo "DONE. Please run 'wsl --shutdown' in PowerShell now."
