import requests

API = "https://saruna.mnu.edu.mv/server/api"

def get_collections():
    try:
        url = f"{API}/core/collections?size=100"
        response = requests.get(url, timeout=30)
        data = response.json()
        
        collections = data.get('_embedded', {}).get('collections', [])
        
        print("=== Saruna Collections ===")
        for c in collections:
            name = c.get('name', 'Unknown')
            uuid = c.get('uuid', 'Unknown')
            # Fetch item count using the discover endpoint
            # Actually, core/collections doesn't show count easily, but let's just list the names first
            print(f"- {name} (UUID: {uuid})")
            
        # Check if there are multiple pages
        total_pages = data.get('page', {}).get('totalPages', 1)
        if total_pages > 1:
            print(f"... and {total_pages - 1} more pages of collections.")
            
    except Exception as e:
        print(f"Failed to fetch collections: {e}")

if __name__ == "__main__":
    get_collections()
