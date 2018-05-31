## this program takes timestamps and a data type for a single fight within a wcl upload and saves the
## requested data type for the fight to a file

import pycurl
import certifi
import os.path

base_fights_url = "https://www.warcraftlogs.com:443/v1/report/tables/"
API_key = "bb7a652ddabff076285430d88b002dc8"

valid_data_types = {'damage-done',
                    'damage-taken',
                    'healing',
                    'casts',
                    'summons',
                    'buffs',
                    'debuffs',
                    'deaths',
                    'survivability',
                    'resources',
                    'resources-gains'}

def gettables(working_log_code,data_type,start_time,end_time,output_filename,output_directory=None):
    if data_type not in valid_data_types:
        quit(data_type+" is not a valid data type!")

    if output_directory:
        output_filename = os.path.join(output_directory,output_filename)
     
    with open(output_filename,'wb') as open_file:
        c = pycurl.Curl()
        c.setopt(pycurl.CAINFO, certifi.where())
        c.setopt(c.URL,''.join([base_fights_url,data_type,"/",working_log_code,"?start=",str(start_time),"&end=",str(end_time),"&api_key=",API_key]))
        c.setopt(c.WRITEDATA,open_file)
        c.setopt(c.VERBOSE, True)
        c.perform()
        c.close()

if __name__ == '__main__':
    gettables("mzdah3G7qn2XtjvH",'damage-done',393982,813862,'first_damage_log.json')