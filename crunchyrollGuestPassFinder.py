import re
import sys
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import traceback


class CrunchyrollGuestPassFinder:
    endOfGuestPassThreadPage = "http://www.crunchyroll.com/forumtopic-803801/the-official-guest-pass-thread-read-opening-post-first?pg=last"
    redeemGuestPassPage ="http://www.crunchyroll.com/coupon_redeem?code="
    loginPage="https://www.crunchyroll.com/login"
    homePage="http://www.crunchyroll.com/"
    GUEST_PASS_PATTERN="[A-Z0-9]{11}"
    timeout=20
    invalidResponse="Coupon code not found."
    
    
    KILL_TIME = 43200
    
    def __init__(self,username,password):
    
        self.driver = webdriver.PhantomJS(service_log_path="/dev/null",service_args=['--ssl-protocol=any'])
        self.driver.implicitly_wait(self.timeout)
        self.startTime=time.time()
        self.output("starting bot")
        self.username=username
        self.password=password
        self.login()
    
    def checkTimeLeft(self,errorCode=64):
        if time.time() - self.startTime >= self.KILL_TIME:
            exit(errorCode)
        else:
            return True
    def login(self):
        self.driver.get(self.loginPage)
        self.output("attemting to login to "+self.username)

        self.driver.find_element_by_id("login_form_name").send_keys(self.username)
        self.driver.find_element_by_id("login_form_password").send_keys(self.password)
        self.driver.find_element_by_class_name("type-primary").click()
        #self.saveScreenshot("loggedIn.png~")
        self.output("logged in")
        self.output(self.driver.current_url)
        
    def waitForElementToLoad(self,id):
        element_present = EC.presence_of_element_located((By.ID, id))
        WebDriverWait(self.driver, self.timeout).until(element_present)
    def waitForElementToLoadByClass(self,clazz):
        element_present = EC.presence_of_element_located((By.CLASS_NAME, clazz))
        WebDriverWait(self.driver, self.timeout).until(element_present)
        
    def startFreeAccess(self):
        count=0
        usedCodes=[]
        while True:
            count+=1
            
            guestCodes=self.findGuestPass()
            unusedGuestCodes=[]
            for i in range(len(guestCodes)):
                if guestCodes[i] not in usedCodes:
                    unusedGuestCodes.append(guestCodes[i])
            if len(unusedGuestCodes)>0:
                self.output("Trial ",count,": found ",len(unusedGuestCodes)," codes: ",unusedGuestCodes,"; ", len(usedCodes), " others have been used: ",usedCodes)
            elif count%1200==0:
                self.output ("Trial ",count)
                sys.stdout.flush()
                try:
                    self.waitForElementToLoadByClass("premium")
                except TimeoutException:
                    self.output("Could not find indicator of non-premium account; exiting")
                    return None
            self.checkTimeLeft()
            for i in range(len(unusedGuestCodes)):
                try:
                    self.driver.get(self.redeemGuestPassPage+unusedGuestCodes[i])

                    self.output("currentURL:",self.driver.current_url)
                    self.waitForElementToLoad("couponcode_redeem_form")
                    self.driver.find_element_by_id("couponcode_redeem_form").submit()
                    
                    self.output("URL after submit:",self.driver.current_url)
                    if self.driver.current_url == self.homePage or not self.redeemGuestPassPage.startswith(self.driver.current_url):
                        #self.saveScreenshot("~guest_pass_activated_question")
                        self.waitForElementToLoad("message_box")
                        message=self.driver.find_element_by_id("message_box").text
                        self.output(message)

                        if self.invalidResponse not in message:
                            #self.saveScreenshot("~guest_pass_activated")
                            self.postTakenGuestPass(unusedGuestCodes[i])
                            self.output("found guest pass; exiting")
                            return unusedGuestCodes[i]
                        else: 
                            usedCodes.append(unusedGuestCodes[i])
                    else:
                        usedCodes.append(unusedGuestCodes[i])
                    self.output(self.driver.current_url)
                except TimeoutException:
                    usedCodes.append(unusedGuestCodes[i])
                    self.output("timeout occured with ",unusedGuestCodes[i])
                except:
                    self.output("error:",  sys.exc_info()[0])
                    traceback.print_exc()
                    pass
            
            time.sleep(1)
    
    def postTakenGuestPass(self,guestPass):
        try:
            self.output("attempting to post that guest pass was taken")
            self.driver.get(self.endOfGuestPassThreadPage)
            self.waitForElementToLoad("newforumpost")
            self.driver.find_element_by_id("newforumpost").send_keys(guestPass+" has been taken.\nThanks")
            self.driver.find_element_by_name("post_btn").click()

            #self.saveScreenshot("posted_guest_pass")
        except:
            self.output("failed to post guest pass");
                
    def findGuestPass(self):
        self.driver.get(self.endOfGuestPassThreadPage)

        classes=self.driver.find_elements_by_class_name("showforumtopic-message-contents-text")
        guestCodes=[]
        inValidGuestCodes=[]

        for i in range(len(classes)):
            
            matches=re.findall(self.GUEST_PASS_PATTERN,classes[i].text,re.M)
        
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
        #self.output("saving screen shot to ",fileName)
        #self.driver.save_screenshot(fileName)
        pass

    def output(self,*message):
        
        time=datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")+":"
        formattedMessage=message[0]
        for i in range(1,len(message)):
            formattedMessage+=str(message[i])
        print (time,formattedMessage, flush=True)

if __name__ == "__main__":
    if len(sys.argv)>4:
        print(int(sys.argv[4]))
        CrunchyrollGuestPassFinder.KILL_TIME=int(sys.argv[3])
    crunchyrollGuestPassFinder=CrunchyrollGuestPassFinder(sys.argv[1],sys.argv[2])
    crunchyrollGuestPassFinder.startFreeAccess()
