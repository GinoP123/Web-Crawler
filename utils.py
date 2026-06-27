import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from collections import defaultdict
import urllib3
from bs4 import BeautifulSoup
import bs4
import pandas as pd
import time
import random
from datetime import datetime
import numpy as np
import re
from collections import defaultdict
from tqdm import tqdm
import subprocess as sp
from inspect import signature
import webbrowser
import zmq
import os, glob
from selenium.webdriver.support import expected_conditions as EC
import hashlib
import gensim.downloader
from nltk.corpus import words
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import importlib
import genie.genie_v1 as genie
import aladdin.aladdin_0_1 as aladdin
genie = importlib.reload(genie)
aladdin = importlib.reload(aladdin)


def get_glove_vectors():
    glove_vectors = gensim.downloader.load('glove-wiki-gigaword-300')
    words_ = words.words()
    common_words = set([x for x in words_ if glove_vectors.has_index_for(x)])
    return glove_vectors, common_words

class Logger():
    def __init__(self, silent=True):
        self.start_time = datetime.now().strftime('%h_%d_%H-%M')
        self.outdir = f"dataset/{self.start_time}"
        os.makedirs(self.outdir, exist_ok=True)
        self.outfile = f"{self.outdir}/log.txt"
        sp.run(f"touch {self.outfile}", shell=True)
        if not silent:
            sp.run(f"/usr/bin/open -a 'Google Chrome' {self.outfile}", shell=True)
        # self.outfile = open(self.outfile, 'a')

    def log(self, x):
        with open(self.outfile, 'a') as outfile:
            outfile.write(x + '\n\n')

    def close(self):
        # self.outfile.close()
        pass

GLOBALS = {
    "driver": None,
    "form_data": None,
    "initial_values": None,
    "logger": None,
    "glove_vectors": None,
    "common_words": None,
    "page_num": 1,
    'interactible_elements': None
}


def restart_driver():
    reset_form_log()
    GLOBALS["logger"].log(f"Restarting Driver")
    GLOBALS["driver"] = webdriver.Chrome()

    GLOBALS["driver"].set_window_size(880, 900)
    GLOBALS["driver"].set_window_position(100,0)

    # GLOBALS["driver"].set_window_size(1280, 1200)
    # GLOBALS["driver"].set_window_position(120,0)
    return 'Driver Restarted'

def get_parent(element):
    return element.find_element("xpath", "..") if element.tag_name.lower() != 'html' else element

def goto_link(link):
    if GLOBALS["driver"] is None:
        restart_driver()
    GLOBALS["logger"].log(f"Opening Link '{link}'")
    GLOBALS["driver"].get(link)
    iframe_check()
    return ''
    
def close():
    GLOBALS["logger"].log("Closing Driver")
    GLOBALS["logger"].close()
    GLOBALS["driver"].quit()
    GLOBALS["driver"] = None
    return ''

def get_element_info(element, soup=False):
    soup = type(element) == bs4.element.Tag
    text = element['label'] if element.has_attr('label') else element.text
    while not text:
        text = element.text
        if not text:
            if soup:
                text = element['placeholder'] if element.has_attr('placeholder') else ''
            else:
                text = element.get_attribute("placeholder")
        if not text:
            if soup:
                text = element['aria-label'] if element.has_attr('aria-label') else ''
            else:
                text = element.get_attribute("aria-label")
        
        if soup:
            element = element.parent
        else:
            element = element.find_element("xpath", "..")
    if not text or len(text) > 100:
        if soup:
            text = ' '.join(element['class']) if element.has_attr('class') else ''
        else:
            text = element.get_attribute("class")
        if text:
            text += f"RANDOM_TAG={str(random.random())}"
    return text

def increment_info(info):
    if type(info) == tuple:
        info = (info[0], info[1]+1)
    else:
        info = (info, 2)
    return info

def find_buttons():
    soup = get_soup()
    buttons = {x.text: x for x in soup.find_all(lambda tag: tag.has_attr('class') and "button" in tag['class'])}
    include_elements = soup.find_all(lambda tag: tag.name in ["sdf-button", "button", "li", "a", 'sdf-checkbox', 'checkbox'])
    for x in include_elements:
        info = get_element_info(x).strip()
        while info and info in buttons:
            info = increment_info(info)
        buttons[info] = x
    formatted_buttons = {x if type(x) == str else f"{x[0]} ({x[1]})": y for x, y in buttons.items()}
