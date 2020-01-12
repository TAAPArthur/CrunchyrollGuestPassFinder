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


class Status(Enum):
    INIT = 61
    LOGIN_FAILED = 62
    LOGGED_IN = 62
    SEARCHING = 63
    ACCOUNT_ACTIVATED = 0
    ACCOUNT_ALREADY_ACTIVATED = 65
    TIMEOUT = 64


CONFIG_DIR = str(Path.home()) + "/.config/crunchyroll-guest-pass-finder/"


class CrunchyrollGuestPassFinder:

    endOfGuestPassThreadPage = "http://www.crunchyroll.com/forumtopic-803801/the-official-guest-pass-thread-read-opening-post-first?pg=last"
    redeemGuestPassPage = "http://www.crunchyroll.com/coupon_redeem?code="
    failedGuestPassRedeemPage = "http://www.crunchyroll.com/coupon_redeem"
    loginPage = "https://www.crunchyroll.com/login"
    homePage = "http://www.crunchyroll.com"
    GUEST_PASS_PATTERN = "[A-Z0-9]{11}"
    timeout = 10
    invalidResponse = "Coupon code not found."

    HEADLESS = True
    DRIVER = False

    KILL_TIME = 36000  # after x seconds the program will quit with exit code 64
    DELAY = 10  # the delay between refreshing the guest pass page

    status = Status.INIT

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
        self.driver.implicitly_wait(self.timeout)
        self.driver.set_page_load_timeout(self.timeout)
        self.startTime = time.time()
        self.username = username
        self.password = password
        self.output("initial status", self.status)

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
            self.saveScreenshot("logged-in-failed.png")
            self.status = Status.LOGIN_FAILED
            return False

        self.status = Status.LOGGED_IN
        return True

    def waitForElementToLoad(self, id):
        element_present = EC.presence_of_element_located((By.ID, id))
        WebDriverWait(self.driver, self.timeout).until(element_present)

    def waitForElementToLoadByClass(self, clazz):
        element_present = EC.presence_of_element_located((By.CLASS_NAME, clazz))
        WebDriverWait(self.driver, self.timeout).until(element_present)

    def isAccountNonPremium(self, init=False):
        try:
            self.waitForElementToLoadByClass("premium")
            return True
        except TimeoutException:
            self.output("Could not find indicator of non-premium account; exiting")
            if init:
                self.status = Status.ACCOUNT_ALREADY_ACTIVATED
            self.saveScreenshot("alreadyPremium")
            return False

    def activateCode(self, code):
        try:
            self.driver.get(self.redeemGuestPassPage + code)

            self.output("currentURL:", self.driver.current_url)
            self.waitForElementToLoad("couponcode_redeem_form")
            self.driver.find_element_by_id("couponcode_redeem_form").submit()

            if not self.isAccountNonPremium():
                self.postTakenGuestPass(code)
                self.output("found guest pass %s; exiting" % str(code))
                self.status = Status.ACCOUNT_ACTIVATED
                return code
            self.output("URL after submit:", self.driver.current_url)
        except TimeoutException:
            traceback.print_exc(2)
            pass
        return None

    def startFreeAccess(self):
        count = -1
        usedCodes = []
        timeOfLastCheck = 0
        self.status = Status.SEARCHING
        if not self.isAccountNonPremium(True):
            return None
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
                    self.status = Status.TIMEOUT
                    return None

                for code in unusedGuestCodes:
                    if self.activateCode(code):
                        return code
                    usedCodes.append(code)

                if(len(unusedGuestCodes)):  # only check if we just attempted
                    if not self.isAccountNonPremium():
                        self.output("currentURL:", self.driver.current_url)
                        self.status = Status.ACCOUNT_ACTIVATED
                        return None
                time.sleep(self.DELAY)
            except TimeoutException:
                pass
            except BrokenPipeError:
                traceback.print_exc(2)

    def postTakenGuestPass(self, guestPass):
        try:
            self.output("attempting to post that guest pass was taken")
            self.driver.get(self.endOfGuestPassThreadPage)
            self.driver.find_element_by_id("newforumpost").send_keys(guestPass + " has been taken.\nThanks")
            self.driver.find_element_by_name("post_btn").click()
        except TimeoutException:
            self.output("failed to post guest pass")

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

    def getStatus(self):
        return self.status.value

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


if __name__ == "__main__":
    DATE_FORMAT = "%y/%m/%d"
    DRY_RUN = 0
    username = password = False
    accountInfo = []
    shortargs = "aghvk:mp:u:d:"
    longargs = ["graphical", "help", "version", "kill-time=", "config-dir=", "delay=", "auto", "dry-run", "driver=", "username=", "password="]
    optlist, args = getopt.getopt(sys.argv[1:], shortargs, longargs)
    for opt, value in optlist:
        if opt == "-a" or opt == "--auto":
            try:
                with safeOpen(path.join(CONFIG_DIR, "accounts.json")) as jsonFile:
                    accounts = list(filter(lambda x: x.get("Active", 1), json.load(jsonFile)))
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                print("Add account data to {}".format(path.join(CONFIG_DIR, "accounts.json")))
                exit(2)
            accountInfo += [(account["Username"], account["Password"]) for account in accounts]
        elif opt == "-p" or opt == "--password":
            password = value
        elif opt == "-u" or opt == "--username":
            username = value
        elif opt == "--driver":
            CrunchyrollGuestPassFinder.DRIVER = value
        elif opt == "-g" or opt == "--graphical":
            CrunchyrollGuestPassFinder.HEADLESS = False
        elif opt == "-k" or opt == "--kill-time":
            CrunchyrollGuestPassFinder.KILL_TIME = int(value)
        elif opt == "-d" or opt == "--delay":
            CrunchyrollGuestPassFinder.DELAY = int(value)
        elif opt == "--config-dir":
            CONFIG_DIR = value
        elif opt == "--dry-run":
            DRY_RUN = 1
        elif opt == "-v" or opt == "--version":
            printVersion()
            exit(0)
        elif opt == "-h" or opt == "--help":
            printHelp()
            exit(0)
        else:
            printHelp()
            raise ValueError("Unknown argument: ", opt)

    if not accountInfo:
        if not username:
            username = input("Username:")
        if not password:
            try:
                with safeOpen(path.join(CONFIG_DIR, "accounts.json")) as jsonFile:
                    row = next(filter(lambda x: x.get("Username", 0) == username, json.load(jsonFile)), None)
                    if row:
                        password = row["Password"]
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                pass
            if not password:
                password = input("Password:")
        accountInfo.append(username, password)

    if not path.exists(CONFIG_DIR):
        print("WARNING the dir specified does not exists:", CONFIG_DIR)
        mkdir(CONFIG_DIR)

    for username, password in accountInfo:
        crunchyrollGuestPassFinder = CrunchyrollGuestPassFinder(username, password)
        if crunchyrollGuestPassFinder.login() and not DRY_RUN:
            crunchyrollGuestPassFinder.startFreeAccess()
        crunchyrollGuestPassFinder.close()
        print("status = %d" % crunchyrollGuestPassFinder.getStatus())

    exit(crunchyrollGuestPassFinder.getStatus())
