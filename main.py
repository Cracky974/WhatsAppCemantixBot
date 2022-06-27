from WhatsAppBot import WhatsappBot
import time
# variables globales
conv = "William Gougam"

# tableau 2D ID | mot | heure
#           1   essai  10:15
#           2   manger 15:12


################################################################################
from selenium.common.exceptions import StaleElementReferenceException

wabot = WhatsappBot(conv)

wabot.sendmessage(wabot.WELCOME)
wabot.sendmessage(wabot.USAGE)

last_msg_in = wabot.recup_msgs("in")
last_msg_out = wabot.recup_msgs("out")

while (1):
    # Selection des messages_in reçu
    messages_in = wabot.recup_msgs("in")
    messages_out = wabot.recup_msgs("out")
    try:
        if last_msg_in != messages_in[-1]:
            last_msg_in = messages_in[-1]
            try:
                wabot.interpreteur(last_msg_in)
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
                wabot.interpreteur(last_msg_out)
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
