
---

# 🖥️ Central Network Monitor: Project Build & Deployment Runbook

This document serves as the official architectural record, deployment guide, and troubleshooting ledger for the Central Network Monitor project. It details the complete step-by-step setup of the AWS infrastructure, the deployment of the Python/Streamlit software stack, and a comprehensive log of technical errors encountered and resolved.

---

## I. Technical Requirements & Architecture

### Hardware Requirements

* **Central Server (EC2):** Minimum **2 GB of RAM** is strictly required (e.g., AWS `t2.small` or `t3.small`). Running this stack on a 1 GB instance (`t2.micro`) will result in Linux Out of Memory (OOM) silent crashes when loading Pandas and Plotly libraries.
* **Client Devices:** Windows, macOS, or Linux machines capable of running Python 3.

### Software Stack

* **Backend Engine:** Python 3 (Sockets, Multi-threading, JSON).
* **Frontend UI:** Streamlit, Pandas, Plotly Express.
* **Database Interface:** `mysql-connector-python` & `SQLAlchemy`.
* **Cloud SDK:** `boto3` (AWS SDK for Python).
* **Client Agent:** Python `psutil` (for hardware metrics extraction).

---

## II. Step-by-Step Infrastructure Setup

### Phase 1: AWS Foundation, Networking & Load Balancing

1. **Virtual Private Cloud (VPC):**
* Deployed a target VPC (`NetworkMonitor-vpc` - `172.16.0.0/16`) spanning 3 Availability Zones for High Availability (HA).
* Configured **3 Public Subnets** (for the ALB and Bastion Host) routed to an Internet Gateway (IGW).
* Configured **3 Private Subnets** (for the Core EC2 servers and RDS Database) routed to a NAT Gateway to keep compute resources off the public internet.


2. **Chained Security Groups (Firewalls):**
* **ALB-SG (Public):** Configured inbound rules allowing HTTP (Port 80) and HTTPS (Port 443) from `0.0.0.0/0`. Outbound traffic is restricted strictly to the `EC2-Server-SG`.
* **EC2-Server-SG (Private):** Configured inbound rules allowing Custom TCP (Port 5000 for Brain) and Custom TCP (Port 8501 for Streamlit) *strictly* from the `ALB-SG`. SSH (Port 22) is allowed only from the Bastion Host/Systems Manager.
* **RDS-DB-SG (Private):** Configured inbound rules to allow MySQL traffic (Port 3306) specifically originating from the `EC2-Server-SG`.


3. **Application Load Balancer (ALB) & Routing:**
* Provisioned an internet-facing ALB spanning the 3 Public Subnets.
* **Target Group A (Backend):** Points to the EC2 instances on Port 5000.
* **Target Group B (Frontend):** Points to the EC2 instances on Port 8501.
* **Layer 7 Listener Rules:** Configured the ALB to route URL paths matching `/submit-metrics*` directly to Target Group A. All other default traffic routes to Target Group B.


4. **Simple Notification Service (SNS):**
* Created a Standard Topic (`Device-Health-Alerts`) in the `ap-south-2` (Hyderabad) region.
* Subscribed IT admin email addresses and confirmed the subscriptions.


5. **Simple Storage Service (S3):**
* Provisioned a private S3 bucket (`net-monitor-pdfs-storage`) for secure log and report storage.



### Phase 2: Database Setup & Parameter Configuration

1. **RDS MySQL Provisioning:**
* Launched a Multi-AZ MySQL RDS instance (`network-monitor-db`) placed securely within the private subnets and protected by the `RDS-DB-SG` security group.


2. **Custom DB Parameter Group (Crucial Step):**
* *Requirement:* The system uses an automated data cleanup event. AWS RDS blocks the `SUPER` privilege required to run `SET GLOBAL event_scheduler = ON;` directly via SQL code.
* *Action:* Navigated to RDS Parameter Groups -> Created a custom group -> Edited the `event_scheduler` parameter from `OFF` to `ON`.
* Applied this custom Parameter Group to the RDS instance and rebooted.



### Phase 3: EC2 Compute & IAM Setup

1. **Identity and Access Management (IAM):**
* Created an IAM Role (`EC2-NetworkMonitor-Role`) mapped to the EC2 service.
* Attached `AmazonS3FullAccess`, `AmazonSNSFullAccess`, and `AmazonSSMManagedInstanceCore` policies to allow the server to upload files, send emails, and be managed securely without SSH keys.


