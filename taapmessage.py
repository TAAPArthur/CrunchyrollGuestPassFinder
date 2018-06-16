#!/usr/bin/env python3

from telegram.ext import Updater
from telegram.ext import CommandHandler
import telegram
import sys

CHAT_ID=None
TOKEN=None
updater = None

def start(bot, update):
        print(update.message.chat_id)
        bot.sendMessage(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

def sendMessage(message,id=CHAT_ID):
        bot = telegram.Bot(token=TOKEN)
        bot.send_message(chat_id=id,text=message)

if __name__ == "__main__":
        if len(sys.argv)==4:
            print(sys.argv)
            #updater = Updater(token=sys.argv[1])
            #dispatcher = updater.dispatcher
            TOKEN=sys.argv[1]
            sendMessage(sys.argv[3],sys.argv[2])
        else:
            print("not enough args")

