import time
import re

from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from simon.accounts.pages import LoginPage

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
_conv = "GwoLeo"
url_cemantix = "https://cemantix.herokuapp.com/"
tableaudujour = []
col_id=0
col_mot=1
col_heure=2
col_score=3
regex_proposition = "c::(.+)::\n(.+)"
rex_mot = re.compile(regex_proposition)
last_msg = None


service = Service(executable_path="Z:\Progra\python\WAcemantix\chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.maximize_window()
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[1])
driver.get(url_cemantix)
cem_tabs = driver.current_window_handle



############
driver.movet
guessable = driver.findElement(By.ID("guessable"));
