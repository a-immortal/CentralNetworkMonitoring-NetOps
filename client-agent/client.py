import psutil
import json
import platform
import time
import requests

# 🚨 Corrected URL (Removed the double slash before submit-metrics)
ALB_URL = "http://ALB-netops-1118890655.ap-south-2.elb.amazonaws.com/submit-metrics"

def get_system_metrics():
    # Gather hardware data
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    # Simple network speed calculation
    net_io = psutil.net_io_counters()
    time.sleep(1)
    net_io_2 = psutil.net_io_counters()
    bytes_sent = net_io_2.bytes_sent - net_io.bytes_sent
    bytes_recv = net_io_2.bytes_recv - net_io.bytes_recv
    mbps = ((bytes_sent + bytes_recv) * 8) / 1_000_000

    return {
        "hostname": platform.node(),
        "os_type": platform.system(),
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "network": round(mbps, 2)
    }

def send_data():
    while True:
        try:
            payload = get_system_metrics()
            # Send HTTP POST to the ALB
            response = requests.post(ALB_URL, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"✅ Data sent successfully to ALB.")
            elif response.status_code == 403:
                print(f"🚫 Connection refused: You are blocked by the server.")
            else:
                print(f"⚠️ Server returned error: {response.status_code}")
                print(f"🔍 Error Details: {response.text}")
 
        except Exception as e:
            print(f"❌ Failed to connect to ALB: {e}")
            
        time.sleep(10) # Wait 10 seconds before next ping

if __name__ == "__main__":
    print("🚀 Starting HTTP Network Agent...")
    send_data()