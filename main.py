from WhatsAppBot import WhatsappBot
import sys

CONV = ""

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("Mauvais utilisation")
        print("./main.py conversation")
        exit()
    else:
        CONV = sys.argv[1]
    wabot = WhatsappBot(CONV)
    wabot.run()

#       StaleElementReferenceException


# 'Parapet\n18:12'

# tableau 2D ID | mot | heure
#           1   essai  10:15
#           2   manger 15:12

################################################################################
