import pandas as pd
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
import chromedriver_autoinstaller
import pickle
import json
import os
from selenium_stealth import stealth

class Scraper():
    
    login_url = 'https://twitter.com/i/flow/login'
    username_field_xpath = '//input[@name="text"]'
    password_field_xpath = '//input[@name="password"]'
    chromedriver_path = chromedriver_autoinstaller.install(path='ChromeDriver')
    output_path = 'ScrapedData'
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    output_path = f'{os.getcwd()}/{output_path}'
    
    def __init__(self) -> None:
        self.browser_options = webdriver.ChromeOptions()
        self.browser_options.add_argument("--start-maximized")
        self.browser_options.add_argument('--disable-blink-features')
        self.browser_options.add_argument('--disable-blink-features=AutomationControlled')
        self.browser_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.browser_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.browser_options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(service=ChromeService(self.chromedriver_path), options=self.browser_options)
        stealth(
            self.driver,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            languages=["en-GB","en-US", "en"],
            vendor="Google Inc.",
            platform="Linux x86_64",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            run_on_insecure_origins=True,
        )
        self.driver.get(self.login_url)
    
    def click_and_send_keys(self, target: WebElement, value: str):
        ActionChains(self.driver).click(target).perform()
        for character in value:
            target.send_keys(character)
            time.sleep(0.1)
        time.sleep(2)
    
    def quick_login(self) -> None:
        cookies = pickle.load(open('cookies.pkl', 'rb'))
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        
    def standard_login(self, username: str, password: str) -> None:
        self.driver.implicitly_wait(5)
        self.driver.get(self.login_url)
        username_field = self.driver.find_element(By.XPATH, self.username_field_xpath)
        self.click_and_send_keys(username_field, username)
        self.driver.execute_script('document.querySelectorAll("div[role=button]")[2].click()')
        self.driver.implicitly_wait(5)
        password_field = self.driver.find_element(By.XPATH, self.password_field_xpath)
        self.click_and_send_keys(password_field, password)
        pickle.dump(self.driver.get_cookies(), open('cookies.pkl','wb'))
    
    def check_followers(self, user) -> None:
        self.driver.get(f'https://twitter.com/{user}')
        self.driver.implicitly_wait(5)
        user_info = self.driver.find_element(By.XPATH, '//script[@data-testid="UserProfileSchema-test"]').text
        self.follower_count = json.loads(user_info)['author']['interactionStatistic'][0]['userInteractionCount']
    
    def scrape_followers(self, user) -> None:
        self.check_followers(user)
        follower_list=[]
        self.driver.get(f'https://twitter.com/{user}/followers')
        self.driver.implicitly_wait(5)
        # for _ in range(self.follower_count):
        for _ in range(10):
            self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source)
            followers = soup.find_all('a',class_='css-4rbku5 css-18t94o4 css-1dbjc4n r-1loqt21 r-1wbh5a2 r-dnmrzs r-1ny4l3l')
            time.sleep(3)

            for follower in followers:
                follower_list.append(follower.text)
        df=pd.DataFrame(follower_list,columns=['Users'])
        df=df.drop_duplicates()
        
        df.to_excel(f'/{user}.xlsx')