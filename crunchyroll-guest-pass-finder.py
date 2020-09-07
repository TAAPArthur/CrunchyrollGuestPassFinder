#!/usr/bin/python3

import getopt
import json
import logging
import re
import sys
import time
import traceback
from datetime import datetime, timedelta
from enum import Enum
from os import mkdir, path
from pathlib import Path
from random import shuffle

import cloudscraper
from bs4 import BeautifulSoup

CONFIG_DIR = str(Path.home()) + "/.config/crunchyroll-guest-pass-finder/"


class CrunchyrollGuestPassFinder():

    endOfGuestPassThreadPage = "http://www.crunchyroll.com/forumtopic-803801/the-official-guest-pass-thread-read-opening-post-first?pg=last"
    redeemGuestPassPage = "http://www.crunchyroll.com/coupon_redeem?code="
    homePage = "http://www.crunchyroll.com"
    GUEST_PASS_PATTERN = "[A-Z0-9]{11}"

    KILL_TIME = 36000  # after x seconds the program will quit with exit code 64
    DELAY = 10  # the delay between refreshing the guest pass page

    start_session_url = 'https://api.crunchyroll.com/start_session.0.json'
    login_url = 'https://api.crunchyroll.com/login.0.json'
    api_auth_url = 'https://api-manga.crunchyroll.com/cr_authenticate?session_id={}&version=0&format=json'

    _access_token = 'WveH9VkPLrXvuNm'
    _access_type = 'com.crunchyroll.crunchyroid'

    def __init__(self, session):
        self.session = session

    def _get_session_id(self):
        data = self.session.post(
            self.start_session_url,
            data={
                'device_id': '1234567',
                'device_type': self._access_type,
                'access_token': self._access_token,
            }
        ).json()['data']
        return data['session_id']

    def login(self, username, password):
        self.session_id = self._get_session_id()

        login = self.session.post(self.login_url,
                                  data={
                                      'session_id': self.session_id,
                                      'account': username,
                                      'password': password
                                  }).json()
        if 'data' in login:
            return True
        logging.info("Failed to login to %s", username)
        return False

    def isAccountNonPremium(self):
        r = self.session.get(self.api_auth_url.format(self.session_id))
        return not r.json()['data']["user"]['premium']

    def get_from_data(self, url, formClassName):
        r = self.session.get(url)
        soup = BeautifulSoup(r.content, "lxml")
        form = soup.find("form", {"id": formClassName})
        data = {}

        for child in form.findAll("input"):
            if child.has_attr("name"):
                data[child["name"]] = child["value"]

        url = form["action"]
        if url[0] == "/":
            url = self.homePage + url
        logging.debug("From url: %s From data: %s", url, data)
        return url, data

    def activateCode(self, code):
        action, data = self.get_from_data(self.redeemGuestPassPage + code, "couponcode_redeem_form")
        r = self.session.post(action, data=data)

    def findGuestPassAndActivateAccount(self):
        count = -1
        usedCodes = []
        timeOfLastCheck = 0
        logging.info("searching for guest passes")
        startTime = time.time()
        while True:
            count += 1
            guestCodes = self.findGuestPass()

            unusedGuestCodes = [x for x in guestCodes if x not in usedCodes]

            if len(unusedGuestCodes) > 0:
                logging.info("Trial %d: found %d codes %s; %d others have been used: %s", count, len(unusedGuestCodes), unusedGuestCodes, len(usedCodes), usedCodes)
                timeOfLastCheck = time.time()
                shuffle(unusedGuestCodes)
            elif time.time() - timeOfLastCheck > 600:
                logging.info("Trial %d", count)
                timeOfLastCheck = time.time()

            if time.time() - startTime >= self.KILL_TIME:
                return None
            for code in unusedGuestCodes:
                logging.info("Attempting to use code: %s", code)
                self.activateCode(code)
                if not self.isAccountNonPremium():
                    self.postTakenGuestPass(code)
                    return code
                usedCodes.append(code)
            time.sleep(self.DELAY)

    def postTakenGuestPass(self, guestPass):
        logging.info("Attempting to post that guest pass was taken")
        action, data = self.get_from_data(self.endOfGuestPassThreadPage, "RpcApiForum_CreatePost")
        data["newforumpost"] = guestPass + " has been taken.\nThanks"
        r = self.session.post(action, data=data)

    def findGuestPass(self):
        guestCodes = set()
        r = self.session.get(self.endOfGuestPassThreadPage)
        soup = BeautifulSoup(r.content, "lxml")
        messages = soup.findAll("div", {"class": "showforumtopic-message-contents-text"})
        for message in messages:
            matches = re.findall(self.GUEST_PASS_PATTERN, message.getText(), re.M)
            if matches:
                for n in range(len(matches)):
                    if matches[n] not in guestCodes:
                        guestCodes.add(matches[n])
        return guestCodes


