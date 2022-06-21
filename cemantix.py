import time
import re

from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from PIL import Image
from io import BytesIO
from simon.accounts.pages import LoginPage
import win32clipboard

# variables globales

_conv = "William Gougam"
url_cemantix = "https://cemantix.herokuapp.com/"
tableaudujour = []
col_id = 0
col_mot = 1
col_heure = 2
col_score = 3
regex_proposition = "^c::(.+):: *\n([0-1]?[0-9]|2[0-3]):([0-5][0-9])$"
rex_mot = re.compile(regex_proposition)
last_msg_in = None
last_msg_out = None
bienvenue = "Le serveur est prêt à prendre vos propositions "
usage = "exemple : c::mot:: option : c::_update:: c::_refresh::"


# tableau 2D ID | mot | heure
#           1   essai  10:15
#           2   manger 15:12


def column(matrix, column):
    return [row[column] for row in matrix]

def init():
    global driver
    global wa_tabs
    global textbox_wa
    service = Service(executable_path="Z:\Progra\python\WAcemantix\chromedriver.exe")
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    # Login
    #       and uncheck the remember check box
    #       (Get your phone ready to read the QR code)
    login_page = LoginPage(driver)
    login_page.load()
    wa_tabs = driver.current_window_handle
    time.sleep(1)
    select_conv(_conv, driver)


init()

def select_conv(conv : str, driver ):

    # Selection de la conversation Gwoleo
    textbox_wa = None
    while textbox_wa is None:
        try:
            _conv = driver.find_element(By.XPATH, "//*[@id='pane-side']/div[2]//*[@title='" + conv + "']")
            _conv.click()
            textbox_wa = driver.find_element(By.XPATH,
                                             "/html/body/div[1]/div/div/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]")
        except NoSuchElementException:
            print("Oops, impossible de trouver Gwoleo")
            time.sleep(1)



#####################################################################################

def sendmessage(message, wa_tab, textbox_wa=driver.find_element(By.XPATH,
                                                                "/html/body/div[1]/div/div/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]")):
    driver.switch_to.window(wa_tab)
    textbox_wa.click()
    textbox_wa.clear()
    textbox_wa.send_keys(message)

    send_button_wa = WebDriverWait(driver, 0.2).until(
        EC.presence_of_element_located((By.XPATH, "//*[@id='main']/footer/div[1]/div/span[2]/div/div[2]/div[2]/button"))
    )
    send_button_wa.click()


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
        time.sleep(1)  # attente de l'affichage du score
        score = element[2].text

    except TimeoutException:
        score = 0
    finally:
        if re.match("Je ne connais pas le mot", driver.find_element(By.ID, "error").text):
            score = -1
            sendmessage("Je ne connais pas le mot", wa_tabs)
        driver.switch_to.window(wa_tabs)
        return (score)


def getscore(rex_msg, tableaudujour, textbox_wa=driver.find_element(By.XPATH,
                                                                    "/html/body/div[1]/div/div/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]")):
    mot = rex_msg.group(1).replace(" ", "")
    if mot not in column(tableaudujour, "mot"):
        heure = rex_msg.group(2)
        minute = rex_msg.group(3)
        time = str(heure) + ":" + str(minute)
        if len(tableaudujour) > 0:
            _id = tableaudujour[len(tableaudujour) - 1]["_id"] + 1
        else:
            _id = 0
        ligne = {"_id": _id, "mot": mot, "time": time, "score": score_proposition_cemantix(mot)}
        #   driver.switch_to.window(wa_tabs)
        #   textbox_wa.clear()
        #   textbox_wa.send_keys("id :  " +str(_id ) +"  mot : " + mot +"   " +str(score))
        #   textbox_wa.send_keys(Keys.RETURN)
        return ligne
    else:
        return None


def get_screenshot_update():
    driver.switch_to.window(cem_tabs)
    guessable = driver.find_element(By.ID, "guessable")
    png = driver.get_screenshot_as_png()

    location = guessable.location
    size = guessable.size
    im = Image.open(BytesIO(png))  # uses PIL library to open image in memory
    maxHeight = 527  # taille pour 20guesse+tableau
    if size['height'] > maxHeight:
        size['height'] = maxHeight

    left = location['x']
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']

    im = im.crop((left, top, right, bottom))  # defines crop points
    im.save('update.png')
    # im.save('screenshot.png') # saves new cropped image


