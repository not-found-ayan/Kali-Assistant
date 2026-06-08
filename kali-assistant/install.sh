#!/usr/bin/env bash

# Exit immediately on error
set -e

# Verify executing as root/sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run this installer using sudo:"
  echo "sudo ./install.sh"
  exit 1
fi

echo "[*] Checking and installing environment dependencies..."
apt-get update -y
apt-get install -y python3 python3-tk

echo "[*] Copying utility script to system binary path..."
cp kali_assistant.py /usr/local/bin/kali-assistant
chmod +x /usr/local/bin/kali-assistant

echo "[*] Generating system desktop application profile..."
cat <<EOF > /usr/share/applications/kali-assistant.desktop
[Desktop Entry]
Name=Terminal Quick Assistant
Comment=Generate and execute Kali terminal commands
Exec=/usr/local/bin/kali-assistant
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Development;System;Utility;
StartupNotify=true
EOF

echo "[*] Updating desktop shortcuts..."
update-desktop-database || true

echo "------------------------------------------------------"
echo "[+] Installation complete!"
echo "[+] You can now launch 'Terminal Quick Assistant' from your applications menu"
echo "[+] Or execute 'kali-assistant' in any terminal window."
echo "------------------------------------------------------"
