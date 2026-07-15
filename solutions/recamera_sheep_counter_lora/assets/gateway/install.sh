#!/usr/bin/env bash
set -euo pipefail

# Sheep Counter Gateway Install Script
# Deploys meshtastic_mqtt_bridge and ha_bridge to a reComputer/Raspberry Pi
# with systemd auto-start.

INSTALL_DIR="/opt/sheep-gateway"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# User inputs (injected by deployer)
HA_HOST="${HA_HOST:-127.0.0.1}"
HA_TOKEN="${HA_TOKEN:-}"
MQTT_HOST="${MQTT_HOST:-127.0.0.1}"
SERIAL_PORT="${SERIAL_PORT:-/dev/ttyACM0}"

echo "[install] Sheep Counter Gateway installer"
echo "[install] Target: $INSTALL_DIR"

# 1. Ensure Python 3 and pip are available
if ! command -v python3 &>/dev/null; then
    echo "[install] python3 not found — attempting install..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip
    elif command -v apk &>/dev/null; then
        sudo apk add --no-cache python3 py3-pip
    else
        echo "[install] ERROR: no package manager found. Install python3 manually." >&2
        exit 1
    fi
fi

# 2. Install Python dependencies
echo "[install] Installing Python dependencies..."
pip3 install --user --quiet paho-mqtt meshtastic requests 2>/dev/null || \
    pip3 install --quiet paho-mqtt meshtastic requests

# 3. Create install directory and copy scripts
echo "[install] Copying bridge scripts to $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp "$SCRIPT_DIR/meshtastic_mqtt_bridge.py" "$INSTALL_DIR/"
sudo cp "$SCRIPT_DIR/ha_bridge.py" "$INSTALL_DIR/"
sudo cp "$SCRIPT_DIR/ha_dashboard.yaml" "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/meshtastic_mqtt_bridge.py" "$INSTALL_DIR/ha_bridge.py"

# 4. Write environment file
echo "[install] Writing environment file..."
cat | sudo tee "$INSTALL_DIR/.env" >/dev/null <<EOF
HA_HOST=$HA_HOST
HA_TOKEN=$HA_TOKEN
MQTT_HOST=$MQTT_HOST
SERIAL_PORT=$SERIAL_PORT
EOF
sudo chmod 600 "$INSTALL_DIR/.env"

# 5. Write systemd service for meshtastic-bridge
echo "[install] Creating systemd service: meshtastic-bridge..."
cat | sudo tee /etc/systemd/system/meshtastic-bridge.service >/dev/null <<'EOF'
[Unit]
Description=Meshtastic to MQTT Bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/sheep-gateway/meshtastic_mqtt_bridge.py
Restart=always
RestartSec=5
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 6. Write systemd service for ha-bridge
echo "[install] Creating systemd service: ha-bridge..."
cat | sudo tee /etc/systemd/system/ha-bridge.service >/dev/null <<'EOF'
[Unit]
Description=Home Assistant Sheep Counter Bridge
After=network-online.target mosquitto.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/sheep-gateway/ha_bridge.py
Restart=always
RestartSec=5
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 7. Reload systemd and enable services
echo "[install] Enabling systemd services..."
sudo systemctl daemon-reload
sudo systemctl enable meshtastic-bridge ha-bridge

# 8. Start services
echo "[install] Starting services..."
sudo systemctl start meshtastic-bridge || true
sudo systemctl start ha-bridge || true

# 9. Health check
echo "[install] Running health check..."
sleep 2
if systemctl is-active --quiet meshtastic-bridge; then
    echo "[install] ✓ meshtastic-bridge is active"
else
    echo "[install] ⚠ meshtastic-bridge failed to start. Check: journalctl -u meshtastic-bridge"
fi

if systemctl is-active --quiet ha-bridge; then
    echo "[install] ✓ ha-bridge is active"
else
    echo "[install] ⚠ ha-bridge failed to start. Check: journalctl -u ha-bridge"
fi

echo "[install] Done. Dashboard config: $INSTALL_DIR/ha_dashboard.yaml"