#     GLOBALS["logger"].log(f"BUTTONS: '{str(buttons)}'")
    return formatted_buttons

def find_inputs():
    soup = get_soup()
    elements = {}
    seen = set()

    for element in list(soup.find_all(lambda tag: tag.name in ["sdf-input", "input", "textarea"])) + list(soup.select(".input")):
        if element not in seen:
            info = get_element_info(element).strip()
            while info and info in elements:
                info = increment_info(info)
            elements[info] = element
            seen.add(element)
    formatted_elements = {x if type(x) == str else f"{x[0]} ({x[1]})": y for x, y in elements.items()}
    return formatted_elements

def print_inputs():
    return '\n'.join([str(x).replace('\n', '\\n') for x in find_inputs().keys() if 'RANDOM_TAG' not in x])

def print_buttons():
    return '\n'.join([str(x).replace('\n', '\\n') for x in find_buttons().keys() if 'RANDOM_TAG' not in x])

def click_button_element(element, parents=5, scroll_on=True):
    counter = 0
    while counter < parents:
        try:
            if scroll_on:
                GLOBALS['driver'].execute_script("arguments[0]&&arguments[0].scrollIntoView({behavior: \"smooth\", block: \"center\", }, {duration: 250});", element)
                sleep(1)
            # webdriver.ActionChains(GLOBALS["driver"]).move_to_element(element).click(element).perform()
            GLOBALS['driver'].execute_script("arguments[0]&&arguments[0].click();", element)
            sleep(1)
            return True
        except selenium.common.exceptions.StaleElementReferenceException:
            GLOBALS['logger'].log('Error: UNABLE TO CLICK DUE TO STALE ELEMENT EXCEPTION')
            break
        except selenium.common.exceptions.ElementClickInterceptedException:
            element = get_parent(element)
            counter += 1

def fill_input_element(element, value):
    if click_button_element(element):
        GLOBALS["logger"].log(f"Clicking Success")
        if value.lower() != 'click':
            # element.clear()
            # sleep(0.25)
            element.send_keys(value)
            GLOBALS["logger"].log(f"Filling with '{value}', Success")
            sleep(1)
        else:
            GLOBALS["logger"].log(f"Filling with '{value}', Failure")        
        return True
    else:
        GLOBALS["logger"].log(f"Clicking Faliure")

def click_out(element):
    action = ActionChains(GLOBALS['driver'])
    try:
        action.move_to_element(element).move_by_offset(-150, 0).click().perform()
    except BaseException as e:
        try:
            action.move_to_element(element).move_by_offset(150, 0).click().perform()
        except BaseException as e:
            GLOBALS['logger'].log(f"{element.get_attribute('id')}, Failed Click Out")
            print(f"{element.get_attribute('id')}, Failed Click Out")

def click_dropdown_element(element, value):
    click_button_element(element)
    soup = get_soup()
    options = soup.find_all(lambda tag: tag.name == "li" and value == tag.text)
    if options:
        driver_element = soup_to_selenium(options[0])
        click_button_element(driver_element)
        GLOBALS['logger'].log(f"Successful dropdown change to value '{value}'")
    else:
        GLOBALS['logger'].log(f"ERROR: CAN'T FIND DROPDOWN OPTION: '{value}'")

def click_multi_select(element, value):
    for item in value.split('\n'):
        fill_input_element(element, f"{item}\n")
        soup = get_soup()
        options = [(len(str(x)), x) for x in soup.find_all(lambda x: x.text == item)]
        if options:
            driver_element = soup_to_selenium(min(options)[1])
            click_button_element(driver_element)
            GLOBALS['logger'].log(f"Successful multiselect change: {item}")
        else:
            GLOBALS['logger'].log(f"ERROR: CAN'T FIND MULTISELECT OPTION: {value}")
        click_out(element)


def click_button(key):
    buttons = find_buttons()
    if key in buttons and key:
        element = soup_to_selenium(buttons[key])
        if click_button_element(element):
            GLOBALS["logger"].log(f"Clicking '{key}', Success")
            return 'Success'
        
    GLOBALS["logger"].log(f"Clicking '{key}', Failure")
    return 'Failure'


def click_button_patiently(key, timeout=120):
    wait_time = 0
    while wait_time < timeout:
        if key in find_buttons():
            return click_button(key)
        else:
            wait_time += 0.5
            time.sleep(0.5)
    GLOBALS["logger"].log(f"ERROR: Key {key} not found after waiting {timeout} sec")
    return 'Failure'

