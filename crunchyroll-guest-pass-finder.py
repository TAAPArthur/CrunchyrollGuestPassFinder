#!/usr/bin/python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import json
import logging
import re
import sys
import time
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
        timeOfLastCheck = 0
        logging.info("searching for guest passes")

        usedCodes = list(self.findGuestPass())
        logging.info("Assuming %s are already used", usedCodes)
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
    username = password = False
    accountInfo = None
    credentials = None

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", "-a", action="store_const", const=True, default=False, help="Attempt to activate all credentials")
    parser.add_argument("--delay", "-d", type=int, default=CrunchyrollGuestPassFinder.DELAY, help="the delay between refreshing the guest pass page in seconds")
    parser.add_argument("--log-level", default="INFO", choices=logging._levelToName.values(), help="Controls verbosity of logs")
    parser.add_argument("--dry-run", action="store_const", const=True, default=False)
    parser.add_argument("--username", "-u", help="Attempt to activate the specified account; if a password is known it will be used unless -p is explictly specified")
    parser.add_argument("--password", "-p", help="Password for specified username; if not provided will be read from stdin")
    parser.add_argument("--save", "-s", action="store_const", const=True, default=False)
    parser.add_argument("--list-users", action="store_const", const=True, default=False)
    parser.add_argument("-v", "--version", action="version", version="3.0")

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass
    namespace = parser.parse_args()
    if namespace.list_users:
        accountInfo = loadAccountInfo()
        for key in accountInfo.keys():
            print(key)
        exit(0)
    if namespace.auto:
        accountInfo = loadAccountInfo()
        credentials = accountInfo.items()
    CrunchyrollGuestPassFinder.DELAY = namespace.delay
    logging.getLogger().setLevel(namespace.log_level)
    username = namespace.username
    password = namespace.password

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

    if namespace.save:
        with open(path.join(CONFIG_DIR, "accounts.json"), 'w', encoding='utf-8') as f:
            json.dump(accountInfo, f, indent=4)
        exit(0)

    for username, password in credentials:
        crunchyrollGuestPassFinder = CrunchyrollGuestPassFinder(cloudscraper.CloudScraper())
        if crunchyrollGuestPassFinder.login(username, password) and not namespace.dry_run:
            logging.info("logged into %s", username)
            if crunchyrollGuestPassFinder.isAccountNonPremium():
                crunchyrollGuestPassFinder.findGuestPassAndActivateAccount()
            else:
                logging.info("Account '%s' is already premium", username)