def copy_image(path: str) -> None:
    image = Image.open(path)
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def send_copied_image(wa_tab, textbox_wat=driver.find_element(By.XPATH, "//*[@title='Type a message']")):
    driver.switch_to.window(wa_tab)
    textbox_wat.clear()
    textbox_wat.send_keys(Keys.CONTROL + "v")
    driver.implicitly_wait(1)
    # obligé de changer de textbox a cause du changement de whatsapp quand collage d'une image
    textbox_wat = driver.find_element(By.XPATH,
                                      "/html/body/div[1]/div/div/div[2]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[2]")
    textbox_wat.send_keys(Keys.RETURN)


def refresh_cemantix(cem_tab, driver):
    driver.switch_to.window(cem_tab)
    driver.refresh()


def interpreteur(msg):
    global tableaudujour
    if re.match(regex_proposition, msg.text.lower()):
        rex_msg = rex_mot.search(msg.text.lower())
        mot = rex_msg.group(1).replace(" ", "")
        if mot[0] == "_":
            if mot == "_update":
                print("update")
                get_screenshot_update()
                copy_image(r'update.png')
                send_copied_image(wa_tabs)
            elif mot == "_refresh":
                refresh_cemantix(cem_tabs, driver)
                sendmessage("refresh effectué", wa_tabs)
            else:
                print("option invalide")
                sendmessage("option invalide", wa_tabs)

        else:
            ligne = getscore(rex_msg, tableaudujour, textbox_wa)
            if ligne is not None:
                sendmessage("id :  " + str(ligne["_id"]) + "  mot : " + mot + "   " + str(ligne["score"]), wa_tabs)
                tableaudujour.append(ligne)
            else:
                sendmessage("mot déjà essayé :", wa_tabs)
                for _ in tableaudujour:
                    for key, value in _.items():
                        if value == mot:
                            sendmessage("id :  " + str(_["_id"]) + "  mot : " + mot + "   " + str(_["score"]), wa_tabs)


################################################################################


# Ouverture de l'onglet cemantix
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[1])
driver.get(url_cemantix)
cem_tabs = driver.current_window_handle

try:
    close_dialog = driver.find_element(By.XPATH, "//*[@id='dialog-close']")
    close_dialog.click()  # pour enlever le popup
except NoSuchElementException:
    print("Oops, impossible de trouver l'élément X")

form_guess = driver.find_element(By.XPATH, "//*[@id='guess']")
form_guess.click()
form_guess.clear()
driver.switch_to.window(wa_tabs)
driver.switch_to.window(wa_tabs)
sendmessage(bienvenue, wa_tabs, textbox_wa)
sendmessage(usage, wa_tabs, textbox_wa)
try:
    messages_in = driver.find_elements(By.XPATH,
                                       "//div[contains(concat(' ',normalize-space(@class),' '),' message-in ')]")
    if messages_in.__len__() == 0:
        print("Oops, impossible de trouver les messages_in")
    else:
        last_msg_in = messages_in[-1]

    messages_out = driver.find_elements(By.XPATH,
                                        "//div[contains(concat(' ',normalize-space(@class),' '),' message-out ')]")
    if messages_out.__len__() == 0:
        print("Oops, impossible de trouver les messages_out")
    else:
        last_msg_out = messages_out[-1]

except NoSuchElementException:
    print("Oops, impossible de trouver les messages_in")

while (1):
    # Selection des messages_in reçu
    try:
        driver.switch_to.window(wa_tabs)
        messages_in = driver.find_elements(By.XPATH,
                                           "//div[contains(concat(' ',normalize-space(@class),' '),' message-in ')]")
        messages_out = driver.find_elements(By.XPATH,
                                            "//div[contains(concat(' ',normalize-space(@class),' '),' message-out ')]")
        if messages_in.__len__() == 0 or messages_out.__len__() == 0:
            print("Oops, impossible de trouver les messages // messages[]=None")

    except NoSuchElementException:
        print("Oops, impossible de trouver les messages")
    try:
        if last_msg_in != messages_in[-1]:
            last_msg_in = messages_in[-1]
            try:
                interpreteur(last_msg_in)
            except StaleElementReferenceException:
                print("msg in went wrong")

        if last_msg_out != messages_out[-1]:
            last_msg_out = messages_out[-1]
            try:
                interpreteur(last_msg_out)
            except StaleElementReferenceException:
                print("StaleElementReferenceException")
    except NameError:
        print("messages not defined")

    #   for _ in tableaudujour:
    #       for key, value in _.items():
    #           print(key, ' : ', value)
    #       print()

    time.sleep(0.2)
#       StaleElementReferenceException


# 'Parapet\n18:12'
