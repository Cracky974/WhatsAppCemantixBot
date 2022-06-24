import os
import pathlib
import time
from platform import system
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
from selenium.common.exceptions import NoSuchWindowException
from PIL import Image
from io import BytesIO

# variables globales

_conv = "GwoLeo"
DRIVER_PATH = "./chromedriver"
url_cemantix = "https://cemantix.herokuapp.com/"
url_wa = "https://web.whatsapp.com/"
tableaudujour = []
col_id = 0
col_mot = 1
col_heure = 2
col_score = 3
regex_proposition = "^c::(.+):: *\n([0-1]?[0-9]|2[0-3]):([0-5][0-9])$"
rex_mot = re.compile(regex_proposition)

bienvenue = "Le serveur est prêt à prendre vos propositions "
usage = "exemple : c::mot:: option : c::_update:: c::_refresh:: c::_reboot::"
REBOOT_WARNING = "Attention vous allez perdre votre partie, recommencer ? c::_oui:: c::_non::"


# tableau 2D ID | mot | heure
#           1   essai  10:15
#           2   manger 15:12

class LocalStorage:

    def __init__(self, driver) :
        self.driver = driver

    def __len__(self):
        return self.driver.execute_script("return window.localStorage.length;")

    def items(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, items = {}; " \
            "for (var i = 0, k; i < ls.length; ++i) " \
            "  items[k = ls.key(i)] = ls.getItem(k); " \
            "return items; ")

    def keys(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, keys = []; " \
            "for (var i = 0; i < ls.length; ++i) " \
            "  keys[i] = ls.key(i); " \
            "return keys; ")

    def get(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)

    def set(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def has(self, key):
        return key in self.keys()

    def remove(self, key):
        self.driver.execute_script("window.localStorage.removeItem(arguments[0]);", key)

    def clear(self):
        self.driver.execute_script("window.localStorage.clear();")

    def __getitem__(self, key) :
        value = self.get(key)
        if value is None :
          raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return key in self.keys()

    def __iter__(self):
        return self.items().__iter__()

    def __repr__(self):
        return self.items().__str__()



def column(matrix, column):
    return [row[column] for row in matrix]

def init():
    global driver

    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    init_wa() # Ouverture de l'onglet cemantix
    init_cem()

def init_wa():
    global textbox_wa
    global wa_tabs
    # Login
    #       and uncheck the remember check box
    #       (Get your phone ready to read the QR code)
    driver.get(url_wa)
    wa_tabs = driver.current_window_handle
    textbox_wa = select_conv(_conv, driver)

def init_cem():
    global cem_tabs
    global form_guess
    storage = LocalStorage(driver)
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(url_cemantix)
    storage.clear()
    cem_tabs = driver.current_window_handle
    try:
        close_dialog = driver.find_element(By.XPATH, "//*[@id='dialog-close']")
        close_dialog.click()  # pour enlever le popup
    except NoSuchElementException:
        print("Oops, impossible de trouver l'élément X")
    try:
        form_guess = driver.find_element(By.XPATH, "//*[@id='guess']")
        form_guess.click()
        form_guess.clear()
    except NoSuchElementException:
        print("Oops, impossible de trouver l'élément @id='guess'")
        driver.quit()
        init()
    driver.switch_to.window(wa_tabs)




# Creating the driver (browser)
# driver = webdriver.Firefox()


def select_conv(conv : str, driver):


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
    return textbox_wa

init()
#####################################################################################

def sendmessage(message, wa_tab, textbox_wa):
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
        print("Timeout excepetion")
    finally:
        if re.match("Je ne connais pas le mot", driver.find_element(By.ID, "error").text):
            score = -1
            sendmessage("Je ne connais pas le mot", wa_tabs, textbox_wa)
        driver.switch_to.window(wa_tabs)
        return score


def getscore(rex_msg, tableaudujour, textbox_wa=driver.find_element(By.XPATH,
                                                                    "/html/body/div[1]/div/div/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]")) -> dict:
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
    """Copy the Image to Clipboard based on the Platform"""

    if system().lower() == "linux":
        if pathlib.Path(path).suffix in (".PNG", ".png"):
            os.system(f"copyq copy image/png - < {path}")
        elif pathlib.Path(path).suffix in (".jpg", ".JPG", ".jpeg", ".JPEG"):
            os.system(f"copyq copy image/jpeg - < {path}")
        else:
            raise Exception(
                f"File Format {pathlib.Path(path).suffix} is not Supported!"
            )
    elif system().lower() == "windows":
        

        import win32clipboard
        

        image = Image.open(path)
        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
    elif system().lower() == "darwin":
        if pathlib.Path(path).suffix in (".jpg", ".jpeg", ".JPG", ".JPEG"):
            os.system(
                f"osascript -e 'set the clipboard to (read (POSIX file \"{path}\") as JPEG picture)'"
            )
        else:
            raise Exception(
                f"File Format {pathlib.Path(path).suffix} is not Supported!"
            )
    else:
        raise Exception(f"Unsupported System: {system().lower()}")


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
                sendmessage("refresh effectué", wa_tabs, textbox_wa)
            elif mot == "_reboot":
                sendmessage(REBOOT_WARNING,  wa_tabs, textbox_wa)
                msg_in = ""
                msg_out= ""
                while msg_in != "_oui" or msg_out != "_oui" or msg_in != "_non" or msg_out != "_non":
                    msg_in = recup_msgs("in")[-1].text
                    msg_out = recup_msgs("out")[-1].text
                    rex_msg_in = rex_mot.search(msg_in.lower())
                    rex_msg_out = rex_mot.search(msg_out.lower())
                    if rex_msg_in is not None :
                        msg_in = rex_msg_in.group(1).replace(" ", "")
                    if rex_msg_out is not None :
                        msg_out = rex_msg_out.group(1).replace(" ", "")
                    if msg_in == "_non" or msg_out == "_non":
                            break
                    elif msg_in == "_oui" or msg_out == "_oui":
                            driver.switch_to.window(cem_tabs)
                            driver.close()
                            driver.switch_to.window(wa_tabs)
                            init_cem()
                            break
            else:
                if mot != "_oui" or mot != "_non":
                    print("option invalide")
                    sendmessage("option invalide", wa_tabs, textbox_wa)

        else:
            ligne = getscore(rex_msg, tableaudujour, textbox_wa)
            if ligne is not None:
                sendmessage("id :  " + str(ligne["_id"]) + "  mot : " + mot + "   " + str(ligne["score"]), wa_tabs, textbox_wa)
                tableaudujour.append(ligne)
            else:
                sendmessage("mot déjà essayé :", wa_tabs, textbox_wa)
                for _ in tableaudujour:
                    for key, value in _.items():
                        if value == mot:
                            sendmessage("id :  " + str(_["_id"]) + "  mot : " + mot + "   " + str(_["score"]), wa_tabs, textbox_wa)

def recup_msgs(inorout : str)->list:
    if inorout == "in" or inorout == "out":
        try:
            driver.switch_to.window(wa_tabs)
            messages = driver.find_elements(By.XPATH,
                                               "//div[contains(concat(' ',normalize-space(@class),' '),' message-" + inorout + " ')]")

            if messages.__len__() == 0:
                print("Oops, impossible de trouver les messages // messages[]=None")
        except NoSuchWindowException :
            print("Fenetre a été fermé, reinitialation du driver")
            driver.quit()
            init()
        return messages
    else :
        print("inorout != in or out")
        print(inorout)
        return None
################################################################################


sendmessage(bienvenue, wa_tabs, textbox_wa)
sendmessage(usage, wa_tabs, textbox_wa)

last_msg_in = recup_msgs("in")
last_msg_out = recup_msgs("out")

while (1):
    # Selection des messages_in reçu
    messages_in = recup_msgs("in")
    messages_out = recup_msgs("out")
    try:
        if last_msg_in != messages_in[-1]:
            last_msg_in = messages_in[-1]
            try:
                interpreteur(last_msg_in)
            except StaleElementReferenceException:
                print("msg in went wrong")
    except IndexError:
        print("list msg_in index out of range")
    except NameError:
        print("messages_in not defined")
    try:
        if last_msg_out != messages_out[-1]:
            last_msg_out = messages_out[-1]
            try:
                interpreteur(last_msg_out)
            except StaleElementReferenceException:
                print("msg out went wrong")
    except IndexError:
        print("list msg_out index out of range")
    except NameError:
        print("messages_out not defined")


    #   for _ in tableaudujour:
    #       for key, value in _.items():
    #           print(key, ' : ', value)
    #       print()

    time.sleep(0.2)
#       StaleElementReferenceException


# 'Parapet\n18:12'
