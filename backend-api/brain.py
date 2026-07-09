from flask import Flask, request, jsonify
import mysql.connector
import boto3
import json
import traceback

app = Flask(__name__)

# --- CONFIGURATION ---
DB_HOST = "netops-database.cf0wwg2gwnvb.ap-south-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "adminsql2026"
SNS_ARN = "arn:aws:sns:ap-south-2:774667856687:Device-Health-Alerts"

# Initialize AWS safely
try:
    sns_client = boto3.client('sns', region_name='ap-south-2')
except Exception as e:
    print(f"⚠️ Warning: SNS Client failed to init. {e}")
    sns_client = None

def get_db_connection():
    return mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database="network_data")

# --- ROUTE 1: ALB Health Check ---
@app.route('/', methods=['GET'])
def health_check():
    """Bulletproof health check for the AWS ALB."""
    return "ALB is connected to Flask!", 200

# --- ROUTE 2: Data Intake ---
@app.route('/submit-metrics', methods=['POST', 'GET'])
def handle_client():
    """Receives data via HTTP POST from the ALB."""

    # 🚨 ULTIMATE DIAGNOSTIC LOGGER (Catches the 400 Error!)
    print("\n" + "="*50)
    print("📥 INCOMING REQUEST DETECTED AT /submit-metrics")
    print(f"Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Raw Body: {request.data}")
    print("="*50 + "\n")

    # If the ALB accidentally pings this route for a health check, smile and wave.
    if request.method == 'GET':
        return jsonify({"status": "Healthy Brain API Endpoint"}), 200

    # Extract the true client IP from the ALB headers
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]

    db = None
    cursor = None

    try:
        # Force parse JSON to bypass strict Load Balancer header rules
        payload = request.get_json(force=True, silent=True)

        if not payload:
            print(f"❌ 400 ERROR: Flask could not parse the payload from {client_ip}.")
            return jsonify({"error": "Invalid JSON or empty payload"}), 400

        print(f"✅ Successfully parsed data from {payload.get('hostname', 'Unknown')} ({client_ip})")

        # Connect to Database
        db = get_db_connection()
        cursor = db.cursor()

        # --- The Bouncer Check ---
        cursor.execute("SELECT ip_address FROM blocked_ips WHERE ip_address = %s", (client_ip,))
        if cursor.fetchone():
            print(f"🚫 Blocked connection attempt dropped from IP: {client_ip}")
            return jsonify({"status": "blocked"}), 403

         # --- Insert Data ---
        sql = """INSERT INTO device_metrics
                 (hostname, os_type, ip_address, cpu_usage, ram_usage, disk_usage, network_mbps)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""

        val = (payload.get('hostname'), payload.get('os_type'), client_ip,
               payload.get('cpu'), payload.get('ram'), payload.get('disk'), payload.get('network'))

        cursor.execute(sql, val)
        db.commit()

        # --- Alerts ---
        cpu_val = payload.get('cpu', 0)
        ram_val = payload.get('ram', 0)

        if sns_client and (cpu_val > 90 or ram_val > 90):
            msg = f"CRITICAL ALERT: {payload.get('hostname')} is overloaded!\nCPU: {cpu_val}%\nRAM: {ram_val}%"
            sns_client.publish(TopicArn=SNS_ARN, Message=msg, Subject=f"Network Alert - {payload.get('hostname')}")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"❌ SERVER ERROR: {e}")
        traceback.print_exc() 
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        # Safely clean up database connections even if the code crashes
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

if __name__ == "__main__":
    print("🧠 HTTP Brain API is running and listening on Port 5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True)