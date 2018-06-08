from selenium import webdriver
from bs4 import BeautifulSoup
import re
from selenium.webdriver.firefox.options import Options

def scrape_damage_parse_data(wcl_string,fight_id):
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox()

    driver.get('https://www.warcraftlogs.com/reports/'+wcl_string+'#fight='+str(fight_id)+'&type=damage-done')
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "lxml")

    parse_data = []
    for tablerow in soup.find_all(id=re.compile('main-table-row')):
        if not tablerow.find(class_='main-table-performance') or not tablerow.find(class_='main-table-link') or not tablerow.find(class_='main-table-ilvl-performance'):
            continue
        overall_performance = tablerow.find(class_='main-table-performance').a.string.strip()
        player_name = tablerow.find(class_='main-table-link').a.string.strip()
        ilvl_performance = tablerow.find(class_='main-table-ilvl-performance').a.string.strip()
        parse_data.append({'name': player_name,
                        'overall-performance': overall_performance,
                        'ilvl-performance': ilvl_performance})

    return parse_data