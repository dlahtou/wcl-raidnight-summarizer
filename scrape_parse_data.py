from selenium import webdriver
from bs4 import BeautifulSoup
import re
from selenium.webdriver.firefox.options import Options

def scrape_damage_parse_data(wcl_string,fight_id):
    ignore_specs = {'Monk-Mistweaver',
                    'Paladin-Holy',
                    'Druid-Restoration',
                    'Priest-Discipline',
                    'Priest-Holy',
                    'Shaman-Restoration'}

    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox(firefox_options=options)

    driver.get('https://www.warcraftlogs.com/reports/'+wcl_string+'#fight='+str(fight_id)+'&type=damage-done')
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "lxml")

    single_fight_parse_scrape_data = []
    for tablerow in soup.find_all(id=re.compile('main-table-row')):
        if not tablerow.find(class_='main-table-performance') or not tablerow.find(class_='main-table-link') or not tablerow.find(class_='main-table-ilvl-performance'):
            continue
        if tablerow.img['src']:
            if re.findall(r'^/(.+/)*(.+)\.',tablerow.img['src'])[-1][-1] in ignore_specs:
                continue
        try:
            overall_performance = int(tablerow.find(class_='main-table-performance').a.string.strip().replace('*',''))
        except:
            overall_performance = 0
        player_name = tablerow.find(class_='main-table-link').a.string.strip()
        try:
            ilvl_performance = int(tablerow.find(class_='main-table-ilvl-performance').a.string.strip().replace('*',''))
        except:
            ilvl_performance = 0
        single_fight_parse_scrape_data.append({'name': player_name,
                        'overall-performance': overall_performance,
                        'ilvl-performance': ilvl_performance})

    return single_fight_parse_scrape_data