#!/usr/bin/python3

from datetime import datetime, timedelta
from enum import Enum
from os import path, mkdir
from pathlib import Path
from random import shuffle
import getopt
import json
import re
import sys
import time
import traceback

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


CONFIG_DIR = str(Path.home()) + "/.config/crunchyroll-guest-pass-finder/"


class CrunchyrollGuestPassFinder:

    endOfGuestPassThreadPage = "http://www.crunchyroll.com/forumtopic-803801/the-official-guest-pass-thread-read-opening-post-first?pg=last"
    redeemGuestPassPage = "http://www.crunchyroll.com/coupon_redeem?code="
    failedGuestPassRedeemPage = "http://www.crunchyroll.com/coupon_redeem"
    loginPage = "https://www.crunchyroll.com/login"
    homePage = "http://www.crunchyroll.com"
    GUEST_PASS_PATTERN = "[A-Z0-9]{11}"

    HEADLESS = True
    DRIVER = False

    PAGE_LOAD_TIMEOUT = 20
    KILL_TIME = 36000  # after x seconds the program will quit with exit code 64
    DELAY = 10  # the delay between refreshing the guest pass page

    def __init__(self, username, password):
        self.output("starting bot")
        options = Options()
        if self.isHeadless():
            options.add_argument("--headless")
        if not self.DRIVER:
            firefox_profile = webdriver.FirefoxProfile()
            firefox_profile.set_preference('permissions.default.image', 2)
            firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
            self.driver = webdriver.Firefox(service_log_path="/dev/null", options=options, firefox_profile=firefox_profile)
        else:
            self.driver = getattr(webdriver, self.DRIVER)(service_log_path="/dev/null", options=options)
        self.driver.implicitly_wait(self.PAGE_LOAD_TIMEOUT)
        self.driver.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)
        self.startTime = time.time()
        self.username = username
        self.password = password

    def isHeadless(self):
        return self.HEADLESS

    def isTimeout(self):
        if time.time() - self.startTime >= self.KILL_TIME:
            return True
        else:
            return False

    def login(self):
        self.output("attempting to login to " + self.username)
        self.driver.get(self.loginPage)
        self.driver.find_element_by_id("login_form_name").send_keys(self.username)
        self.driver.find_element_by_id("login_form_password").send_keys(self.password)
        self.driver.find_element_by_class_name("type-primary").click()

        self.output("logged in")
        self.output(self.driver.current_url)
        if self.driver.current_url == self.loginPage:
            return False

        return True

    def waitForElementToLoad(self, id):
        element_present = EC.presence_of_element_located((By.ID, id))
        WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(element_present)

    def waitForElementToLoadByClass(self, clazz):
        element_present = EC.presence_of_element_located((By.CLASS_NAME, clazz))
        WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(element_present)

    def isAccountNonPremium(self):
        try:
            self.waitForElementToLoad("header_try_premium_free")
            return True
        except TimeoutException:
            self.output("Could not find indicator of non-premium account {}; exiting".format(self.username))
            return False

    def activateCode(self, code):
        try:
            self.driver.get(self.redeemGuestPassPage + code)

            self.output("currentURL:", self.driver.current_url)
            self.waitForElementToLoad("couponcode_redeem_form")
            self.driver.find_element_by_id("couponcode_redeem_form").submit()

            return self.postTakenGuestPass(code)
        except TimeoutException:
            traceback.print_exc(2)
            pass
        return None

    def findGuestPassAndActivateAccount(self):
        count = -1
        usedCodes = []
        timeOfLastCheck = 0
        self.output("searching for guest passes")
        while True:
            count += 1
            try:
                guestCodes = self.findGuestPass()

                unusedGuestCodes = [x for x in guestCodes if x not in usedCodes]

                if len(unusedGuestCodes) > 0:
                    self.output("Trial ", count, ": found ", len(unusedGuestCodes), " codes: ", unusedGuestCodes, "; ", len(usedCodes), " others have been used: ", usedCodes)
                    timeOfLastCheck = time.time()
                    shuffle(unusedGuestCodes)
                elif time.time() - timeOfLastCheck > 600:
                    self.output("Trial ", count)
                    sys.stdout.flush()
                    timeOfLastCheck = time.time()
                if self.isTimeout():
                    return None
                for code in unusedGuestCodes:
                    if self.activateCode(code):
                        return code
                    usedCodes.append(code)
                time.sleep(self.DELAY)
            except TimeoutException:
                self.output("got timeout")
                pass
            except BrokenPipeError:
                traceback.print_exc(2)

    def postTakenGuestPass(self, guestPass):
        try:
            self.output("attempting to post that guest pass was taken")
            self.driver.get(self.endOfGuestPassThreadPage)
            self.driver.find_element_by_id("newforumpost").send_keys(guestPass + " has been taken.\nThanks")

            if not self.isAccountNonPremium():
                self.driver.find_element_by_name("post_btn").click()
                self.output("found guest pass %s; exiting" % str(guestPass))
                return guestPass
            else:
                self.output("Aborting; our account is still not active")
        except TimeoutException:
            self.output("failed to post guest pass")
        return False

    def findGuestPass(self):
        guestCodes = []
        inValidGuestCodes = []
        try:
            self.driver.get(self.endOfGuestPassThreadPage)
            classes = self.driver.find_elements_by_class_name("showforumtopic-message-contents-text")
            for i in range(len(classes)):

                matches = re.findall(self.GUEST_PASS_PATTERN, classes[i].text, re.M)

                if matches:
                    for n in range(len(matches)):
                        if matches[n] not in guestCodes:

                            guestCodes.append(matches[n])
                        elif matches[n] not in inValidGuestCodes:
                            inValidGuestCodes.append(matches[n])
        except TimeoutException:
            traceback.print_exc(2)
        for i in range(len(inValidGuestCodes)):
            guestCodes.remove(inValidGuestCodes[i])

        return guestCodes

    def saveScreenshot(self, fileName="screenshot.png"):
        #fileName += ".png"
        #self.output("saving screen shot to ", fileName)
        #self.driver.save_screenshot(CONFIG_DIR + fileName)
        pass

    def output(self, *message):

        time = datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ":"
        formattedMessage = message[0]
        for i in range(1, len(message)):
            formattedMessage += str(message[i])
        print(time, formattedMessage, flush=True)

    def close(self):
        self.output("exiting")
        if self.isHeadless():
            self.driver.quit()


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
    --driver                    Specifies the name of the driver to use (Firefox (default) or PhantomJS)
    --dry-run                   Login but don't do anything
    --graphical, -g             Runs in a non-headless manner. Useless if the driver is PhantomJS
    --help, -h                  Prints this help message
    --killtime, -k              How much time in seconds until the programs kills itself
    --password, -p              Specifies the password to use
    --username, -u              Specifies the username to use
    --version, -v               Prints the version

