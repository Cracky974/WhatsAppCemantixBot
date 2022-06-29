import json
import os
import pathlib
import time
import traceback
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


class LocalStorage:

    def __init__(self, driver):
        self.driver = driver


    def __len__(self):
        return self.driver.execute_script("return window.localStorage.length;")

    def items(self):
        return self.driver.execute_script(
            "var ls = window.localStorage, items = {}; ""for (var i = 0, k; i < ls.length; ++i) ""  items[k = ls.key(i)] = ls.getItem(k); ""return items; ")

    def keys(self):
        return self.driver.execute_script(
            "var ls = window.localStorage, keys = []; ""for (var i = 0; i < ls.length; ++i) ""  keys[i] = ls.key(i); ""return keys; ")

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

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
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


class WhatsappBot:
    driver = None
    textbox_wa = None
    wa_tabs = None
    cem_tabs = None
    form_guess = None
    score = 0
    tableaudujour = []
    last_msg_in = None
    last_msg_out = None
    _conv = ""
    regex_proposition = "(?:.+\n)?c::(.+):: *\n([0-1]?[0-9]|2[0-3]):([0-5][0-9])$"
    rex_mot = None
    DRIVER_PATH = "./chromedriver"
    url_cemantix = "https://cemantix.herokuapp.com/"
    url_wa = "https://web.whatsapp.com/"
    WELCOME = "Le serveur est prêt à prendre vos propositions "
    USAGE = "exemple : c::mot:: option : c::_update:: c::_refresh:: c::_reboot:: c::_reload::"
    REBOOT_WARNING = "Attention vous allez perdre votre partie, recommencer ? c::_oui:: c::_non::"
    PATH_SAVE = ".\save.json"


    def __init__(self, conv: str):
        # self.driver = driver
        service = Service(executable_path=self.DRIVER_PATH)
        self.driver = webdriver.Chrome(service=service)
        self.driver.maximize_window()
        self._conv = conv
        self.rex_mot = re.compile(self.regex_proposition)

        if not os.path.exists(self.PATH_SAVE):
            with open(self.PATH_SAVE, 'w') as file:
                file.write("[]")


    def init_wa(self):

        # Login
        #       and uncheck the remember check box
        #       (Get your phone ready to read the QR code)
        self.driver.get(self.url_wa)
        self.wa_tabs = self.driver.current_window_handle
        self.textbox_wa = self.select_conv(self._conv)
        self.last_msg_in = self.recup_msgs("in")
        self.last_msg_out = self.recup_msgs("out")

    def init_cem(self):

        self.driver = self.driver
        storage = LocalStorage(self.driver)
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(self.url_cemantix)
        storage.clear()
        self.cem_tabs = self.driver.current_window_handle
        try:
            close_dialog = self.driver.find_element(By.XPATH, "//*[@id='dialog-close']")
            close_dialog.click()  # pour enlever le popup
        except NoSuchElementException:
            print("Oops, impossible de trouver l'élément X")
        try:
            self.form_guess = self.driver.find_element(By.XPATH, "//*[@id='guess']")
            self.form_guess.click()
            self.form_guess.clear()
        except NoSuchElementException:
            print("Oops, impossible de trouver l'élément @id='guess'")
            self.driver.quit()
            self.init()
        del storage
        self.driver.switch_to.window(self.wa_tabs)

    def select_conv(self, conv: str):
        # Selection de la conversation Gwoleo
        textbox_wa = None
        self.driver.switch_to.window(self.wa_tabs)
        while textbox_wa is None:
            try:
                _conv = self.driver.find_element(By.XPATH, "//*[@id='pane-side']/div[2]//*[@title='" + conv + "']")
                _conv.click()
                textbox_wa = self.driver.find_element(By.XPATH,
                                                      "/html/body/div[1]/div/div/div[4]/div/footer/div[1]/div/"
                                                      "span[2]/div/div[2]/div[1]/div/div[2]")
            except NoSuchElementException:
                print("Oops, impossible de trouver Gwoleo")
                time.sleep(1)
        return textbox_wa

    def getcolumn(self, matrix, column):
        return [row[column] for row in matrix]

    def sendmessage(self, message):
        self.driver.switch_to.window(self.wa_tabs)
        self.textbox_wa.click()
        self.textbox_wa.clear()
        self.textbox_wa.send_keys(message)

        send_button_wa = WebDriverWait(self.driver, 0.2).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='main']/footer/div[1]/div/span[2]/div/div[2]/div[2]/button"))
        )
        send_button_wa.click()

    def score_proposition_cemantix(self, proposition_gwoleo):

        self.driver.switch_to.window(self.cem_tabs)
        try:
            form_guess = self.form_guess
            form_guess.click()
            form_guess.clear()
            form_guess.send_keys(proposition_gwoleo)
            form_guess.submit()
            time.sleep(0.5)
            element = WebDriverWait(self.driver, 3).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "popup"))
            )
            time.sleep(1)  # attente de l'affichage du score
            self.score = element[2].text

        except TimeoutException:
            self.score = 0
            print("Timeout excepetion")
        finally:
            if re.match("Je ne connais pas le mot", self.driver.find_element(By.ID, "error").text):
                self.score = -1
                self.sendmessage("Je ne connais pas le mot")
            self.driver.switch_to.window(self.wa_tabs)
            return self.score

    def getscore(self, rex_msg) -> dict:

        mot = rex_msg.group(1).replace(" ", "")
        if mot not in self.getcolumn(self.tableaudujour, "mot"):
            heure = rex_msg.group(2)
            minute = rex_msg.group(3)
            time = str(heure) + ":" + str(minute)
            if len(self.tableaudujour) > 0:
                _id = self.tableaudujour[len(self.tableaudujour) - 1]["_id"] + 1
            else:
                _id = 0
            ligne = {"_id": _id, "mot": mot, "time": time, "score": self.score_proposition_cemantix(mot)}

            return ligne
        else:
            return None

    def get_screenshot_update(self) -> None:
        self.driver.switch_to.window(self.cem_tabs)
        guessable = self.driver.find_element(By.ID, "guessable")
        png = self.driver.get_screenshot_as_png()

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

    @staticmethod
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

    def send_copied_image(self):
        self.driver.switch_to.window(self.wa_tabs)
        textbox_wat = self.driver.find_element(By.XPATH, "//*[@title='Type a message']")
        textbox_wat.clear()
        textbox_wat.send_keys(Keys.CONTROL + "v")
        self.driver.implicitly_wait(1)
        # obligé de changer de textbox a cause du changement de whatsapp quand collage d'une image
        #textbox_wat = self.driver.find_element(By.XPATH,
        #                                      "/html/body/div[1]/div/div/div[2]/div[2]/span/div/span/div/div/"
        #                                      "div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[2]")
        # textbox_wat.send_keys(Keys.RETURN)
        send_button_wa = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="app"]'
                           '/div/div/div[2]/div[2]/span/div/span/div/div/div[2]/div/div[2]/div[2]/div/div')))
        send_button_wa.click()

    def refresh_cemantix(self):
        self.driver.switch_to.window(self.cem_tab)
        self.driver.refresh()

    def interpreteur(self, msg):
        # global tableaudujour
        if re.match(self.regex_proposition, msg.text.lower()):
            rex_msg = self.rex_mot.search(msg.text.lower())
            mot = rex_msg.group(1).replace(" ", "")
            if mot[0] == "_":
                if mot == "_update":
                    print("update")
                    self.get_screenshot_update()
                    self.copy_image(r'update.png')
                    self.send_copied_image()
                elif mot == "_refresh":
                    self.refresh_cemantix()
                    self.sendmessage("refresh effectué")
                elif mot == "_reboot":
                    self.rebootgame()
                elif mot == "_reload":
                    self.reload()
                else:
                    self.sendmessage("option invalide")
                    print("option invalide")
            else:
                ligne = self.getscore(rex_msg)
                if ligne is not None:
                    self.watch_for_new_msg()
                    self.sendmessage("id :  " + str(ligne["_id"]) + "  mot : " + mot + "   " + str(ligne["score"]))
                    self.tableaudujour.append(ligne)
                    self.write_json(ligne)
                else:
                    self.sendmessage("mot déjà essayé :")
                    for _ in self.tableaudujour:
                        for key, value in _.items():
                            if value == mot:
                                self.sendmessage("id :  " + str(_["_id"]) + "  mot : " + mot + "   " + str(_["score"]))

    def rebootgame(self):
        self.sendmessage(self.REBOOT_WARNING)
        msg_in = ""
        msg_out = ""
        rex_msg_in = None
        rex_msg_out = None
        self.watch_for_new_msg()
        while msg_in != "_oui" or msg_out != "_oui" or msg_in != "_non" or msg_out != "_non":

            if self.watch_for_new_msg():
                try:
                    msg_in = self.last_msg_in.text
                    rex_msg_in = self.rex_mot.search(msg_in.lower())
                except (IndexError, AttributeError):
                    print("continue")
                try:

                    msg_out = self.last_msg_out.text
                    rex_msg_out = self.rex_mot.search(msg_out.lower())
                except (IndexError, AttributeError):
                    print("continue")
                if rex_msg_in is not None:
                    msg_in = rex_msg_in.group(1).replace(" ", "")
                if rex_msg_out is not None:
                    msg_out = rex_msg_out.group(1).replace(" ", "")

                if msg_in == "_non" or msg_out == "_non":
                    self.sendmessage("annulation")
                    print("annulation")
                    self.watch_for_new_msg()
                    break
                elif msg_in == "_oui" or msg_out == "_oui":
                    self.driver.switch_to.window(self.cem_tabs)
                    self.driver.close()
                    self.driver.switch_to.window(self.wa_tabs)
                    self.init_cem()
                    self.tableaudujour = []
                    with open(self.PATH_SAVE, 'w') as file:
                        file.write("[]")
                    self.sendmessage("reboot effectué")
                    print("reboot effectué")
                    self.watch_for_new_msg()
                    break
                else:
                    print("option invalide choisir _oui ou _non")
                    self.sendmessage("option invalide choisir _oui ou _non")
                    self.watch_for_new_msg()

    def recup_msgs(self, inorout: str):
        if inorout == "in" or inorout == "out":
            try:
                self.driver.switch_to.window(self.wa_tabs)
                messages = self.driver.find_elements(By.XPATH,
                                                     "//div[contains(concat(' ',normalize-space(@class),' '),' message-" + inorout + " ')]")

                if messages.__len__() == 0:
                    print("Oops, impossible de trouver les messages // messages[]=None")
            except NoSuchWindowException:
                print("Fenetre a été fermé, reinitialation du driver")
                self.driver.quit()
                self.__init__(self._conv)
                self.init_wa()  # Ouverture de l'onglet cemantix
                self.init_cem()

            return messages
        else:
            print("inorout != in or out")
            print(inorout)
            return None

    def reload(self):
        self.sendmessage("Chargement, veuillez attendre")
        try:
            with open(self.PATH_SAVE, "r", encoding='utf-8') as json_file:
                self.tableaudujour = json.load(json_file)
            for ligne in self.tableaudujour:
                if int(ligne["score"]) > 0:
                    self.score_proposition_cemantix(ligne["mot"])
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            print("sauvegarde corrompue ou inexistante")
            self.sendmessage("sauvegarde corrompue ou inexistante")
        print("charg sauvegarde ok")
        self.sendmessage("Chargement de la Sauvegarde OK")

    def watch_for_new_msg(self)->bool:
        messages_in = self.recup_msgs("in")
        messages_out = self.recup_msgs("out")
        try:
            if self.last_msg_in != messages_in[-1]:
                self.last_msg_in = messages_in[-1]
                return True
        except IndexError:
            print("list msg_in index out of range")
            traceback.print_exc()
        except NameError:
            print("messages_in not defined")
            traceback.print_exc()
        try:
            if self.last_msg_out != messages_out[-1]:
                self.last_msg_out = messages_out[-1]
                return True
        except IndexError:
            print("list msg_in index out of range")
            traceback.print_exc()
        except NameError:
            print("messages_in not defined")
            traceback.print_exc()
        return False

    def run(self):
        self.init_wa()  # Ouverture de l'onglet cemantix
        self.init_cem()
        self.sendmessage(self.WELCOME)
        self.sendmessage(self.USAGE)

        while 1:
            # Selection des messages_in reçu
            messages_in = self.recup_msgs("in")
            messages_out = self.recup_msgs("out")
            try:
                if self.last_msg_in != messages_in[-1]:
                    self.last_msg_in = messages_in[-1]
                    try:
                        self.interpreteur(self.last_msg_in)
                    except StaleElementReferenceException:
                        print("msg in went wrong")
                        traceback.print_exc()
                        self.textbox_wa = self.select_conv(self._conv)
            except IndexError:
                print("list msg_in index out of range")
                traceback.print_exc()
            except NameError:
                print("messages_in not defined")
                traceback.print_exc()
            try:
                if self.last_msg_out != messages_out[-1]:
                    self.last_msg_out = messages_out[-1]
                    try:
                        self.interpreteur(self.last_msg_out)
                    except StaleElementReferenceException:
                        print("msg out went wrong")
                        traceback.print_exc()
                        self.textbox_wa = self.select_conv(self._conv)

            except IndexError:
                print("list msg_out index out of range")
                traceback.print_exc()
            except NameError:
                print("messages_out not defined")
                traceback.print_exc()

            #   for _ in tableaudujour:
            #       for key, value in _.items():
            #           print(key, ' : ', value)
            #       print()

            time.sleep(0.2)

    @staticmethod
    def write_json(new_data, filename="./save.json"):
        try:
            with open(filename, 'r+', encoding='utf-8') as file:
                # First we load existing data into a dict.
                file_data = json.load(file)
                # Join new_data with file_data
                file_data.append(new_data)
                # Sets file's current position at offset.
                file.seek(0)
                # convert back to json.
                json.dump(file_data, file, indent=4, ensure_ascii=False)
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            with open(filename, 'w') as file:
                file.write("[]")





