"""
Author: Wasifa Hossain
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""
# Required Modules:
import socket
import threading
import sqlite3
import os
import platform
import datetime

# Print Python version and OS name:
print("Python Version:", platform.python_version())
print("Operating System:", os.name)

# common_ports dictionary:
# Stores common port numbers and their associated service names
common_ports = {
    20: "FTP Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    123: "NTP",
    137: "NetBIOS",
    138: "NetBIOS",
    139: "NetBIOS",
    143: "IMAP",
    161: "SNMP",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    514: "Syslog",
    631: "CUPS",
    993: "IMAPS",
    995: "POP3S",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}

# NetworkTool parent class:
class NetworkTool:
    def __init__(self, target):
        self.__target = target

# Q3: What is the benefit of using @property and @target.setter?

# Using @property and @target.setter lets the program control access to the target
# attribute while still allowing it to be used like a normal variable. This makes it
# easier to validate data, such as preventing an empty target string, and it supports
# encapsulation by protecting the private attribute from invalid assignments. 

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("Error: Target cannot be empty.")
        self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")




# Q1: How does PortScanner reuse code from NetworkTool?
# PortScanner inherits from NetworkTool, which gives it target-handling logic and
# attribute validation automatically. By calling super().__init__(target), it reuses the
# setup code instead of rewriting it. This reduces duplication and ensures consistent
# behavior across all networking tools.



# PortScanner child class inherits from NetworkTool
class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

    # -----------------------
    # Scan a single port
    # -----------------------
    def scan_port(self, port):

        # Q4: What would happen without try-except here?
        # Without try-except, any socket failure (timeout, unreachable host, refused
        # connection) would crash the whole scan. Exception handling ensures the program
        # continues scanning all ports even if some fail.
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))

            status = "Open" if result == 0 else "Closed"
            service_name = common_ports.get(port, "Unknown")

            with self.lock:
                self.scan_results.append((port, status, service_name))

        except socket.error as e:
            print(f"Error scanning port {port}: {e}")

            

        finally:
            sock.close()

    # -----------------------
    # Return only open ports
    # -----------------------
    def get_open_ports(self):
        return [r for r in self.scan_results if r[1] == "Open"]

    # Q2: Why do we use threading instead of scanning one port at a time?
    # Scanning sequentially is slow because each port may take up to a timeout period.
    # Threading allows parallel scanning, drastically reducing total scan time.
    
    # -----------------------
    # Scan a range of ports
    # -----------------------
    def scan_range(self, start_port, end_port):
        threads = []

        for port in range(start_port, end_port + 1):
            t = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()


# Function save_results(target, results) 
def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                port INTEGER,
                status TEXT,
                service TEXT,
                scan_date TEXT
            )
        """)

        for port, status, service in results:
            cur.execute("""
                INSERT INTO scans (target, port, status, service, scan_date)
                VALUES (?, ?, ?, ?, ?)
            """, (target, port, status, service, str(datetime.datetime.now())))

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print("Database error:", e)


# Function load_past_scans() 
def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM scans")
        rows = cur.fetchall()

        if not rows:
            print("No past scans found.")
        else:
            for r in rows:
                print(f"ID {r[0]} | Target: {r[1]} | Port {r[2]} | {r[3]} | {r[4]} | Date: {r[5]}")

        conn.close()

    except sqlite3.Error:
        print("No past scans found.")


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":

    try:
        target = input("Enter target IP (default 127.0.0.1): ").strip() or "127.0.0.1"

        start_port = int(input("Enter start port (1–1024): "))
        end_port = int(input("Enter end port (1–1024): "))

        if not (1 <= start_port <= 1024 and 1 <= end_port <= 1024):
            print("Port must be between 1 and 1024.")
            exit()

        if end_port < start_port:
            print("End port must be >= start port.")
            exit()

    except ValueError:
        print("Invalid input. Please enter a valid integer.")
        exit()

    scanner = PortScanner(target)
    print(f"Scanning {target} from port {start_port} to {end_port}...")

    scanner.scan_range(start_port, end_port)

    open_ports = scanner.get_open_ports()

    print("\nOpen Ports:")
    for port, status, svc in open_ports:
        print(f"Port {port}: {svc}")

    print(f"\nTotal open ports found: {len(open_ports)}")

    save_results(target, scanner.scan_results)

    show_history = input("\nWould you like to see past scan history? (yes/no): ").lower()
    if show_history == "yes":
        load_past_scans()


# Q5: New Feature Proposal
# A useful new feature would be hostname resolution and service banner grabbing for open ports.
# This would let the scanner display the host name and collect extra service details from some
# open ports, making the scan results more informative for troubleshooting and network analysis.
# Diagram: See diagram_101594842.png in the repository root