"""
    )


def printVersion():
    print(2.1)


def getAccountPath():
    return path.join(CONFIG_DIR, "accounts.json")


def loadAccountInfo():
    accountInfo = {}
    try:
        with safeOpen(getAccountPath()) as jsonFile:
            accounts = json.load(jsonFile)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        print("Add account data to {}".format(path.join(CONFIG_DIR, "accounts.json")))
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
    shortargs = "aghsvk:mp:u:d:t:"
    longargs = ["account-file", "auto", "config-dir=", "delay=", "driver=", "dry-run", "graphical", "help", "kill-time=", "password=", "save", "timeout=", "username=", "users", "version"]
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
        elif opt == "--delay" or opt == "-d":
            CrunchyrollGuestPassFinder.DELAY = int(value)
        elif opt == "--driver":
            CrunchyrollGuestPassFinder.DRIVER = value
        elif opt == "--dry-run":
            dry_run = 1
        elif opt == "--graphical" or opt == "-g":
            CrunchyrollGuestPassFinder.HEADLESS = False
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
        elif opt == "--timeout" or opt == "-t":
            CrunchyrollGuestPassFinder.PAGE_LOAD_TIMEOUT = int(value)
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
        print("WARNING the dir specified does not exists:", CONFIG_DIR)
        mkdir(CONFIG_DIR)

    if save_account_info:
        with open(path.join(CONFIG_DIR, "accounts.json"), 'w', encoding='utf-8') as f:
            json.dump(accountInfo, f, indent=4)
        exit(0)

    for username, password in credentials:
        crunchyrollGuestPassFinder = CrunchyrollGuestPassFinder(username, password)
        if crunchyrollGuestPassFinder.login() and not dry_run:
            if crunchyrollGuestPassFinder.isAccountNonPremium():
                crunchyrollGuestPassFinder.findGuestPassAndActivateAccount()
        crunchyrollGuestPassFinder.close()
