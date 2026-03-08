import runpod
import os
from dotenv import load_dotenv

load_dotenv()
runpod.api_key = os.getenv("RUNPOD_API_KEY")

def get_active_pod():
    try:
        pods = runpod.get_pods()
        for pod in pods:
            if pod.get('desiredStatus') == 'RUNNING':
                runtime = pod.get('runtime')
                if not runtime:
                    continue
                
                ports = runtime.get('ports', [])
                ssh_ip = None
                ssh_port = None
                
                for p in ports:
                    # Look for the SSH port mapping
                    if p.get('privatePort') == 22:
                        ssh_port = p.get('publicPort')
                        ssh_ip = p.get('ip')
                        break
                
                if ssh_ip and ssh_port:
                    return {
                        "id": pod['id'],
                        "name": pod['name'],
                        "ip": ssh_ip,
                        "port": ssh_port
                    }
        return None
    except Exception as e:
        print(f"Error fetching pods: {e}")
        return None

if __name__ == "__main__":
    pod = get_active_pod()
    if pod:
        print(f"\n--- Active Pod Found ---")
        print(f"Name: {pod['name']}")
        print(f"ID:   {pod['id']}")
        print(f"IP:   {pod['ip']}")
        print(f"Port: {pod['port']}")
        print(f"\n--- Commands for Copy-Paste ---")
        print(f"SSH:  ssh root@{pod['ip']} -p {pod['port']}")
        print(f"SCP (Download): scp -P {pod['port']} root@{pod['ip']}:/path/to/remote/file ./local/path")
        print(f"SCP (Upload):   scp -P {pod['port']} ./local/path root@{pod['ip']}:/path/to/remote/dir")
    else:
        print("\n[!] No active running pods with SSH access found.")