def fill_input(key, value):
    inputs = find_inputs()    
    if key in inputs:
        element = soup_to_selenium(inputs[key])
        if fill_input_element(element, value):
            return 'Success'
    else:
        GLOBALS["logger"].log(f"ERROR: Key {key} not found")
    return 'Failure'


def fill_input_patiently(key, value, timeout=120):
    wait_time = 0
    while wait_time < timeout:
        if key in find_inputs():
            return fill_input(key, value)
        else:
            wait_time += 0.5
            time.sleep(0.5)
    GLOBALS["logger"].log(f"ERROR: Key {key} not found after waiting {timeout} sec")
    return 'Failure'


def break_():
    GLOBALS["logger"].log("BREAKING")
    return "BREAKING"

def sleep(x):
    time.sleep(max(x + (0.125 * np.random.randn()), 0.125))

def copy_html():
    outdir = f'{GLOBALS["logger"].outdir}/html_files'
    os.makedirs(outdir, exist_ok=True)
    outfile_path = f'{outdir}/page_{GLOBALS["page_num"]}_{datetime.now().strftime("%m-%d_%H-%M-%S")}.html'
    with open(outfile_path, 'w') as outfile:
        outfile.write(GLOBALS["driver"].page_source)
    GLOBALS["logger"].log(f"Saved HTML to '{outfile_path}'")
    return f"Saved HTML to '{outfile_path}'"

def back():
    GLOBALS['driver'].back()
    sleep(1)
    return ''

def dun_b_wait():
    soup = get_soup()
    challenge = soup.find_all(lambda x: x.name == 'iframe' and x.has_attr('challenge'))
    if challenge:
        wait_time = 10
        if challenge[0].has_attr('data-duration'):
            wait_time = eval(challenge[0]['data-duration']) + 3
        GLOBALS["logger"].log(f'Waiting for {wait_time} seconds')
        sleep(wait_time)
        GLOBALS['driver'].implicitly_wait(wait_time)

def dun_b_search(name):
    click_button('Search')
    sleep(1)
    GLOBALS['driver'].implicitly_wait(30)
    fill_input('Search here... (2)', name)
    sleep(1)
    GLOBALS['driver'].implicitly_wait(30)

    buttons = find_buttons()
    if 'Company Profile' in buttons:
        click_button('Company Profile')
        dun_b_wait()

    outdir = 'dun_b_data'
    os.makedirs(outdir, exist_ok=True)
    with open(f"{outdir}/{name}_{GLOBALS['logger'].start_time}.html", 'w') as outfile:
        outfile.write(GLOBALS["driver"].page_source)
    sleep(3)

    if 'Company Profile' in buttons:
        back()
    else:
        click_button('Search')
    dun_b_wait()
    return 'Done'

def save_page_html():
    page_path = f"{GLOBALS['logger'].outdir}/html_files/"
    os.makedirs(page_path, exist_ok=True)
    page_path += f"{datetime.now().strftime('%h_%d_%H-%M_%h-%m')}.html"
    with open(page_path, 'w') as outfile:
        outfile.write(GLOBALS['driver'].page_source)
    return f"Saved html to '{page_path}'"

def save_page_img():
    page_path = f"{GLOBALS['logger'].outdir}/png_files/"
    os.makedirs(page_path, exist_ok=True)
    page_path += f"{datetime.now().strftime('%h_%d_%H-%M_%h-%m')}.png"
    with open(page_path, 'w') as outfile:
        original_size = GLOBALS['driver'].get_window_size()
        required_width = GLOBALS['driver'].execute_script('return document.body.parentNode.scrollWidth')
        required_height = GLOBALS['driver'].execute_script('return document.body.parentNode.scrollHeight')
        GLOBALS['driver'].set_window_size(required_width, required_height)
        # driver.save_screenshot(path)  # has scrollbar
        GLOBALS['driver'].find_element(By.TAG_NAME, 'body').screenshot(page_path)  # avoids scrollbar
        GLOBALS['driver'].set_window_size(original_size['width'], original_size['height'])
    return f"Saved image to '{page_path}'"