2. **EC2 Launch (Auto Scaling Group ready):**
* Launched an Ubuntu AMI using the `t2.small` (2GB RAM) instance type into the Private Subnet.
* Attached the `EC2-Server-SG` security group and the `EC2-NetworkMonitor-Role` IAM profile.


3. **Environment Preparation:**
* Connected via AWS Systems Manager (SSM) and installed system dependencies: `sudo apt update`, `sudo apt install python3-pip tmux -y`.
* Installed Python libraries: `pip3 install Flask streamlit pandas plotly boto3 mysql-connector-python SQLAlchemy --break-system-packages`.



### Phase 4: Application Deployment

1. **The Backend (`brain.py`):**
* Deployed the Flask HTTP server script responsible for responding to ALB health checks, receiving client telemetry, and validating Bouncer blocklists via RDS.


2. **The Frontend (`dashboard.py`):**
* Deployed the Streamlit script serving as the interactive UI, featuring live Plotly charts, S3 uploads, manual SNS broadcasts, device purging, and an IP blocklist manager.


3. **Background Execution (`tmux`):**
* Created persistent virtual terminals to run the services 24/7.
* Brain execution: `tmux new -s brain` -> `python3 brain.py`
* UI execution: `tmux new -s ui` -> `python3 -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false`



---

## III. Troubleshooting & Error Correction Ledger

I completely understand! Sometimes raw Markdown tables can look like a wall of text if the sentences inside them are too long, making them terrible to read or copy.

To fix this and make it look like a clean, professional MS Word grid, I have ruthlessly edited the text down to be **concise and punchy**.

*Pro-Tip for MS Word: If you highlight this rendered table from your browser, copy it (`Ctrl+C`), and paste it into Word (`Ctrl+V`), Word will automatically convert it into a perfectly formatted, editable grid table!*

### III. Troubleshooting & Error Correction Ledger

| Component | Symptom / Error Log | Root Cause | Implemented Solution |
| --- | --- | --- | --- |
| **AWS ALB** | HTTP 502 Bad Gateway. | Health check pinged `/` but API expected `/submit-metrics`. | Added `@app.route('/')` returning 200 OK for health checks. |

| **AWS ALB** | HTTP 400 Bad Request. | ALB modified/stripped strict JSON HTTP headers. | Forced JSON parsing via `request.get_json(force=True, silent=True)`. |

| **AWS RDS** | `Access denied; you need SUPER privileges` | AWS restricts `SET GLOBAL event_scheduler` via SQL code. | Enabled event scheduler via custom AWS RDS Parameter Group. |

| **Streamlit UI** | Blank white page on Port 8501. | Default config blocks cross-origin WebSocket traffic. | Added flags: `--server.enableCORS false --server.enableXsrfProtection false`. |

| **Linux OS** | `streamlit: command not found` | Installed in hidden `~/.local/bin` missing from global PATH. | Invoked strictly as Python module: `python3 -m streamlit run`. |

| **EC2 RAM** | Blank black screen; terminal drops process. | Out of Memory (OOM) crash on 1 GB `t2.micro` instance. | Upgraded infrastructure to `t2.small` (2 GB RAM). |

| **Streamlit UI** | `SyntaxError: Failed to execute 'appendChild'` | Corrupt invisible characters in custom CSS injection. | Removed `st.markdown('<style>...')` CSS injection entirely. |

| **AWS SNS** | "Alert sent" but no emails arrive. | `boto3` client defaulted to `us-east-1` instead of `ap-south-2`. | Updated `region_name` parameter to strictly match `ap-south-2`. |

| **Streamlit UI** | Persistent red AWS disconnect text on UI. | Sidebar `st.write()` forced error display on every refresh. | Created silent `st.session_state` Error Logger. |

| **AWS S3** | `botocore.exceptions.ClientError: AccessDenied` | Missing `AmazonS3FullAccess` policy on EC2 IAM Role. | Attached correct IAM Role via EC2 Security Actions menu. |

| **MySQL Auth** | `NotSupportedError: caching_sha2_password` | Outdated local Python MySQL connector. | Ran `pip3 install --upgrade mysql-connector-python`. |

| **EC2 OS** | Dashboard goes offline after server reboot. | `tmux` sessions are destroyed upon physical EC2 restart. | Documented manual restart. *(Future fix: Linux `systemd` services)*. |