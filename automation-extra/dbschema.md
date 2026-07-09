Here is the complete and final MySQL database schema for your Central Monitoring System (NetOps), incorporating all the architectural upgrades we built for High Availability, Idempotency, and Stateless Authentication.

### 1. The Core Telemetry Table (`device_metrics`)

This table handles the massive influx of hardware data from your edge agents. It includes the `UNIQUE KEY` constraint we added to prevent duplicate entries if the Load Balancer routes the same payload twice.

```sql
CREATE TABLE IF NOT EXISTS device_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(100) NOT NULL,
    os_type VARCHAR(50),
    ip_address VARCHAR(45),
    cpu_usage FLOAT,
    ram_usage FLOAT,
    disk_usage FLOAT,
    network_mbps FLOAT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_telemetry (hostname, recorded_at)
);

```

### 2. The Firewall Table (`blocked_ips`)

This is the backend for your "Bouncer" mechanism. The Brain API cross-references incoming traffic against this table to instantly drop malicious or unwanted packets.

```sql
CREATE TABLE IF NOT EXISTS blocked_ips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(45) UNIQUE NOT NULL,
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

### below these are future plans, not implemented till july 2026

### 3. The Authentication Table (`admin_users`)

This table securely stores the credentials for IT administrators to log into the Streamlit dashboard, utilizing `werkzeug.security` password hashes.

```sql
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

### 4. The High Availability Cluster Table (`system_config`)

This single-row table acts as the "shared whiteboard" for your distributed EC2 servers. It manages the heartbeat cluster state and the shared ephemeral password that grants access to the dashboard.

```sql
CREATE TABLE IF NOT EXISTS system_config (
    id INT PRIMARY KEY DEFAULT 1,
    shared_password VARCHAR(50),
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```