def preprocess_text(string):
    for char in set(string.lower()) - set([chr(x) for x in range(ord('a'), ord('z')+1)]):
        string = string.replace(char, ' ')

    for char in set([chr(x) for x in range(ord('A'), ord('Z')+1)]):
        string = string.replace(char, f' {char.lower()}')

    string = ' '.join([x for x in string.split(' ') if x])
    weird_words = {x for x in string.split(' ') if not GLOBALS["glove_vectors"].has_index_for(x)}
    weird_map = {}

    for word_mix in weird_words:
        best = (float('-inf'), 0, 0)
        for i in range(1, len(word_mix)):
            best = max(best, (int(word_mix[:i] in GLOBALS["common_words"]) + int(word_mix[i:] in GLOBALS["common_words"]), min(i, len(word_mix)-i), i))
        if best[0] == 2:
            weird_map[word_mix] = f"{word_mix[:best[-1]]} {word_mix[best[-1]:]}"

    for word_mix, replacewith in weird_map.items():
        string = string.replace(word_mix, replacewith)

    for word_mix in weird_words - set(weird_map):
        string = string.replace(word_mix, '?')
    return string

def get_text_stack(element, layers=10, word_limit=50):
    counter = 0
    embedding = []
    while len(embedding) < layers:
        if (element.parent is None) or (element.text and (not embedding or (embedding[-1] != element.text))):
            embedding.append(element.text)
        if 'parent' in dir(element.parent):
            element = element.parent
        counter += 1
        if counter > 200:
            raise AssertionError
    embedding = [preprocess_text(embedding_i).split(' ')[:word_limit-1] for embedding_i in embedding]
    lengths = np.array([len(x) for x in embedding]).astype(np.int32)
    embedding = [['^'] + embedding_i + list("*" * (word_limit-length-1)) for length, embedding_i in zip(lengths, embedding)]
    return embedding

def reset_form_log():
    GLOBALS['logger'].log(f"Resetting Form Log")
    GLOBALS["form_data"] = None
    GLOBALS["initial_values"] = None
    GLOBALS["interactible_elements"] = None
    return 'Form Log Reset'

def write_completed_form(post_values):
    assert sorted(list(GLOBALS["form_data"].keys())) == sorted(list(GLOBALS["initial_values"].keys()))
    assert sorted(list(GLOBALS["form_data"].keys())) == sorted(list(post_values.keys()))
    BACKSLASH_CHAR = "\\"
    NEWLINE_CHAR = "\n"
    with open(f"{GLOBALS['logger'].outdir}/dataset.txt", 'a') as outfile:
        for sub_element_key, sub_element in GLOBALS["form_data"].items():
            for item in sub_element[1:-1]:
                outfile.write(item + '\n')
            
            outfile.write(('-'*50) + '\n')
            outfile.write(sub_element[-1] + '\n')
            outfile.write(('-'*50) + '\n')
            
            outfile.write(f'"{GLOBALS["initial_values"][sub_element_key].replace(NEWLINE_CHAR, f"{BACKSLASH_CHAR}n")}"' + '\n')
            outfile.write(f'"{post_values[sub_element_key].replace(NEWLINE_CHAR, f"{BACKSLASH_CHAR}n")}"' + '\n\n\n')
    reset_form_log()

def record_state():
    values = get_values()
    copy_html()
    if GLOBALS["initial_values"] is not None:
        write_keystroke_log()
        write_completed_form(values)
        GLOBALS["page_num"] += 1
        # return f"Saved data to '{GLOBALS['logger'].outdir}/dataset.txt'" + '\n'.join((f"{x}: {y}" for x, y in values.items()))
    else:
        GLOBALS["initial_values"] = values
        GLOBALS["interactible_elements"] = ['Pre-Recording Check']
        record()
    return 'Done\n'
        # return "Stored Initial Cache\n\n" + '\n'.join((f"{x}: {y}" for x, y in values.items()))
##### TODO CHANGE WITH beautiful soup to reduce time
def add_section(section_name, num, sleep_time=3):
    soup = get_soup()
    if soup.find_all(lambda tag: tag.has_attr('data-automation-id') and tag['data-automation-id'] == 'reviewJobApplicationPage'):
        return
    for i in range(num):
        soup = get_soup()
        ancestor = soup.find_all(lambda tag: tag.has_attr('data-automation-id') and tag['data-automation-id'] == section_name)
        if ancestor:
            button = ancestor[0].find_all(lambda tag: tag.name == 'button' and 'Add' in tag.text)[0]
            button = soup_to_selenium(button)
            webdriver.ActionChains(GLOBALS["driver"]).move_to_element(button).perform()
            GLOBALS["driver"].execute_script("arguments[0].click();", button)
            GLOBALS["driver"].implicitly_wait(3)
            sleep(sleep_time)
    GLOBALS["logger"].log(f"FINISHED {section_name} add")

