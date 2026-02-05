#!/bin/bash
# Backup existing resolv.conf if not already done
if [ ! -f /etc/resolv.conf.bak ]; then
    sudo cp /etc/resolv.conf /etc/resolv.conf.bak
    echo "Backed up original resolv.conf"
fi

# Set Cloudflare DNS
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf > /dev/null
echo "DNS updated to 1.1.1.1 (Cloudflare)"
echo "Current /etc/resolv.conf content:"
cat /etc/resolv.conf

# Test connection (optional, will fail fast if no net)
echo "Testing connection..."
ping -c 3 google.com || echo "Ping failed, but DNS updated. Try docker-compose now."
