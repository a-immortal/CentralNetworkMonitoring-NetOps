import mysql.connector
import os
import json

def lambda_handler(event, context):
    # Retrieve credentials securely from Lambda Environment Variables
    DB_HOST = os.environ.get("DB_HOST", "netops-database.cf0wwg2gwnvb.ap-south-2.rds.amazonaws.com")
    DB_USER = os.environ.get("DB_USER", "admin")
    DB_PASS = os.environ.get("DB_PASS", "adminsql2026")
    DB_NAME = os.environ.get("DB_NAME", "network_data")

    db = None
    cursor = None

    try:
        print("🔄 Initiating RDS Database Cleanup...")
        
        # Connect to the RDS Database
        db = mysql.connector.connect(
            host=DB_HOST, 
            user=DB_USER, 
            password=DB_PASS, 
            database=DB_NAME
        )
        cursor = db.cursor()
        
        # Execute the Truncate Commands
        print("🗑️ Emptying device_metrics table...")
        cursor.execute("TRUNCATE TABLE device_metrics;")
        
        print("🗑️ Emptying blocked_ips table...")
        cursor.execute("TRUNCATE TABLE blocked_ips;")
        
        db.commit()
        print("✅ Database successfully purged.")
        
        return {
            "statusCode": 200, 
            "body": json.dumps("Automated cleanup completed successfully.")
        }
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return {
            "statusCode": 500, 
            "body": json.dumps(f"Internal Server Error: {str(e)}")
        }
        
    finally:
        # Ensure connections are closed even if the script fails
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()
            print("🔒 Database connection closed.")