def classify(element):
#     return element.get_attribute('data-automation-id')
    if element.has_attr('data-uxi-widget-type') and element['data-uxi-widget-type']:
        return element['data-uxi-widget-type']
    elif element.name == 'button' or element.name == 'select' or \
        (element.has_attr('role') and element['role'] == 'button'):
        return 'button'
    elif (element.has_attr('type') and 'select' in element['type']) or \
        (element.has_attr('aria-autocomplete') and element['aria-autocomplete'] == 'list'):
        return 'multiselect'
    elif element.has_attr('type') and 'check' in element['type']:
        return 'checkbox'
    elif element.has_attr('type') and 'radio' in element['type']:
        return 'radio'
    elif element.has_attr('type') and \
        element['type'] in ['hidden', 'button', 'text']:
        return element['type']
    elif element.name in ['textarea', 'input']:
        return 'text'
    return '?'

def soup_to_selenium(soup_element):
    if soup_element is None:
        return None
    quotation_mark='"'
    if soup_element.has_attr('class'):
        del soup_element['class']
    if soup_element.has_attr('style'):
        del soup_element['style']
    xml_components = " and ".join([f"@{attr}={quotation_mark}{value}{quotation_mark}" for attr, value in soup_element.attrs.items() if \
        not any(map(lambda x: ord(x) > 255 or x in ['"', "'"], value)) and \
        value])
    # not any(map(lambda x: x in attr, '.:')) and 
    # return xml_components
    # return xml_components
    elements = GLOBALS['driver'].find_elements('xpath', f'//{soup_element.name}[{xml_components}]')
    if elements:
        return elements[0]

def get_form_data():
    iframe_check()
    GLOBALS["form_data"] = defaultdict(list)
    soup = get_soup()
    for element in aladdin_inputs():
        ID = element['id'] if element.has_attr('id') else f"ID_NOT_FOUND:_{element.name}_{hash(element)}"
        GLOBALS["form_data"][f'{ID}'].append(element)
        GLOBALS["form_data"][f'{ID}'].append(classify(element))
        GLOBALS["form_data"][f'{ID}'].append(element['data-automation-id'] if element.has_attr('data-automation-id') else 'None')
        GLOBALS["form_data"][f'{ID}'].append('\n'.join([' '.join(x) for x in get_text_stack(element)]))
    return GLOBALS["form_data"]


def next_():
    if GLOBALS["initial_values"] is None:
        record_state()
    
    rstate_output_1 = record_state()
    
    soup = get_soup()
    options = soup.find_all(lambda tag: tag.name == "button" and tag.text.lower().strip() in ['next', 'save and continue'])[0]
    next_button = soup_to_selenium(options)

    click_button_element(next_button, scroll_on=False)
    iframe_check()
    GLOBALS["driver"].implicitly_wait(5)
    
    sleep(3)

    add_section('workExperienceSection', 4)
    add_section('educationSection', 2)
    add_section('websiteSection', 2)
    
    sleep(5)
    reset_form_log()
    rstate_output_2 = record_state()
    fill_output = fill_predicted_values()
    return '\n\n'.join([rstate_output_1, 'Successful Mouse Click', rstate_output_2, fill_output])

def open_broadcom():
    restart_driver()
    goto_link("https://broadcom.wd1.myworkdayjobs.com/en-US/External_Career/job/USA-IL-Lisle-Warrenville-Road/Mainframe-Technical-Support-Engineer_R020313")
    sleep(3)
    GLOBALS["driver"].implicitly_wait(15)
    sleep(3)
    buttons = find_buttons()
    GLOBALS["driver"].execute_script("arguments[0].click();", soup_to_selenium(buttons['Apply']))
    # GLOBALS["driver"].implicitly_wait(3)
    sleep(5)
    buttons = find_buttons()
    GLOBALS["driver"].execute_script("arguments[0].click();", soup_to_selenium(buttons['Apply Manually']))
    sleep(4)
    GLOBALS["driver"].implicitly_wait(30)
    sleep(4)
    record_state()
    return fill_predicted_values()

