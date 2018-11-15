from selenium import webdriver
from bs4 import BeautifulSoup
import re
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
import pprint

def scrape_damage_parse_data(wcl_string,fight_id):
    ignore_specs = {'Monk-Mistweaver',
                    'Paladin-Holy',
                    'Druid-Restoration',
                    'Priest-Discipline',
                    'Priest-Holy',
                    'Shaman-Restoration'}

    options = Options()
    options.add_argument('--headless')
    options.set_preference("dom.max_script_run_time", 5)
    options.set_preference("http.response.timeout", 5)
    driver = webdriver.Firefox(firefox_options=options)

    driver.get('https://www.warcraftlogs.com/reports/'+wcl_string+'#fight='+str(fight_id)+'&type=damage-done')

    all_tablerows_selector = '//div[@id="table-container"]/div/table/tbody/tr'
    trs = driver.find_elements_by_xpath(all_tablerows_selector)
    tablerows = len(trs)
    print(tablerows)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "lxml")

    single_fight_parse_scrape_data = dict()
    for tablerow in soup.find_all(id=re.compile('main-table-row')):
        if not tablerow.find(class_='main-table-performance') or not tablerow.find(class_='main-table-link') or not tablerow.find(class_='main-table-ilvl-performance'):
            continue
        if tablerow.find(class_='main-table-link').a.string.strip() == "Hati":
            continue
        if tablerow.img['src']:
            if re.search(r'icons/.*\.', tablerow.img['src']).group()[6:-1] in ignore_specs:
                continue
        try:
            overall_performance = int(tablerow.find(class_='main-table-performance').a.text.strip())
        except:
            overall_performance = 0
        player_name = tablerow.find(class_='main-table-link').a.string.strip()
        try:
            ilvl_performance = int(tablerow.find(class_='main-table-ilvl-performance').a.text.strip())
        except:
            ilvl_performance = 0
        single_fight_parse_scrape_data[player_name] = ({'overall-performance': overall_performance,
                                                        'ilvl-performance': ilvl_performance})

    return single_fight_parse_scrape_data