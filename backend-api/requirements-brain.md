
---

# 🧠 Brain API (`brain.py`) Deployment Notes

This document contains the required dependencies, installation steps, and operational commands for deploying the Central Monitoring System's backend API on an Ubuntu EC2 instance.

## 📦 1. Dependencies (`requirements-brain.md`)

```text
# requirements-brain.md
Flask==3.0.3
mysql-connector-python==8.4.0
boto3==1.34.138

```

*(Note: Pinning exact version numbers is a cloud engineering best practice to prevent future updates from breaking your code, though running a standard `pip3 install` without versions will also work).*

---

## 🛠️ 2. Environment Setup Commands

If you are provisioning a brand new Ubuntu EC2 instance, run these commands sequentially to prepare the server for the Python environment.

**Update the package manager:**

```bash
sudo apt-get update && sudo apt-get upgrade -y

```

**Install Python 3, pip, and tmux (for background processing):**

```bash
sudo apt-get install python3 python3-pip tmux -y

```

**Install the Python requirements:**

```bash
# If using the requirements.txt file:
pip3 install -r requirements.txt

# Or, if installing manually:
pip3 install Flask mysql-connector-python boto3

```

---

## 🚀 3. Execution Commands

Because this is a server, you need the API to stay alive even after you close your SSH terminal. We use `tmux` (Terminal Multiplexer) to run it in a detached background session.

**Start the Flask API in the background:**

```bash
# 1. Create a new background session named 'api'
tmux new -s api

# 2. Run the script
python3 brain.py

# 3. Detach from the session (leave it running)
# Press: Ctrl + B, then press D

```

**Re-attach to the session (to view live logs):**

```bash
tmux attach -t api

```

---

## 🧹 4. Diagnostics & Cleanup Commands

If Port 5000 gets locked or you need to forcefully restart the backend, use these commands to wipe the slate clean.

**View all active Python processes:**

```bash
ps aux | grep python3

```

**Forcefully kill all running Python scripts:**

```bash
sudo pkill -f python3

```

**Kill all active tmux sessions (shuts down the background API):**

```bash
tmux kill-server

```

**Check if Port 5000 is currently listening:**

```bash
sudo netstat -tulpn | grep :5000

```