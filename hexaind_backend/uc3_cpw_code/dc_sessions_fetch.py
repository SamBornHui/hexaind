import requests
import os
import pandas as pd
 
def hexaind_custom_widget_function(page_limit: int) -> pd.DataFrame:
    url = "http://micron_apis_proxy:80/micron/data_catalog/get_all_sessions"
    params = {
        "projectId": os.getenv("CURRENT_PROJECT_ID"),
        "page_limit": 100,
        "page_number": 1
    }
    print(f"calling with these params {params}")
    response = requests.get(url, params=params)
    print("response fetched")
    if response.status_code == 200:
        data = response.json()
        sessions = data.get("datacatalog_sessions", [])
        print(f"found {len(sessions)} sessions")
        result = {}
        for session in sessions:
            name = session.get("name", "")
            result[name] = session.get("_id", None)
        print(result)
        if result:
            df = pd.DataFrame(result, index=["_id"])
            return df
        else:
            print("No sessions found.")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()