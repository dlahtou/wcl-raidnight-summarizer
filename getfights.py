## downloads and writes a json file containing fight metadata
## includes: fight times,boss names,players involved, kill status

import pycurl
import certifi
import os.path
import datetime
import gettables
import json

base_fights_url = "https://www.warcraftlogs.com:443/v1/report/fights/"
API_key = "bb7a652ddabff076285430d88b002dc8"

def getfights(working_log_code,output_filename,output_directory=None):
    if output_directory:
        output_filename = os.path.join(output_directory,output_filename)

    with open(output_filename,'wb') as open_file:
        c = pycurl.Curl()
        c.setopt(pycurl.CAINFO, certifi.where())
        c.setopt(c.URL,''.join([base_fights_url,working_log_code,"?api_key=",API_key]))
        c.setopt(c.WRITEDATA,open_file)
        c.setopt(c.VERBOSE, True)
        c.perform()
        c.close()

def getalltables(working_log_code,fights_file,save_directory):
    ## TODO: grab zone data and date for save_directory name
    with open(fights_file,'r') as open_file:
        fights_data = json.load(open_file)

    for fight in fights_data['fights']:
        if not fight['kill']:
            continue
        save_name =  fight['name']+'.json'
        gettables.gettables(working_log_code,'damage-done',fight['start_time'],fight['end_time'],save_name,save_directory)


if __name__ == '__main__':
    getfights("mzdah3G7qn2XtjvH", 'first_log.json')
    getalltables("mzdah3G7qn2XtjvH",'first_fights_log.json','First-fights')