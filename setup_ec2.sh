#!/bin/bash
set -e

echo "=== Axel Guard Pothole — t2.micro setup ==="

# 1. Add 2GB swap (critical for 1GB RAM + YOLO)
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo "✅ Swap created"
fi

# 2. System deps for OpenCV headless
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv libglib2.0-0 ffmpeg --no-install-recommends

# 3. Virtualenv
cd /home/ubuntu/pothole-app
python3 -m venv venv
source venv/bin/activate

# 4. Install Python deps
pip install --upgrade pip --quiet
pip install streamlit ultralytics opencv-python-headless boto3 python-dotenv --quiet

echo "✅ Dependencies installed"

# 5. Systemd service so it restarts on reboot
sudo tee /etc/systemd/system/pothole.service > /dev/null <<EOF
[Unit]
Description=Axel Guard Pothole Detection
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/pothole-app
EnvironmentFile=/home/ubuntu/pothole-app/.env
ExecStart=/home/ubuntu/pothole-app/venv/bin/streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.maxUploadSize=200 \
  --browser.gatherUsageStats=false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pothole
sudo systemctl start pothole

echo "✅ Service running at http://$(curl -s ifconfig.me):8501"
