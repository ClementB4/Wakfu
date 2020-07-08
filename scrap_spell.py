from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import re

client = MongoClient('mongodb://localhost:27017')
db=client.wakfu

driver = webdriver.Chrome(ChromeDriverManager().install())
driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 60*5)


classes = [
    '1-feca', '2-osamodas', '3-enutrof', 
    '4-sram', '5-xelor', '6-ecaflip', 
    '7-eniripsa', '8-iop', '9-cra', 
    '10-sadida', '11-sacrieur', '12-pandawa',
    '13-roublard', '14-zobal', '15-ouginak',
    '16-steamer', '18-eliotrope', '19-huppermage'
]
elements = ['fire', 'water', 'earth', 'wind']
costs = ['pa', 'pm', 'wakfu']

def to_add_row(driver, classe, costs, hide=True):
    to_add = {
        'classe':classe.split('-')[1],
        'spell':'',
        'pa':0,
        'pm':0,
        'wakfu':0,
        'po':'',
        'text':'',
        'spell_type':'',
        'sprite':''
    }
    if hide:    
        spell = driver.find_element_by_xpath('//div[@class="ak-level-selector-target ak-level-1 hide"]')
    else:
        i = 1
        found = False
        while found == False and i < 3:
            try:
                spell = driver.find_element_by_xpath('//div[@class="ak-level-selector-target ak-level-%s show"]'%i)
                found = True
            except Exception as e:
                print(e)
                i += 1
                found = False
    title = spell.find_element_by_xpath('//h2[@class="ak-spell-name"]')
    text = spell.find_element_by_xpath('//span[@class="ak-spell-description"]')
    text_description = text.get_attribute('innerHTML')
    to_add['text'] = text_description
    for cost in costs:
        child = title.find_elements_by_xpath('//span[@class="%s"]'%cost)
        if child != []:
            if hide:
                to_add[cost] = child[214].text
            else:
                to_add[cost] = child[0].text
    po = spell.find_elements_by_xpath('//span[@class="costs_range"]')
    if po != []:
        if hide:
            to_add['po'] = po[214].text
        else:
            to_add['po'] = po[0].text
    return to_add

def add_row(to_add, driver, the_type, spells):
    to_add['spell_type'] = the_type
    if not check_db(to_add['spell']):    
        db['spells'].insert_one(to_add)

def check_db(spell_tag):
    return db['spells'].count_documents({'spell':spell_tag}) > 0

def get_all_spells(driver, elements, to_add):
    elementaire = list()
    specialite = list()
    sprites = []
    for element in elements:
        try:
            element_spells = driver.find_element_by_class_name('ak-elementary-spell-%s'%element)
        except Exception as e:
            print(e)
            continue
        spells_by_element = element_spells.find_elements_by_tag_name('a')
        for each_spell in spells_by_element:
            the_spell = each_spell.get_attribute('title')
            elementaire.append(the_spell)
            find_sprite = each_spell.find_element_by_xpath('//img[@alt="%s"]'%the_spell)
            sprite = find_sprite.get_attribute('src')
            sprites.append(sprite)
        
    rows = driver.find_elements_by_class_name('ak-spell-list-row')
    for row in rows:
        spells_row = row.find_elements_by_class_name('ak-elementary-spell ')
        for spell in spells_row:
            the_spell = spell.get_attribute('title')
            specialite.append(the_spell)
            find_sprite = each_spell.find_element_by_xpath('//img[@alt="%s"]'%the_spell)
            sprite = find_sprite.get_attribute('src')
            sprites.append(sprite)
            

    div_img = driver.find_element_by_class_name('ak-spell-details-illu')
    img = div_img.find_element_by_tag_name('img')
    to_drop = img.get_attribute('alt')
    to_add['spell'] = to_drop
    elementaire.remove(to_drop)
    find_zone = driver.find_element_by_xpath('//div[@class="ak-spells-elements ak-ajaxloader"]')
    find_sprite = find_zone.find_element_by_xpath('//img[@alt="%s"]'%to_drop)
    drop_sprite = find_sprite.get_attribute('src')
    to_add['sprite'] = drop_sprite
    sprites.remove(drop_sprite)
    return elementaire, specialite, sprites

def get_next(driver, spells):
    balise = driver.find_elements_by_xpath('//a[@title="%s"]'%spells[0])
    try:
        balise[0].click()
    except Exception as e:
        print(e)
    wait.until(EC.presence_of_element_located((By.XPATH, '//img[@title="%s"]'%spells[0])))
    return spells

def run(classes, elements, costs):
    for classe in classes:
        driver.delete_all_cookies()
        driver.get('https://www.wakfu.com/fr/mmorpg/encyclopedie/classes/{}'.format(classe))
        to_add = to_add_row(driver, classe, costs)
        elementaire, specialite, sprites = get_all_spells(driver, elements, to_add)
        add_row(to_add, driver, 'élementaire', elementaire)
        new_elementaire = get_next(driver, elementaire)
        for i in range(2):
            if i == 0:
                for x in range(len(new_elementaire)):
                    to_add = to_add_row(driver, classe, costs)
                    if not check_db(to_add['spell']):
                        to_add['spell'] = new_elementaire[0]
                        to_add['sprite'] = sprites[0]
                        add_row(to_add, driver, 'élementaire', new_elementaire[0])
                        del sprites[0]
                        del new_elementaire[0]
                        if len(new_elementaire) > 0:
                            get_next(driver, new_elementaire)
            else:
                for x in range(len(specialite)):
                    if x == 0:
                        to_add = to_add_row(driver, classe, costs)
                    else:
                        to_add = to_add_row(driver, classe, costs, hide=False)
                    if not check_db(to_add['spell']):
                        to_add['spell'] = specialite[0]
                        to_add['sprite'] = sprites[0]
                        add_row(to_add, driver, 'spécialité', specialite[0])
                        del sprites[0]
                        del specialite[0]
                        if len(specialite) > 0:
                            get_next(driver, specialite)


run(classes, elements, costs)


driver.close()

client.close()