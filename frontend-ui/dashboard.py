import streamlit as st
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
import plotly.express as px
import boto3
import datetime
import time
import warnings
import secrets
import string

# Mute any residual Pandas warnings to keep the EC2 terminal clean
warnings.filterwarnings('ignore', message='.*SQLAlchemy connectable.*')

# ==========================================
# 1. PAGE CONFIG & UI FIXES
# ==========================================
st.set_page_config(page_title="Central Network Monitor", page_icon="🖥️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. EPHEMERAL AUTHENTICATION
# ==========================================
@st.cache_resource
def generate_server_password():
    """Generates a secure 12-character password ONCE per server boot."""
    alphabet = string.ascii_letters + string.digits
    pwd = ''.join(secrets.choice(alphabet) for i in range(12))
    
    # 🚨 Print to the EC2 terminal so the admin knows the password!
    print("\n" + "="*50)
    print("🔒 STREAMLIT SERVER STARTED")
    print(f"🔑 NEW EPHEMERAL PASSWORD: {pwd}")
    print("="*50 + "\n")
    return pwd

# Fetch the global server password
SERVER_PASSWORD = generate_server_password()

# Initialize session state for the specific user's browser tab
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# The Gatekeeper: Halt execution if not authenticated
if not st.session_state.authenticated:
    st.title("🔒 Admin Authentication Required")
    st.info("Enter the ephemeral server password to access the Central Network Monitor.")
    
    with st.form("login_form"):
        pwd_input = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd_input == SERVER_PASSWORD:
                st.session_state.authenticated = True
                st.rerun() # Refresh the page to load the dashboard
            else:
                st.error("❌ Incorrect password.")
    
    # Stop the script here so unauthorized users cannot trigger DB/AWS connections
    st.stop() 


# ==========================================
# 3. CONFIGURATION
# ==========================================
DB_HOST = "netops-database.cf0wwg2gwnvb.ap-south-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "adminsql2026"
S3_BUCKET = "netops-storage-docs"
SNS_ARN = "arn:aws:sns:ap-south-2:774667856687:Device-Health-Alerts"

# ==========================================
# 4. INITIALIZE ERROR LOGGER
# ==========================================
if 'error_logs' not in st.session_state:
    st.session_state.error_logs = []

def log_error(module_name, error_message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.error_logs.append(f"[{timestamp}] {module_name} Failure: {error_message}")

# ==========================================
# 5. CACHED CONNECTIONS (Massive Speedup)
# ==========================================
@st.cache_resource
def init_aws_clients():
    try:
        s3 = boto3.client('s3', region_name='ap-south-2')
        sns = boto3.client('sns', region_name='ap-south-2')
        return s3, sns, "🟢 AWS Cloud Services Connected"
    except Exception as e:
        log_error("AWS Init", str(e))
        return None, None, "🔴 AWS Cloud Services Disconnected"

s3_client, sns_client, aws_status = init_aws_clients()

# ENGINE 1: SQLAlchemy 
@st.cache_resource
def get_pandas_engine():
    return create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/network_data")

# ENGINE 2: Raw Connector 
def get_raw_connection():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database="network_data", connection_timeout=3
    )

# ==========================================
# 6. DATABASE HELPER FUNCTIONS
# ==========================================
def fetch_latest_data():
    try:
        engine = get_pandas_engine()
        query = """
            SELECT hostname, os_type, ip_address, cpu_usage, ram_usage, disk_usage, network_mbps, recorded_at
            FROM device_metrics
            WHERE (hostname, recorded_at) IN (
                SELECT hostname, MAX(recorded_at) FROM device_metrics GROUP BY hostname
            );
        """
        df = pd.read_sql(query, con=engine)

        if not df.empty:
            now = pd.Timestamp.utcnow().tz_localize(None)
            df['Status'] = df['recorded_at'].apply(
                lambda x: "🔴 Offline" if (now - x).total_seconds() > 60 else "🟢 Online"
            )
            df.loc[(df['cpu_usage'] > 90) | (df['ram_usage'] > 90), 'Status'] = "⚠️ Alert"
        return df
    except Exception as e:
        log_error("Database (Fetch Latest)", str(e))
        return pd.DataFrame()

def fetch_historical_data():
    try:
        engine = get_pandas_engine()
        query = "SELECT * FROM device_metrics WHERE recorded_at >= NOW() - INTERVAL 5 MINUTE ORDER BY recorded_at DESC"
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        log_error("Database (Fetch History)", str(e))
        return pd.DataFrame()

# ==========================================
# 7. TOP BAR & NAVIGATION
# ==========================================
t1, t2, t3 = st.columns([7, 2, 1])
with t1:
    st.title("🖥️ Central Network Monitor")
with t2:
    st.subheader(datetime.datetime.now().strftime("%Y-%m-%d | %H:%M:%S"))
with t3:
    st.write("")
    if st.button("🔴 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
st.markdown("---")

with st.sidebar:
    st.title("📂 Navigation")
    menu = st.radio("Go to", ["🏠 Dashboard", "📄 PDF Upload", "💻 Device Management", "📧 Send Alert Email", "⚙️ Settings / Logs"])
    st.markdown("---")
    auto_refresh = st.toggle("🔄 Auto-Refresh Dashboard", value=False)

# ==========================================
# 8. VIEWS
# ==========================================
if menu == "🏠 Dashboard":

    @st.fragment(run_every="5s" if auto_refresh else None)
    def render_live_dashboard():
        df_latest = fetch_latest_data()
        df_hist = fetch_historical_data()

        if df_latest.empty:
            st.info("Awaiting data from devices... (Check 'Settings / Logs' to verify database connection)")
        else:
            online = len(df_latest[df_latest['Status'] == '🟢 Online'])
            offline = len(df_latest[df_latest['Status'] == '🔴 Offline'])
            alerts = len(df_latest[df_latest['Status'] == '⚠️ Alert'])

            # --- SUMMARY CARDS ---
            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            m1.metric("🟢 Online", online)
            m2.metric("🔴 Offline", offline)
            m3.metric("⚠️ Alert", alerts)
            m4.metric("💻 CPU", f"{df_latest['cpu_usage'].mean():.1f}%")
            m5.metric("🧠 RAM", f"{df_latest['ram_usage'].mean():.1f}%")
            m6.metric("💾 Disk", f"{df_latest['disk_usage'].mean():.1f}%")
            m7.metric("🌐 Net", f"{df_latest['network_mbps'].mean():.1f} Mbps")
            st.markdown("---")

            # --- CONNECTED DEVICES GRID ---
            st.subheader("🖥️ Connected Devices Grid")
            st.dataframe(df_latest, use_container_width=True, hide_index=True)
            st.markdown("---")

            # --- LIVE CHARTS ---
            if not df_hist.empty:
                st.subheader("📈 Live Telemetry Charts (Last 5 Minutes)")
                c1, c2 = st.columns(2)
                c3, c4 = st.columns(2)
           
                with c1:
                    st.plotly_chart(px.line(df_hist, x='recorded_at', y='cpu_usage', color='hostname', title='CPU Usage (%)'), use_container_width=True)
                with c2:
                    st.plotly_chart(px.line(df_hist, x='recorded_at', y='ram_usage', color='hostname', title='RAM Usage (%)'), use_container_width=True)
                with c3:
                    st.plotly_chart(px.area(df_hist, x='recorded_at', y='network_mbps', color='hostname', title='Network (Mbps)'), use_container_width=True)
                with c4:
                    st.plotly_chart(px.bar(df_hist, x='recorded_at', y='disk_usage', color='hostname', title='Disk Usage (%)'), use_container_width=True)

    render_live_dashboard()

elif menu == "📄 PDF Upload":
    st.header("📄 Upload Device Data to S3")
    uploaded_file = st.file_uploader("Drop PDF here (Max 1MB)", type=['pdf'])

    if uploaded_file and uploaded_file.size < 1048576:
        if st.button("⬆️ Upload to Cloud"):
            if s3_client:
                try:
                    s3_client.upload_fileobj(uploaded_file, S3_BUCKET, uploaded_file.name)
                    st.success(f"✅ Uploaded '{uploaded_file.name}'!")
                except Exception as e:
                    log_error("S3 Upload", str(e))
                    st.info("Upload failed. Check logs.")
            else:
                st.info("Cannot upload: AWS is not connected.")

elif menu == "💻 Device Management":
    st.header("💻 Manage Registered Devices")

    df_latest = fetch_latest_data()
    if not df_latest.empty:
        search = st.text_input("🔍 Search Active Devices...")
        if search:
            df_latest = df_latest[df_latest.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]
        st.dataframe(df_latest[['hostname', 'ip_address', 'Status']], use_container_width=True)

        st.markdown("### 🗑️ Purge Device History")
        del_target = st.selectbox("Select Device to Purge:", df_latest['hostname'].tolist())
        if st.button("Delete Database History", type="primary"):
            try:
                conn = get_raw_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM device_metrics WHERE hostname = %s", (del_target,))
                conn.commit()
                conn.close()
                st.success(f"{del_target} history purged.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                log_error("Database (Delete)", str(e))
                st.info("Failed to delete device. Check logs.")

        st.markdown("---")

        st.markdown("### 🚫 Block Device Traffic (Firewall)")
        st.write("Blocking an IP forces the server to drop all future data packets from that device.")

        block_ip = st.selectbox("Select IP Address to Block:", df_latest['ip_address'].unique().tolist())
        if st.button("🛑 Block This IP Address"):
            try:
                conn = get_raw_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT IGNORE INTO blocked_ips (ip_address) VALUES (%s)", (block_ip,))
                conn.commit()
                conn.close()
                st.success(f"IP {block_ip} is now blocked at the server level.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                log_error("Database (Block IP)", str(e))
                st.info("Failed to block IP. Check logs.")

    try:
        engine = get_pandas_engine()
        blocked_df = pd.read_sql("SELECT ip_address, blocked_at FROM blocked_ips", con=engine)

        if not blocked_df.empty:
            st.markdown("### 🛡️ Currently Blocked IPs")
            st.dataframe(blocked_df, use_container_width=True, hide_index=True)

            unblock_ip = st.selectbox("Select IP to Unblock:", blocked_df['ip_address'].tolist())
            if st.button("✅ Remove Block"):
                conn = get_raw_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM blocked_ips WHERE ip_address = %s", (unblock_ip,))
                conn.commit()
                conn.close()
                st.success(f"IP {unblock_ip} has been unblocked.")
                time.sleep(1)
                st.rerun()
    except Exception as e:
        log_error("Database (Fetch Blocked)", str(e))

elif menu == "📧 Send Alert Email":
    st.header("📧 Manual Email Alerts")
    with st.form("alert"):
        subject = st.text_input("Subject")
        message = st.text_area("Message")
        if st.form_submit_button("📤 Broadcast"):
            if sns_client:
                try:
                    sns_client.publish(TopicArn=SNS_ARN, Message=message, Subject=subject)
                    st.success("✅ Alert sent via AWS SNS!")
                except Exception as e:
                    log_error("SNS Publish", str(e))
                    st.info("Failed to send email. Check logs.")
            else:
                st.info("Cannot send: AWS SNS not connected.")

elif menu == "⚙️ Settings / Logs":
    st.header("⚙️ Admin Settings & Error Logs")
    st.subheader("Cloud Connection Status")
    st.write(aws_status)
    st.markdown("---")
    st.subheader("System Diagnostic Logs")

    if len(st.session_state.error_logs) == 0:
        st.success("No backend errors detected. System is running cleanly.")
    else:
        st.warning(f"{len(st.session_state.error_logs)} errors recorded during this session:")
        for error in reversed(st.session_state.error_logs):
            st.code(error, language="bash")
        if st.button("🗑️ Clear Logs"):
            st.session_state.error_logs = []
            st.rerun()