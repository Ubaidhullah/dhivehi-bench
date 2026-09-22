import paramiko

host = "10.50.1.241"
port = 16011
username = "root"
password = "ccq" # Wait, earlier context says: password `ccq@742015`

def check_log():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.50.1.241", port=16011, username="root", password="ccq@742015", timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command("tail -n 25 /data_disk/chengcq/wula/dhivehi-bench/ocr.log")
        print("--- TAIL OF OCR.LOG ---")
        print(stdout.read().decode('utf-8'))
        
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep run_ocr_server.py")
        print("\n--- PROCESS STATUS ---")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    check_log()
