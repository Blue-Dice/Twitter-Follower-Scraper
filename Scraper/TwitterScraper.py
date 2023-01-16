import pandas as pd
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
import chromedriver_autoinstaller
import pickle
import csv
import json
import os
from selenium_stealth import stealth

class Scraper():
    
    login_url = 'https://twitter.com/i/flow/login'
    home_url = 'https://twitter.com/home'
    username_field_xpath = '//input[@name="text"]'
    password_field_xpath = '//input[@name="password"]'
    if not os.path.isdir('ChromeDriver'):
        os.mkdir('ChromeDriver')
    chromedriver_path = chromedriver_autoinstaller.install(path='ChromeDriver')
    output_path = 'ScrapedData'
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    output_path = f'{os.getcwd()}/{output_path}'
    
    def __init__(self) -> None:
        self.browser_options = webdriver.ChromeOptions()
        self.browser_options.add_argument("--headless")
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
        print('Performing login using saved cookies')
        time.sleep(10)
        cookies = pickle.load(open('cookies.pkl', 'rb'))
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        self.driver.get(self.home_url)
        print('Login successful')
        
    def standard_login(self, username: str, password: str) -> None:
        self.driver.implicitly_wait(10)
        self.driver.get(self.login_url)
        username_field = self.driver.find_element(By.XPATH, self.username_field_xpath)
        self.click_and_send_keys(username_field, username)
        self.driver.execute_script('document.querySelectorAll("div[role=button]")[2].click()')
        self.driver.implicitly_wait(10)
        password_field = self.driver.find_element(By.XPATH, self.password_field_xpath)
        self.click_and_send_keys(password_field, password)
        self.driver.find_element(By.XPATH, "//span[contains(text(), 'Log in')]").click()
        time.sleep(10)
        pickle.dump(self.driver.get_cookies(), open('cookies.pkl','wb'))
    
    def scrape_followers(self, user) -> None:
        follower_list=[]
        print(f'Navigating to [https://twitter.com/{user}/followers]')
        self.driver.get(f'https://twitter.com/{user}/followers')
        WebDriverWait(driver=self.driver, timeout=10).until(
            lambda x: x.execute_script("return document.readyState === 'complete'")
        )
        print('Followers ->')
        time.sleep(3)
        first = True
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            if first:
                self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight/4)')
                first = False
            else:
                self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
            time.sleep(3)
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            followers = soup.find_all('div', {"data-testid":"UserCell"})
            for follower in followers:
                info=[]
                try:
                    info.append(follower.find_all('a', {"role":"link"})[1].text)
                    info.append(follower.find_all('a', {"role":"link"})[2].text)
                    try:
                        info.append(follower.find_all('div', {"dir":"auto"})[1].text)
                    except Exception:
                        info.append('NO BIO FOUND')
                    print(info)
                    if info not in follower_list: follower_list.append(info)
                except Exception as e:
                    print(f'Error while fetching follower information -> {e}')
                    follower_list.append(['ERROR'])
                    continue
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        with open(f'ScrapedData/{user}.csv', 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(follower_list)