def open_databricks():
    restart_driver()
    goto_link("https://www.databricks.com/company/careers/engineering/database-engine-internals---staff-software-engineer-6806692002")
    sleep(4)
    GLOBALS["driver"].implicitly_wait(15)
    sleep(4)
    buttons = find_buttons()
    # while 'Apply now' not in buttons:
    #     sleep(4)
    #     buttons = find_buttons()
    #     print(buttons)
    GLOBALS["driver"].execute_script("arguments[0].click();", soup_to_selenium(buttons['Apply now']))
    GLOBALS["driver"].implicitly_wait(15)
    sleep(3)
    GLOBALS["driver"].execute_script("arguments[0].click();", soup_to_selenium(buttons['Close']))
    iframe_check()
    sleep(1)
    record_state()
    return fill_predicted_values()

def open_adobe():
    restart_driver()

    goto_link("https://careers.adobe.com/us/en/job/ADOBUSR149007EXTERNALENUS/2025-Intern-Research-Firefly")
    GLOBALS["driver"].implicitly_wait(15)
    sleep(3)
    buttons = find_buttons()
    GLOBALS["driver"].execute_script("arguments[0].click();", soup_to_selenium(buttons['Apply now']))
    sleep(4)
    GLOBALS["driver"].implicitly_wait(30)
    sleep(2)
    record_state()
    # GLOBALS["driver"].execute_script("arguments[0].click();", soup_to_selenium(buttons['Close']))
    return fill_predicted_values()

# def is_valid_form_data():
#     return len(form_input_numbers) == len(set(aladdin_inputs()))

# def correct_form_data():
#     if GLOBALS['form_data'] is None:
#         return
#     ### TODO: FIND MORE PERMANENT FIX FOR THIS ISSUE OF MISSING AND REMOVED/ADDED INPUTS
#     form_input_numbers = set([eval(x[len('input-'):].split('.')[0]) for x in GLOBALS["form_data"].keys()])
#     for input_num in form_input_numbers - set(get_input_numbers()):
#         for key in list(GLOBALS["form_data"].keys()):
#             if input_num == eval(key[len('input-'):].split('.')[0]):
#                 del GLOBALS["form_data"][key]
#                 if not GLOBALS['initial_values'] is None and key in GLOBALS['initial_values']:
#                     del GLOBALS['initial_values'][key]

def soup_to_soup(elem, db, soup):
    hit = aladdin.get_nearest_neighbor(elem, db, certificate_needed=True)
    string = hit[1]
    attributes = re.findall('(?<=\\ ).*?".*?"', string)
    attributes = {attribute.split('=')[0]:attribute.split('=')[1].strip('"') for attribute in attributes}

    name = string.split(' ')[0][1:]
    candidates = soup.find_all(lambda x: x.name == name and \
                  all([x.has_attr(y) for y in attributes]) and \
                  all([x[y] == z for y, z in attributes.items()]))
    # if not candidates:
    #     print(attributes)
    #     print(string)
    return candidates[0] if candidates else None

def format_html(a):
    return a.replace('\n', '').replace('<', '\n<').replace('"\n<', '"<').replace('\n</', '</').strip()

def get_soup():
    return BeautifulSoup(GLOBALS["driver"].page_source, 'lxml', multi_valued_attributes=None)

def get_db():
    return format_html(GLOBALS['driver'].page_source)

def get_values():
    if (bool(GLOBALS["form_data"]) != bool(GLOBALS["initial_values"])):
        GLOBALS["logger"].log(f'RESETTING FORM LOG IV Mismatch {bool(GLOBALS["form_data"])} {bool(GLOBALS["initial_values"])}')
        reset_form_log()
        record()

    if GLOBALS["form_data"] is None:
        get_form_data()

    soup = get_soup()
    db = get_db()
    values = {}
    for id_name, data_list in GLOBALS["form_data"].items():
        tag, *data_list = data_list
        
        if id_name.startswith('ID_NOT_FOUND'):
            element = soup_to_soup(element, db, soup)
        else:
            element = soup.find(id=id_name)
        if element is None:
            values[id_name] = 'ERROR: UNKNOWN'
        elif 'button' in data_list[0]:
            values[id_name] = element.text
        elif 'check' in data_list[0] or 'radio' in data_list[0]:
            values[id_name] = element['aria-checked'] if element.has_attr('aria-checked') else "None"
        elif 'select' in data_list[0]:
            values[id_name] = element.parent.text
        else:
            values[id_name] = element['value'] if element.has_attr('value') else element.text
    return values


def get_predicted_values():
    if GLOBALS["initial_values"] is None:
        record_state()
    current_values = get_values()

    predicted_values = {}
    for id_name, input_form_data in GLOBALS['form_data'].items():
        current_value = current_values[id_name]
        predicted_values[id_name] = genie.predict(input_form_data, current_value)
    return predicted_values


