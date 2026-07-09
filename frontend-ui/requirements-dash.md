Here is the structured Markdown documentation for your frontend dashboard. You can save this as a standalone `README.md` in your frontend folder or append it directly below your `brain.py` notes to create a master deployment guide.

---

# 📊 Dashboard UI (`dashboard.py`) Deployment Notes

This document outlines the required dependencies, installation steps, and operational commands for deploying the Central Monitoring System's frontend interface on an Ubuntu EC2 instance.

## 📦 1. Dependencies (`requirements-dash.md`)
 This ensures your server has all the necessary visualization and database querying libraries.

# requirements-dash.md
streamlit==1.36.0
pandas==2.2.2
SQLAlchemy==2.0.31
plotly==5.22.0
mysql-connector-python==8.4.0
boto3==1.34.138

```

---

## 🛠️ 2. Environment Setup Commands

If you are deploying this on a separate EC2 instance (or a fresh server), run these commands to prepare the Linux environment.

**Update the package manager:**

```bash
sudo apt-get update && sudo apt-get upgrade -y

```

**Install Python 3, pip, and tmux:**

```bash
sudo apt-get install python3 python3-pip tmux -y

```

**Install the Python requirements:**

```bash
# If using the requirements.txt file:
pip3 install -r requirements.txt

# Or, if installing manually:
pip3 install streamlit pandas sqlalchemy plotly mysql-connector-python boto3

```

---

## 🚀 3. Execution Commands

Streamlit runs slightly differently than a standard Python script. We will still use `tmux` to keep the dashboard alive in the background.

**Start the Streamlit UI in the background:**

```bash
# 1. Create a new background session named 'web'
tmux new -s web

# 2. Run the Streamlit application (forces it to run as a module to prevent path errors)
python3 -m streamlit run dashboard.py

# 3. Detach from the session (leave it running)
# Press: Ctrl + B, then press D

```

**Re-attach to the session (to view live web logs):**

```bash
tmux attach -t web

```

---

## 🧹 4. Diagnostics & Cleanup Commands

If Port 8501 gets locked, or you need to restart the dashboard after pushing new code, use these commands to reset the environment.

**View all active Streamlit processes:**

```bash
ps aux | grep streamlit

```

**Forcefully kill the running Streamlit server:**

```bash
sudo pkill -f streamlit

```

**Clear Streamlit's internal cache (fixes stuck UI issues):**

```bash
rm -rf ~/.streamlit/cache

```

**Check if Port 8501 is currently listening:**

```bash
sudo netstat -tulpn | grep :8501

```