def safeOpen(fileName):
    mode = "r" if path.exists(fileName) else "a+"
    return open(fileName, mode)


def printHelp():
    print(
        """
Usage: crunchyroll-guest-pass-finder [arg]
Fishes for Crunchyroll guest passes

If username/password is not specified, the user will be prompted to enter them

Args:
    --auto, -a                  Load the username/password from accounts.json in CONFIG_DIR
    --config-dir                The location on the config files
    --delay, -d                 How often to rescan the guest pass page
    --dry-run                   Login but don't do anything
    --help, -h                  Prints this help message
    --log-level                 Controls how verbose the loggin is
    --killtime, -k              How much time in seconds until the programs kills itself
    --password, -p              Specifies the password to use
    --username, -u              Specifies the username to use
    --version, -v               Prints the version

"""
    )


def printVersion():
    print(3.0)


def getAccountPath():
    return path.join(CONFIG_DIR, "accounts.json")


def loadAccountInfo():
    accountInfo = {}
    try:
        with safeOpen(getAccountPath()) as jsonFile:
            accounts = json.load(jsonFile)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        logging.error("Add account data to {}".format(path.join(CONFIG_DIR, "accounts.json")))
        exit(2)
    if isinstance(accounts, list):
        accountInfo = {account["Username"]: account["Password"] for account in accounts}
    else:
        accountInfo = accounts
    return accountInfo


if __name__ == "__main__":
    DATE_FORMAT = "%y/%m/%d"
    dry_run = 0
    save_account_info = False
    username = password = False
    accountInfo = None
    credentials = None

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    shortargs = "aghsvk:mp:u:d:t:"
    longargs = ["account-file", "auto", "config-dir=", "delay=", "dry-run", "help", "kill-time=", "log-level=", "password=", "save", "timeout=", "username=", "users", "version"]
    optlist, args = getopt.getopt(sys.argv[1:], shortargs, longargs)
    for opt, value in optlist:
        if opt == "--account-file":
            print(getAccountPath())
            exit(0)
        if opt == "--auto" or opt == "-a":
            accountInfo = loadAccountInfo()
            credentials = accountInfo.items()
        elif opt == "--config-dir":
            CONFIG_DIR = value
        elif opt == "--log-level":
            logging.getLogger().setLevel(value.upper())
        elif opt == "--delay" or opt == "-d":
            CrunchyrollGuestPassFinder.DELAY = int(value)
        elif opt == "--dry-run":
            dry_run = 1
        elif opt == "--help" or opt == "-h":
            printHelp()
            exit(0)
        elif opt == "--kill-time" or opt == "-k":
            CrunchyrollGuestPassFinder.KILL_TIME = int(value)
        elif opt == "--password" or opt == "-p":
            password = value
        elif opt == "--save" or opt == "-s":
            accountInfo = loadAccountInfo()
            save_account_info = True
        elif opt == "--username" or opt == "-u":
            username = value
        elif opt == "--users" or opt == "-u":
            accountInfo = loadAccountInfo()
            print(accountInfo.keys())
            exit(0)
        elif opt == "--version" or opt == "-v":
            printVersion()
            exit(0)
        else:
            printHelp()
            raise ValueError("Unknown argument: ", opt)

    if not credentials:
        if not username:
            username = input("Username:")
        if not password:
            if not accountInfo:
                accountInfo = loadAccountInfo()
            password = accountInfo.get(username, None)
            if not password:
                password = input("Password:")
        credentials = [(username, password)]

    if not path.exists(CONFIG_DIR):
        logging.warning("the dir specified does not exists: %s", CONFIG_DIR)
        mkdir(CONFIG_DIR)

    if save_account_info:
        with open(path.join(CONFIG_DIR, "accounts.json"), 'w', encoding='utf-8') as f:
            json.dump(accountInfo, f, indent=4)
        exit(0)

    for username, password in credentials:
        crunchyrollGuestPassFinder = CrunchyrollGuestPassFinder(cloudscraper.CloudScraper())
        if crunchyrollGuestPassFinder.login(username, password) and not dry_run:
            logging.info("logged into %s", username)
            if crunchyrollGuestPassFinder.isAccountNonPremium():
                crunchyrollGuestPassFinder.findGuestPassAndActivateAccount()
            else:
                logging.info("Account '%s' is already premium", username)
