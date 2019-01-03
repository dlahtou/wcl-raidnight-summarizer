import certifi
from io import BytesIO
import json
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def get_wcl_api_table(fightstring, mode="requests"):
    base_tables_url = "https://www.warcraftlogs.com:443/v1/report/tables/"
    url = ''.join([base_tables_url, fightstring])

    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])

    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=retries))

    r = s.get(url)
    return_json = r.json()
        
    return return_json

def get_wcl_api_fights(reportstring, mode="requests"):
    base_fights_url = "https://www.warcraftlogs.com:443/v1/report/fights/"
    url = ''.join([base_fights_url, reportstring])

    retries = Retry(total=10,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])

    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=retries))

    r = s.get(url)
    return_json = r.json()

    return return_json