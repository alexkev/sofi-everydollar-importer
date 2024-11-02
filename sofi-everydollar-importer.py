import os
import csv
import time
import shutil
import sys
from datetime import datetime

from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import glob
import keys

start_importing = False
site_link = 'https://www.everydollar.com/app/budget'

selenium_temp_dir = os.path.join(os.getcwd(), 'temp')

last_click_count = 0
current_click_count = 0

def import_automatically():
    driver = setup_driver()
    driver.get(site_link)
    login_to_everydollar(driver=driver)
    input('Sign into EveryDollar, then press ENTER in this window to continue.')
    print('Preparing to import transactions...')
    import_transactions(driver=driver, auto=True)
    quit_driver(driver=driver)
    print('\n [ All Transactions Imported! ] ')
    print("Don't forget to delete the spreadsheets we used, so they don't mess up your import next time.")

def show_logo():
    print(r'''
           __           ______                      ____        ____          
          / /_____     / ____/   _____  _______  __/ __ \____  / / /___ ______
         / __/ __ \   / __/ | | / / _ \/ ___/ / / / / / / __ \/ / / __ `/ ___/
        / /_/ /_/ /  / /___ | |/ /  __/ /  / /_/ / /_/ / /_/ / / / /_/ / /    
        \__/\____/  /_____/_|___/\___/_/   \__, /_____/\____/_/_/\__,_/_/     
            A tool for automatically importing transactions to EveryDollar
    ''')

def set_chrome_options(user_agent=None, proxy=None):
    options = uc.ChromeOptions()
    # disable Chrome popups
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-save-password-bubble")
    options.add_argument(f"--user-data-dir={selenium_temp_dir}")  # Set custom user data directory
    return options

def setup_driver(user_agent=None, proxy=None):
    print("Setting up chromedriver...")
    options = set_chrome_options(user_agent, proxy)
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(60)  # wait 60 second before error
    print("Done!")
    return driver

def quit_driver(driver):
    try:
        if driver is not None:
            driver.quit()
            shutil.rmtree(selenium_temp_dir, ignore_errors=True)  # Delete the temporary directory
    except:
        pass

def login_to_everydollar(driver):
    # XPaths
    email_xpath = '//input[@name="email"]'
    password_xpath = '//input[@name="password"]'
    login_button_xpath = '//button[@type="submit"]'

    # Wait until the page loads, or for 2min
    wait = WebDriverWait(driver, timeout=120)
    wait.until(EC.presence_of_element_located((By.XPATH, email_xpath)))

    print('Loading...')
    time.sleep(2)
    print('done loading')

    driver.find_element(By.ID, "1-email").click()
    # 4 | click | id=1-email |  | 
    driver.find_element(By.ID, "1-email").click()
    # 5 | type | id=1-email | axel720@gmail.com | 
    driver.find_element(By.ID, "1-email").send_keys(keys.email)
    # 6 | click | id=1-password |  | 
    driver.find_element(By.ID, "1-password").click()
    # 7 | type | id=1-password | AM!firesave017 | 
    driver.find_element(By.ID, "1-password").send_keys(keys.password)
    # 8 | click | id=1-submit |  | 
    driver.find_element(By.ID, "1-submit").click()
  
    # Wait until the page loads, or for 2min
    wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="/app/budget"]')))


def convert_date_format(date_str):
    date_object = datetime.strptime(date_str, "%Y-%m-%d")
    new_date_str = date_object.strftime("%m/%d/%y")
    return new_date_str

def import_transactions(driver, auto=False):
    # The auto argument lets you set if you want to review each transaction before adding or not

    add_transaction_link = 'https://www.everydollar.com/app/budget/transaction/new'

    # XPaths
    expense_selection_xpath = '//input[@name="expense"]'
    income_selection_xpath = '//input[@name="income"]'
    amount_xpath = '//input[@name="amount"]'
    date_xpath = '//input[@id="input-3"]'
    merchant_xpath = '//input[@name="merchant"]'
    more_xpath = '//button[contains(text(), "More Options")]'
    id_xpath = '//input[@name="checkNumber"]'
    note_xpath = '//textarea[@name="note"]'
    submit_button_xpath = '//button[@type="submit"]'

    # READ IN ALL .CSV IN ./
    csv_files = glob.glob('*.csv')

    for file in csv_files:
        # Open the file
        print('Opening {file}...')
        with open(file=file, mode='r', encoding='utf-8') as f:
            
            reader = csv.reader(f)
            id = 0
            for row in reader:
                id += 1
                # Skip the first row (header)
                if row[0] == 'Date':  
                    continue

                if row[1] == 'CHASE CREDIT CRD':
                    continue
                
                driver.get(add_transaction_link)

                # Wait until the page loads, or for 2min
                wait = WebDriverWait(driver, timeout=120)
                wait.until(EC.presence_of_element_located((By.XPATH, income_selection_xpath)))

                amount = row[3] 
                date = convert_date_format(row[0])
                merchant = row[1]
                note = "Imported from SOFI via Script"

                # if amount is positive, it's income, else it's an expense
                if float(amount) > 0:
                    element = driver.find_element(By.XPATH, income_selection_xpath)
                    ActionChains(driver).move_to_element(element).click().perform()
                else:
                    element = driver.find_element(By.XPATH, expense_selection_xpath)
                    ActionChains(driver).move_to_element(element).click().perform()

                # Amount
                element = driver.find_element(By.XPATH, amount_xpath)
                element.clear()
                element.send_keys(amount)

                # Date
                element = driver.find_element(By.XPATH, date_xpath)
                element.clear()
                element.send_keys(Keys.COMMAND + "a" + Keys.DELETE)
                element.send_keys(date)

                # Merchant
                driver.find_element(By.XPATH, merchant_xpath).send_keys(merchant)

                # Select More Options
                driver.find_element(By.XPATH, more_xpath).click()
                wait.until(EC.presence_of_element_located((By.XPATH, id_xpath)))  # (wait until it opens)

                # ID
                driver.find_element(By.XPATH, id_xpath).send_keys(id)

                # Note
                driver.find_element(By.XPATH, note_xpath).send_keys(note)

                if not auto:
                    if __name__ == "__main__":
                        input('To submit this transaction, press ENTER.')
                    else:
                        while last_click_count == current_click_count:
                            pass  # wait until they click the button

                        last_click_count = current_click_count

                else:
                    pass

                print('Submitting...')

                # Submit
                driver.find_element(By.XPATH, submit_button_xpath).click()
                time.sleep(5) if auto else time.sleep(3)

    # After all transactions are imported, print a message
    print('\n [ All Transactions Imported! ] ')

    # ask use to delete the spreadsheets we used, yes or no
    delete_files = input("Would you like to delete the spreadsheets we used? (yes/no): ")
    if delete_files.lower() == 'yes':
        for file in csv_files:
            os.remove(file)
        print('Files deleted.')



if __name__ == "__main__":
    show_logo()
    print('Launching browser...\n')
    import_automatically()