def print_predicted_values():
    predicted_values = get_predicted_values()
    ret_string = ''
    for id_name, input_form_data in GLOBALS['form_data'].items():
        initial_value = GLOBALS['initial_values'][id_name]
        predicted_values[id_name] = predicted_values[id_name]
        ret_string += f"{id_name}: {initial_value} -> {predicted_values[id_name]}\n"
    return ret_string


def fill_predicted_values():
    genie.reset_internal_indices()

    soup = get_soup()
    db = get_db()
    current_values = get_values()
    ret_string = ''

    last_element = None
    for id_name, current_value in current_values.items():
        soup_element, *input_data = GLOBALS['form_data'][id_name][:-1]
        if id_name.startswith('ID_NOT_FOUND'):
            soup_element = soup_to_soup(soup_element, db, soup)
            element_ = soup_to_selenium(soup_element)
        else:
            soup_element = soup.find(id=id_name)
            element_ = soup_to_selenium(soup_element)
            if element_ is None:
                soup = get_soup()
                element_ = soup.find(id=id_name)
                element_ = soup_to_selenium(element_)
        element = element_
        if element is None:
            GLOBALS['logger'].log(f"SKIPPING ELEMENT ELEMENT {id_name}")
            continue
        try:
            ### TODO: REMOVE THIS AND FIX THE Autocomplete elements
            ###  or (soup_element.has_attr('aria-autocomplete') and soup_element['aria-autocomplete'] == 'list')
            
            predicted_name, predicted_value = genie.predict(GLOBALS['form_data'][id_name], current_value)
            ret_string += f"{id_name}: {current_value[:30]} -> {predicted_name}\n"
            if predicted_value == 'ignore' or 'hidden' in input_data[0]:
                continue
            elif predicted_value == 'click':
                click_button_element(element)
                last_element = element
            elif input_data[0] == 'text':
                fill_input_element(element, predicted_value)
                last_element = element
                click_out(last_element)
            elif input_data[0] == 'button':
                click_dropdown_element(element, predicted_value)
                last_element = element
                click_out(last_element)
            elif 'select' in input_data[0]:
                click_multi_select(element, predicted_value)
                click_out(last_element)
            else:
                # fill_input_element(element, predicted_value)
                # last_element = element
                # click_out(last_element)
                GLOBALS['logger'].log("UNSURE WHAT TO DO")
                GLOBALS['logger'].log(f"{id_name} {predicted_value} {input_data}")
                GLOBALS['logger'].log("\n\n")
                print("UNSURE WHAT TO DO")
                print(f"{id_name} {predicted_value} {input_data}")
                print("\n\n")
        except BaseException as e:
            soup_elem_str = str(soup_element).replace('\n', '\\n')

            GLOBALS['logger'].log(f"FAILED ON ELEMENT ELEMENT {id_name}, {predicted_value}, {input_data}\n")
            GLOBALS['logger'].log(f"{e.__class__}\n")
            GLOBALS['logger'].log(f"{soup_elem_str}\n\n")
            # print(f"FAILED ON ELEMENT {id_name}, {input_data[0]}, {predicted_value}, {input_data}\n")
            # print(f"{e.__class__}\n")
            # print(f"{soup_elem_str}\n\n")
            with open("aladdin/dataset/error_list.txt", 'a') as outfile:
                outfile.write(f"{os.path.basename(GLOBALS['logger'].outdir)}\n")
                outfile.write(f"FAILED ON ELEMENT {id_name}, {input_data[0]}, {predicted_value}, {input_data}\n")
                outfile.write(f"{e.__class__}\n")
                outfile.write(f"{soup_elem_str}\n\n")


    # if last_element is not None:
    #     click_out(last_element)
    sleep(1)
    return ret_string


def find_interactible_elements():
    soup = get_soup()
    return soup.find_all(lambda x: x.name in ['input', 'button', 'textarea', 'select'] and x.has_attr('id'))


def aladdin_inputs():
    element_list = find_interactible_elements()
#    return np.array(element_list)[]
    return [x for x, include in zip(element_list, aladdin.predict_batch(element_list)) if include]

def hash(x):
    return hashlib.sha256(x.encode()).hexdigest()[:16]

