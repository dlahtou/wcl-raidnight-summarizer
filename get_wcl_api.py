import pycurl
import certifi
from io import BytesIO
import json
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def get_wcl_api_table(fightstring, mode="requests"):
    base_tables_url = "https://www.warcraftlogs.com:443/v1/report/tables/"
    url = ''.join([base_tables_url, fightstring])

    if mode == "requests":
        s = requests.Session()

        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])

        s.mount('http://', HTTPAdapter(max_retries=retries))

        r =s.get(url)

        return_json = r.json()
    else:
        api_return_buffer =  BytesIO()
        api_curl = pycurl.Curl()

        api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
        api_curl.setopt(pycurl.CAINFO, certifi.where())
        api_curl.setopt(api_curl.URL, url)
        api_curl.setopt(api_curl.TIMEOUT, 30)

        api_curl.perform()
        api_return_string = api_return_buffer.getvalue().decode('utf-8')
        return_json = json.loads(api_return_string)
        
    return return_json

def get_wcl_api_fights(reportstring, mode="requests"):
    base_fights_url = "https://www.warcraftlogs.com:443/v1/report/fights/"
    url = ''.join([base_fights_url, reportstring])

    if mode == "requests":
        s = requests.Session()

        retries = Retry(total=10,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])

        s.mount('http://', HTTPAdapter(max_retries=retries))

        r = s.get(url)

        return_json = r.json()
    else:
        api_return_buffer = BytesIO()
        api_curl = pycurl.Curl()

        api_curl.setopt(api_curl.TIMEOUT, 30)
        api_curl.setopt(api_curl.URL, url)
        api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
        api_curl.setopt(pycurl.CAINFO, certifi.where())

        api_curl.perform()
        api_return_string = api_return_buffer.getvalue().decode('utf-8')
        return_json = json.loads(api_return_string)

    return return_json