import pycurl
import certifi
from io import BytesIO
import json

def get_wcl_api_table(fightstring):
    base_tables_url = "https://www.warcraftlogs.com:443/v1/report/tables/"

    api_return_buffer =  BytesIO()
    api_curl = pycurl.Curl()

    api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
    api_curl.setopt(pycurl.CAINFO, certifi.where())
    api_curl.setopt(api_curl.URL,''.join([base_tables_url, fightstring]))

    api_curl.perform()
    return_json = api_return_buffer.getvalue().decode('utf-8')
    return json.loads(return_json)

def get_wcl_api_fights(reportstring):
    base_fights_url = "https://www.warcraftlogs.com:443/v1/report/fights/"

    api_return_buffer = BytesIO()
    api_curl = pycurl.Curl()

    api_curl.setopt(api_curl.URL,''.join([base_fights_url, reportstring]))
    api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
    api_curl.setopt(pycurl.CAINFO, certifi.where())

    api_curl.perform()
    return_json = api_return_buffer.getvalue().decode('utf-8')
    return json.loads(return_json)