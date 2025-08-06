import requests
import json

def test_endpoints():
    base_url = "http://localhost:5005"
    
    print("Testing CereBro Backend Endpoints...")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ Health endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    # Test metrics endpoint
    try:
        response = requests.get(f"{base_url}/api/metrics")
        print(f"✅ Metrics endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Focus Score: {data.get('focus_score', 'N/A')}%")
            print(f"   Burnout Signals: {len(data.get('burnout_signals', []))}")
            print(f"   Recent Usage: {len(data.get('recent_usage', []))} entries")
    except Exception as e:
        print(f"❌ Metrics endpoint failed: {e}")
    
    # Test preferences endpoint
    try:
        response = requests.get(f"{base_url}/api/preferences")
        print(f"✅ Preferences endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Track Apps: {data.get('track_apps', 'N/A')}")
            print(f"   Track Idle: {data.get('track_idle', 'N/A')}")
    except Exception as e:
        print(f"❌ Preferences endpoint failed: {e}")
    
    # Test analytics endpoint
    try:
        response = requests.get(f"{base_url}/api/analytics")
        print(f"✅ Analytics endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total Records: {data.get('total_records', 'N/A')}")
            print(f"   Idle Records: {data.get('idle_records', 'N/A')}")
    except Exception as e:
        print(f"❌ Analytics endpoint failed: {e}")
    
    print("=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_endpoints() 