def iframe_check():
    return
    soup = get_soup()
    iframes = soup.find_all(lambda x: x.name == 'iframe' and hasattr(x, 'src'))
    print(iframes)
    if iframes:
        print("SWITCHING TO IFRAME")
        GLOBALS['driver'].switch_to.frame(soup_to_selenium(iframes[0]))
    return ''
    # driver.switch_to.default_content()


def record():
    # sleep(2)
    # GLOBALS['driver'].execute_script("window.scrollTo({top: document.body.scrollHeight, left: 0, behavior: \"smooth\"});")
    # sleep(2)
    # GLOBALS['driver'].execute_script("window.scrollTo({top: 0, left: 0, behavior: \"smooth\"});")

    elements = find_interactible_elements()
    GLOBALS["logger"].log(f"Recording Keystrokes: Setting listeners on {len(elements)} elements")
    log_script = """
var genie_log = new Map();

function genie__log_func(id, key) { 
    if (!(genie_log.has(id))) {
        genie_log.set(id, key);
    }
    else {
        old_value = genie_log.get(id);
        genie_log.set(id, old_value + key);
    }
}

function genie__print_log() {
    var output = "";
    var elem = document.getElementById("genie_logger");
    genie_log.forEach((value, key) => {
        output += key + ": " + value + "%%%NEWLINE%%%";
    });
    elem.setAttribute("value", output);
}
""".strip().replace("\n", ' ')

    GLOBALS['driver'].execute_script(''.join(f"""
    var s=window.document.createElement('script');
    s.type = 'text/javascript';
    s.text = '{log_script}';
    s.id = 'genie_logger';
    window.document.head.appendChild(s);
    """))
    soup = get_soup()
    
    for element in elements:
        ID = element['id']
        selenium_element = soup_to_selenium(element)
        assert selenium_element
        GLOBALS["driver"].execute_script("arguments[0] && arguments[0].addEventListener('keydown', function (e) { genie__log_func('" + ID + "', e['key']); });", selenium_element)
        GLOBALS["driver"].execute_script("arguments[0] && arguments[0].addEventListener('click', function (e) { genie__log_func('" + ID + "', '%%%click%%%'); });", selenium_element)
    assert all([x.has_attr('id') for x in elements])
    GLOBALS['interactible_elements'] = {x['id']: x for x in elements}

def listen():
    GLOBALS["logger"].log(f"Listening to Keystrokes")
    if not GLOBALS['interactible_elements']:
        return []
    GLOBALS["driver"].execute_script('genie__print_log()')
    logger_elem = get_soup().find(id='genie_logger')
    ret = [x for x in logger_elem['value'].split('%%%NEWLINE%%%') if x] if logger_elem.has_attr('value') else []
    ret = [(GLOBALS['interactible_elements'][x.split(': ')[0]], x.split(': ')[1]) for x in ret]
    return ret

def print_listen():
    if GLOBALS['interactible_elements'] is None:
        return "ERROR: No interactible elements"
    output = ''
    for x, y in listen():
        output += f"{x}\n{y}\n\n"
    return output

def process_log_text(string):
    string = string.replace('%%%click%%%', '')
    if not string:
        return 'click'
    inter = string.replace('Shift', '')
    inter = inter.split('Backspace')[::-1]
    while len(inter) > 1:
        a = inter.pop()
        inter[-1] = a[:-1] + inter[-1]
    return ''.join(inter)

def write_keystroke_log():
    outdir = f"{GLOBALS['logger'].outdir}/keystrokes"
    os.makedirs(outdir, exist_ok=True)

    outfile_path = f'{outdir}/page_{GLOBALS["page_num"]}_{datetime.now().strftime("%m-%d_%H-%M-%S")}.txt'
    with open(outfile_path, 'a') as outfile:
        listen_output = listen()
        for elem, value in listen_output:
            outfile.write(f"{classify(elem)}\n")
            outfile.write(elem['data-automation-id']+'\n' if elem.has_attr('data-automation-id') else 'None\n')
            outfile.write(str(elem) + '\n')
            outfile.write(f'{value}\n')
            outfile.write(('-'*50) + '\n')
            outfile.write('\n'.join([' '.join(x) for x in get_text_stack(elem)]) + '\n')
            outfile.write(('-'*50) + '\n')
            outfile.write(f'\n{process_log_text(value)}\n\n\n')
        
    GLOBALS["logger"].log(f"Saved Keystrokes to '{outfile_path}'")
    return f"Saved Keystrokes to '{outfile_path}'"

def record_state_and_fill():
    record_state()
    return fill_predicted_values()


