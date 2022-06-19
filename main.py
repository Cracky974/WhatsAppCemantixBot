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

#varianles globales
url_cemantix = "https://cemantix.herokuapp.com/"
tableaudujour = []
col_id=0
col_mot=1
col_heure=2
col_score=3
regex_proposition = "c::(.+)::\n(.+)"
rex_mot = re.compile(regex_proposition)
last_msg = None


#tableau 2D ID | mot | heure
#           1   essai  10:15
#           2   manger 15:12


def column(matrix, column):
    return [row[column] for row in matrix]

# Creating the driver (browser)
#driver = webdriver.Firefox()
service = Service(executable_path="Z:\Progra\python\WAcemantix\chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.maximize_window()
# Login
#       and uncheck the remember check box
#       (Get your phone ready to read the QR code)
login_page = LoginPage(driver)
login_page.load()
wa_tabs = driver.current_window_handle
time.sleep(15)
#Selection de la conversation Gwoleo
try:
    conv_Gwoleo = driver.find_element(By.XPATH, "//*[@id='pane-side']/div[2]//*[@title='Ariane']")
    conv_Gwoleo.click()
    textbox_wa = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]")
except NoSuchElementException :
    print("Oops, impossible de trouver Gwoleo")


#Ouverture de l'onglet cemantix
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[1])
driver.get(url_cemantix)
cem_tabs = driver.current_window_handle

try:
    close_dialog = driver.find_element(By.XPATH, "//*[@id='dialog-close']")
    close_dialog.click() #pour enlever le popup
except NoSuchElementException :
    print("Oops, impossible de trouver l'élément X")

form_guess = driver.find_element(By.XPATH, "//*[@id='guess']")
form_guess.click()
form_guess.clear()
driver.switch_to.window(wa_tabs)


#####################################################################################
def score_proposition_cemantix(proposition_gwoleo):
    global score
    driver.switch_to.window(cem_tabs)
    try:
        form_guess.click()
        form_guess.clear()
        form_guess.send_keys(proposition_gwoleo)
        form_guess.submit()
        time.sleep(0.5)
        element = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "popup"))
        )
        time.sleep(1) #attente de l'affichage du score
        score = element[2].text

    except TimeoutException:
        score = 0
    finally:
        if re.match("Je ne connais pas le mot", driver.find_element(By.ID, "error").text):
            score = -1
        driver.switch_to.window(wa_tabs)
        return (score)

def getscore(rex_msg, tableaudujour, textbox_wa = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]")):
    mot = rex_msg.group(1).replace(" ", "")
    if mot not in column(tableaudujour, col_mot):
        heure =rex_msg.group(2)
        if len(tableaudujour ) >0:
            _id = tableaudujour[len(tableaudujour ) -1][0] + 1
        else:
            _id =0
        ligne = [_id, mot, heure, score_proposition_cemantix(mot)]

        textbox_wa.clear()
        textbox_wa.send_keys("id :  " +str(_id ) +"  mot : " + mot +"   " +str(score))
        textbox_wa.send_keys(Keys.RETURN)
        return ligne
    else:
        return None


######################################################################################

driver.switch_to.window(wa_tabs)
try:
    messages = driver.find_elements(By.XPATH, "//div[contains(concat(' ',normalize-space(@class),' '),' message-in ')]")
    if messages.__len__() == 0:
        print("Oops, impossible de trouver les messages")

    else:
        last_msg = messages[-1]
except NoSuchElementException:
    print("Oops, impossible de trouver les messages")


while(1):
    #Selection des messages reçu
    try:
        driver.switch_to.window(wa_tabs)
        messages = driver.find_elements(By.XPATH, "//div[contains(concat(' ',normalize-space(@class),' '),' message-in ')]")
        if messages.__len__() == 0:
            print("Oops, impossible de trouver les messages")
            break
    except NoSuchElementException:
        print("Oops, impossible de trouver les messages")
        break
    if last_msg != messages[-1]:
        last_msg = messages[-1]
        if re.match(regex_proposition, last_msg.text.lower()):
            rex_msg = rex_mot.search(last_msg.text.lower())
            mot = rex_msg.group(1).replace(" ", "")
            if mot[0] == "_":
                if mot == "_update":
                    print("update")
                else:
                    print("option invalide")

            else:
                ligne = getscore(rex_msg, tableaudujour)
                if ligne is not None:
                    tableaudujour.append(ligne)

    for _ in tableaudujour:
        for i in _:
            print(i, end=" ")
        print()

    time.sleep(0.5)
#       print("id="+str(_id)+"  mot=" + mot+"     "+heure)


#'Parapet\n18:12'

