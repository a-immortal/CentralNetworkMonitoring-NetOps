server setup cmds

1. ubuntu@ip-10-0-xx-xxx:~$ sudo apt update sudo apt install python3-pip tmux -y



2. ubuntu@ip-10-0-xx-xxx:~$ pwd
   /home/ubuntu
   ubuntu@ip-10-0-xx-xxx:~$ mkdir NetOps
   
## install and mkdir for virtual env

3.  sudo apt update
   sudo apt install python3-venv -y

   python3 -m venv net_env

## activate venv
4. source NetOps_venv/bin/activate

## important download requied libraries (incase 5. line errors then run xx.line cmd)
5.pip install streamlit pandas plotly boto3 mysql-connector-python

xx.pip3 install streamlit pandas plotly boto3 mysql-connector-python SQLAlchemy --break-system-packages

7.pip install Flask mysql-connector-python boto3

8. pip install streamlit pandas plotly boto3 mysql-connector-python SQLAlchemy

   ubuntu@ip-10-0-xx-xxx:~/NetOps$ ls
   brain.py

   ubuntu@ip-10-0-xx-xxx:~/NetOps$ nano dashboard.py
   ubuntu@ip-10-0-xx-xxx:~/NetOps$ tmux new -s brain

9. ubuntu@ip-10-0-xx-xxx:~/NetOps$ tmux new -s brain
   duplicate session: brain

   ubuntu@ip-10-0-xx-xxx:~/NetOps$ tmux attach -t brain
   [detached (from session brain)]

   ubuntu@ip-10-0-xx-xxx:~/NetOps$ tmux new -s dashboard

    python3 -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false

    Step 1: The "ALB-Safe" Launch Command

We need to add two specific instructions to your Streamlit launch command. We need to disable WebSocket compression (which ALBs notoriously break) and explicitly tell Streamlit its new "name" is the ALB DNS.

### Kill your current UI process (Ctrl + C) and run this upgraded master command:
Bash

python3 -m streamlit run dashboard.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --server.enableWebsocketCompression false \
  --browser.serverAddress alb-netops-1118890xx55.ap-south-2.elb.amazonaws.com

(Make sure you replace the YOUR-ALB-DNS... part with your actual ALB DNS link, without the http:// at the beginning!)

### [detached (from session dashboard)], ctrl+b -d

   ubuntu@ip-10-0-xx-xxx:~/NetOps$ tmux attach -t brain