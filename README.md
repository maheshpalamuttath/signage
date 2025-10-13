# Digital Signage System with Flask & Firefox Kiosk

This repository contains a minimal Flask-based digital signage application. It serves media files and URLs in a slideshow and can be displayed in full-screen kiosk mode using Firefox.

## Prerequisites

- Ubuntu/Xubuntu system
- Python 3
- Git
- Firefox or Firefox ESR


## Installation

### 1. Update & Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git
````

### 2. Clone Repository

```bash
sudo git clone https://github.com/maheshpalamuttath/signage.git
cd signage
```

### 3. Set Permissions

```bash
sudo chown -R koha:koha /home/koha/signage
sudo chmod -R 775 /home/koha/signage/signage_media
```

### 4. Set Up Python Virtual Environment

```bash
sudo python3 -m venv myenv
source myenv/bin/activate
pip install flask gunicorn
```

### 5. Run Flask Server (Development Mode)

```bash
python3 server.py
```

It should display:

```
* Serving Flask app 'server'
* Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:8000
* Running on http://<your-ip>:8000

```
```
Admin: http://<your-ip>:8000/admin
Slideshow: http://<your-ip>:8000
```
---

## Running as a Systemd Service

### 1. Create Gunicorn Service

```bash
sudo vim /etc/systemd/system/signage.service
```

Add:

```
[Unit]
Description=Gunicorn service for Flask Signage App
After=network.target

[Service]
User=koha
Group=koha
WorkingDirectory=/home/koha/signage
Environment="PATH=/home/koha/signage/myenv/bin"
ExecStart=/home/koha/signage/myenv/bin/gunicorn -b 0.0.0.0:8000 server:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Enable & Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl start signage
sudo systemctl enable signage
sudo systemctl status signage
```

### 3. Allow Firewall Access

```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

### 4. Restart Gunicorn After Code Changes in Future

```bash
pkill gunicorn
/home/koha/signage/myenv/bin/gunicorn -b 0.0.0.0:8000 server:app -D
```

---

## Fullscreen Slideshow in Firefox

### 1. Launch in Kiosk Mode

```bash
firefox --kiosk http://<your-ip>:8000
```

For Firefox ESR:

```bash
firefox-esr --kiosk http://<your-ip>:8000
```

---

## Automatic Firefox Kiosk on Boot (Xubuntu) Client

### 1. Create Startup Script

```bash
vim /home/client-username/start-kiosk.sh
```
```
#!/bin/bash

URL="http://172.16.36.11:8000"
LOGFILE="/home/shec/firefox-kiosk.log"

echo "$(date) - Starting kiosk script" >> "$LOGFILE"

# Wait for X server
while ! xset q &>/dev/null; do
    echo "$(date) - Waiting for X server..." >> "$LOGFILE"
    sleep 2
done

# Extra wait for XFCE panels and window manager
sleep 8

# Wait until signage server is reachable
while ! curl -s --head --request GET "$URL" | grep "200 OK" > /dev/null; do
    echo "$(date) - Waiting for server at $URL..." >> "$LOGFILE"
    sleep 5
done

echo "$(date) - Server reachable. Launching Firefox..." >> "$LOGFILE"

# Launch Firefox in kiosk mode with private window (optional)
exec /usr/bin/firefox-esr --kiosk --private-window "$URL" >> "$LOGFILE" 2>&1

```
```
chmod +x /home/client-username/start-kiosk.sh
```

> The script should check if the signage server is up and then launch Firefox.

### 2. Create Systemd Service

```bash
sudo vim /etc/systemd/system/firefox-kiosk.service
```

Add:

```
[Unit]
Description=Firefox Kiosk for Digital Signage
After=graphical.target network-online.target
Wants=graphical.target network-online.target

[Service]
Type=simple
User=shec
Environment=DISPLAY=:0
ExecStart=/usr/bin/bash /home/shec/start-kiosk.sh
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target

```

### 3. Enable Service

```bash
sudo systemctl daemon-reload && sudo systemctl enable firefox-kiosk.service && sudo systemctl start firefox-kiosk.service

```

> On boot, systemd waits for the network, checks the signage server, and opens Firefox in kiosk mode automatically.

