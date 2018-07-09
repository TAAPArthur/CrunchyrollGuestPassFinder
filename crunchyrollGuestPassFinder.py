import re
import sys
import time
import datetime
from selenium import webdriver

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import traceback
from selenium.webdriver.firefox.options import Options
from enum import Enum

from pathlib import Path
from random import shuffle

CONFIG_DIR=str(Path.home())+"/.config/taapcrunchyroll-bot/"
class Status(Enum):
    INIT=61
    LOGIN_FAILED=62
    LOGGED_IN=62
    SEARCHING=63
    ACCOUNT_ACTIVATED=0
    ACCOUNT_ALREADY_ACTIVATED=65
    TIMEOUT=64

class CrunchyrollGuestPassFinder:
    endOfGuestPassThreadPage = "http://www.crunchyroll.com/forumtopic-803801/the-official-guest-pass-thread-read-opening-post-first?pg=last"
    redeemGuestPassPage = "http://www.crunchyroll.com/coupon_redeem?code="
    failedGuestPassRedeemPage="http://www.crunchyroll.com/coupon_redeem"
    loginPage = "https://www.crunchyroll.com/login"
    homePage = "http://www.crunchyroll.com"
    GUEST_PASS_PATTERN = "[A-Z0-9]{11}"
    timeout = 20
    invalidResponse = "Coupon code not found."
    
    KILL_TIME = 43200 # after x seconds the program will quit with exit code 64
    DELAY = 10 # the delay between refreshing the guest pass page
    
    status=Status.INIT
    
    def __init__(self,username,password):
        self.output("starting bot")
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference('permissions.default.image', 2)
        firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Firefox(log_path="/dev/null", firefox_options=options,firefox_profile=firefox_profile)
        self.driver.implicitly_wait(self.timeout)
        self.startTime = time.time()
        self.username = username
        self.password = password
        
    
    def isTimeout(self):
        if time.time() - self.startTime >= self.KILL_TIME:
            return True
        else:
            return False
    def login(self):
        self.output("attemting to login to "+self.username)
        self.driver.get(self.loginPage)
        self.driver.find_element_by_id("login_form_name").send_keys(self.username)
        self.driver.find_element_by_id("login_form_password").send_keys(self.password)
        self.driver.find_element_by_class_name("type-primary").click()
        self.saveScreenshot("loggedIn.png~")
        self.output("logged in")
        self.output(self.driver.current_url)
        if self.driver.current_url==self.loginPage:
            self.status=Status.LOGIN_FAILED
            return False
        
        self.status=Status.LOGGED_IN
        return True
        
        
    def waitForElementToLoad(self,id):
        element_present = EC.presence_of_element_located((By.ID, id))
        WebDriverWait(self.driver, self.timeout).until(element_present)
    def waitForElementToLoadByClass(self,clazz):
        element_present = EC.presence_of_element_located((By.CLASS_NAME, clazz))
        WebDriverWait(self.driver, self.timeout).until(element_present)
        
    def isAccountNonPremium(self,init=False):
        try:
            self.waitForElementToLoadByClass("premium")
            return True
        except:
            self.output("Could not find indicator of non-premium account; exiting")
            if init:
                self.status=Status.ACCOUNT_ALREADY_ACTIVATED
            self.saveScreenshot("alreadyPremium")
            return False
    def startFreeAccess(self):
        count = -1
        usedCodes = []
        timeOfLastCheck = 0
        self.status=Status.SEARCHING
        self.output("searching for guest passes")
        if not self.isAccountNonPremium(True):
            return None
        while True:
            count += 1
            try:
                guestCodes = self.findGuestPass()
            except TimeoutException:
                continue
            unusedGuestCodes = []
            for i in range(len(guestCodes)):
                if guestCodes[i] not in usedCodes:
                    unusedGuestCodes.append(guestCodes[i])
            if len(unusedGuestCodes) > 0:
                self.output("Trial ",count,": found ",len(unusedGuestCodes)," codes: ",unusedGuestCodes,"; ", len(usedCodes), " others have been used: ",usedCodes)
                timeOfLastCheck = time.time()
                shuffle(unusedGuestCodes)
            elif time.time()-timeOfLastCheck > 600:
                self.output("Trial ",count, "url",self.driver.current_url)
                sys.stdout.flush()
                
                timeOfLastCheck = time.time()
            if self.isTimeout():
                self.status=Status.TIMEOUT
                return None
            for i in range(len(unusedGuestCodes)):
                try:
                    self.driver.get(self.redeemGuestPassPage+unusedGuestCodes[i])

                    self.output("currentURL:",self.driver.current_url)
                    self.waitForElementToLoad("couponcode_redeem_form")
                    self.driver.find_element_by_id("couponcode_redeem_form").submit()
                    
                    self.output("URL after submit:",self.driver.current_url)
                    if not self.driver.current_url.startswith(self.failedGuestPassRedeemPage) and  self.driver.current_url.startswith(self.homePage):
                        #self.saveScreenshot("~guest_pass_activated_question")
                        self.waitForElementToLoad("message_box")
                        message=self.driver.find_element_by_id("message_box").text
                        self.output("Message:",message)

                        if self.invalidResponse not in message:
                            self.saveScreenshot("~guest_pass_activated")
                            if self.isAccountNonPremium():
                                self.output("False positive. account is still non premium")
                                continue
                            else:                        
                                self.postTakenGuestPass(unusedGuestCodes[i])
                                self.output("found guest pass %s; exiting" % str(unusedGuestCodes[i]))
                                self.status=Status.ACCOUNT_ACTIVATED
                                return unusedGuestCodes[i]
                        else:
                            usedCodes.append(unusedGuestCodes[i])
                    else:
                        usedCodes.append(unusedGuestCodes[i])
                    self.output(self.driver.current_url)
                except TimeoutException:
                    usedCodes.append(unusedGuestCodes[i])
                    self.output("timeout occured with ", unusedGuestCodes[i])
                except:
                    self.output("error:",  sys.exc_info()[0])
                    traceback.print_exc()
                    pass

            time.sleep(self.DELAY)
            if not self.isAccountNonPremium():
                self.saveScreenshot("~guest_pass_already_activated")
                self.output("currentURL:",self.driver.current_url)
                self.status=Status.ACCOUNT_ACTIVATED
                return None


    def postTakenGuestPass(self,guestPass):
        try:
            self.output("attempting to post that guest pass was taken")
            self.driver.get(self.endOfGuestPassThreadPage)
            self.driver.find_element_by_id("newforumpost").send_keys(guestPass+" has been taken.\nThanks")
            self.saveScreenshot("posted_guest_pass")
            self.driver.find_element_by_name("post_btn").click()

        except:
            self.output("failed to post guest pass");
                
    def findGuestPass(self):
        self.driver.get(self.endOfGuestPassThreadPage)

        classes=self.driver.find_elements_by_class_name("showforumtopic-message-contents-text")
        guestCodes=[]
        inValidGuestCodes=[]

        for i in range(len(classes)):

            matches = re.findall(self.GUEST_PASS_PATTERN,classes[i].text,re.M)

            if matches:
                for n in range(len(matches)):
                    if matches[n] not in guestCodes:
        
                        guestCodes.append(matches[n])
                    elif matches[n] not in inValidGuestCodes:
                        inValidGuestCodes.append(matches[n])

        for i in range(len(inValidGuestCodes)):
            guestCodes.remove(inValidGuestCodes[i])

        return guestCodes

    def saveScreenshot(self,fileName="screenshot.png"):
        fileName+=".png"
        self.output("saving screen shot to ",fileName)
        self.driver.save_screenshot(CONFIG_DIR+fileName)
        pass

    def output(self,*message):

        time=datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")+":"
        formattedMessage=message[0]
        for i in range(1,len(message)):
            formattedMessage+=str(message[i])
        print(time,formattedMessage, flush=True)

    def getStatus(self):
        return self.status.value


if __name__ == "__main__":

    if len(sys.argv) < 3:
        username = input("Username:")
        password = input("Password:")
    else:
        if len(sys.argv) >= 4:
            CrunchyrollGuestPassFinder.KILL_TIME = int(sys.argv[3])
            if len(sys.argv) >= 5:
                CrunchyrollGuestPassFinder.DELAY = int(sys.argv[4])
        username, password = sys.argv[1], sys.argv[2]
    crunchyrollGuestPassFinder = CrunchyrollGuestPassFinder(username, password)
    if crunchyrollGuestPassFinder.login():
        crunchyrollGuestPassFinder.startFreeAccess()
    print("status = %d" % crunchyrollGuestPassFinder.getStatus())
    exit(crunchyrollGuestPassFinder.getStatus())
