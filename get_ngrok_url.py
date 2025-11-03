"""
Get ngrok public URL from the API
"""
import requests
import time
import sys

# Wait for ngrok to start
print("Waiting for ngrok to start...")
for i in range(10):
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('tunnels') and len(data['tunnels']) > 0:
                public_url = data['tunnels'][0]['public_url']
                print("\n" + "=" * 80)
                print("NGROK TUNNEL ACTIVE")
                print("=" * 80)
                print(f"Local URL: http://localhost:6789")
                print(f"Public URL: {public_url}")
                print("=" * 80)
                print("\nShare the public URL for external access!")
                sys.exit(0)
    except:
        pass
    time.sleep(1)
    print(f"  Attempt {i+1}/10...")

print("\nngrok not found. Please start ngrok manually:")
print("  ngrok http 6789")
