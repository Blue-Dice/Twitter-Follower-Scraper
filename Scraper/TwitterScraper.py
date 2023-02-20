import multiprocessing
multiprocessing.freeze_support()
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import threading
import pickle
import json
import time
import csv
import re
import os

class Scraper():
    
    login_url = 'https://twitter.com/i/flow/login'
    home_url = 'https://twitter.com/home'
    username_field_xpath = '//input[@name="text"]'
    password_field_xpath = '//input[@name="password"]'
    
    output_path = 'ScrapedData'
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    output_path = f'{os.getcwd()}/{output_path}'
    
    def __init__(self, enable_gui, start_sync) -> None:
        self.enable_gui = enable_gui
        self.start_sync = start_sync
        self.keywords = [str(key).lower() for key in json.loads(open('search.json','r').read())['keywords']]
        self.driver = self.create_session()
        self.driver.get(self.login_url)
        time.sleep(3)
    
    def create_session(self) -> WebDriver:
        options = uc.ChromeOptions()
        options.headless = not self.enable_gui
        driver = uc.Chrome(options)
        return driver
    
    def dispose_session(self) ->None:
        self.driver.quit()
 
    def quick_login(self) -> bool:
        print('Performing login using saved cookies')
        try:
            cookies = pickle.load(open('cookies.pkl', 'rb'))
            for _ in range(3):
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                self.driver.get(self.home_url)
                if self.check_login():
                    print('Login successful using saved cookie')
                    return True
        except Exception:
            print('Error while performing quick login')
        return False
    
    def extract_profile(self, user, info: list) -> None:
        with open(f'ScrapedData/{user}.csv', "r+", newline='') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            all_users = list(row[1] for row in csvreader)
            if info[1] not in all_users:
                try:
                    profile_driver = self.create_session()
                    print(f'Fetching content from [{info[1]}]')
                    profile_driver.get(info[1])
                    try:
                        time.sleep(3)
                        link = json.loads(profile_driver.execute_script('return document.querySelector("[data-testid=UserProfileSchema-test]").text'))['relatedLink'][1]
                        info.append(link)
                    except Exception:
                        info.append('NO URL FOUND')
                    profile_driver.quit()
                except Exception: print('Error while fetching user profile')
            try:
                info += re.findall(r"[A-Za-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", info[2])
            except Exception: print('Error file searching Bio for emails')
            print(info)
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(info)
        
    def standard_login(self, email: str, password: str, username: str) -> bool:
        try:
            print('Perform login using credentials provided in [.env] file')
            self.driver.implicitly_wait(10)
            username_field = self.driver.find_element(By.XPATH, self.username_field_xpath)
            self.click_and_send_keys(username_field, email)
            self.driver.execute_script('document.querySelectorAll("div[role=button]")[2].click()')
            print('Email input successful')
            time.sleep(3)
            try:
                username_field = self.driver.find_element(By.XPATH, self.username_field_xpath)
                self.click_and_send_keys(username_field, username)
                self.driver.execute_script('document.querySelectorAll("div[role=button]")[1].click()')
                print('User Name input successful')
            except Exception: pass
            time.sleep(3)
            password_field = self.driver.find_element(By.XPATH, self.password_field_xpath)
            self.click_and_send_keys(password_field, password)
            self.driver.find_element(By.XPATH, "//span[contains(text(), 'Log in')]").click()
            print('Password input successful')
            time.sleep(3)
            try:
                username_field = self.driver.find_element(By.XPATH, self.username_field_xpath)
                otp = str(input(f'ENTER OTP RECEIVED EMAIL: [{email}] AND THEN PRESS [ENTER]: '))
                self.click_and_send_keys(username_field, otp)
                self.driver.execute_script('document.querySelectorAll("div[role=button]")[1].click()')
                print('OTP input successful')
            except Exception: pass
            if self.check_login():
                print('Login successful using provided credentials')
                pickle.dump(self.driver.get_cookies(), open('cookies.pkl','wb'))
                return True
        except Exception:
            print('Error while performing standard login')
        print('Login not successfull')
        return False
    
    def click_and_send_keys(self, target: WebElement, value: str):
        ActionChains(self.driver).click(target).perform()
        for character in value:
            target.send_keys(character)
            time.sleep(0.1)
        time.sleep(2)
    
    def check_login(self) -> bool:
        time.sleep(3)
        try:
            self.driver.execute_script('document.querySelector("h2[dir=ltr]").textContent')
            return True
        except Exception:
            return False
    
    def check_keywords(self, string):
        for key in self.keywords:
            if key in string:
                return True
        return False
    
    def get_previous_records(self, user):
        old_user_names=[]
        try:
            with open(f'ScrapedData/{user}.csv', 'r') as csvfile:
                csvreader = csv.DictReader(csvfile)
                old_user_names = [user for user in [col['User_Name'] for col in csvreader]]
                if len(old_user_names) == 0:
                    csvfile.write('Name,User_Name,Bio,Website,Email\n')
        except Exception:
            with open(f'ScrapedData/{user}.csv', 'w') as csvfile:
                csvfile.write('Name,User_Name,Bio,Website,Email\n')
        return old_user_names
    
    def save_instance(self, info, user):
        if self.check_keywords(str(info[2]).lower()):
            if self.start_sync:
                self.extract_profile(user, info)
            else:
                thread = threading.Thread(target=self.extract_profile, args=(user, info))
                thread.start()
                thread.join()
    
    def custom_scroll(self):
        if self.first_scroll:
            self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight/4)')
            self.first_scroll = False
        else:
            self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
            
    def scrape_followers(self, user) -> None:
        follower_list=[]
        print(f'Navigating to [https://twitter.com/{user}/followers]')
        self.driver.get(f'https://twitter.com/{user}/followers')
        WebDriverWait(driver=self.driver, timeout=10).until(
            lambda x: x.execute_script("return document.readyState === 'complete'")
        )
        print('Followers ->')
        time.sleep(3)
        self.first_scroll = True
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        old_user_names = self.get_previous_records(user)
        while True:
            self.custom_scroll()
            time.sleep(3)
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            followers = soup.find_all('div', {"data-testid":"UserCell"})
            for follower in followers:
                info=[]
                try:
                    info.append(follower.find_all('a', {"role":"link"})[1].text)
                    info.append(f'https://twitter.com/{follower.find_all("a", {"role":"link"})[2].text[1:]}')
                    if info[1] in old_user_names:
                        print(f'Skipping [{info[1]}] (Already in record)')
                        continue
                    try:
                        info.append(follower.find_all('div', {"dir":"auto"})[1].text)
                    except Exception:
                        info.append('NO BIO FOUND')
                    self.save_instance(info, user)
                except Exception as e:
                    print(f'Error while fetching follower information -> {e}')
                    follower_list.append(['ERROR'])
                    continue
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height