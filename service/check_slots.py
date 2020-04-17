import sys, os, re, requests, time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


from twilio.rest import Client
import datetime as dt


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
chromedriver = ROOT_DIR + "/chromedriver"

# amazon credentials

#enter amazon user account here
amazon_username = ""
#enter amazon password here
amazon_password = ""

# twilio configuration

#enter your phone number here that has been identified by twilio
to_mobilenumber = "+"
#enter twillo's free account phone number here
from_mobilenumber = "+"
#enter account_sid that was given by twilio
account_sid = ""
#enter the auth token that was given by twilio
auth_token = ""

client = Client(account_sid, auth_token)


def create_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")

    #this is checking the OS for the computer
    #nt = windows
    #posix = mac/linux

    if os.name is "nt":
        dir_to_nt_driver = os.path.abspath(os.getcwd())
        #trying to get the directory that has the chrome_driver.exe
        dir_to_nt_driver = dir_to_nt_driver[:(len(dir_to_nt_driver)-8)] + "\chromedriver.exe"
        driver = webdriver.Chrome(executable_path=dir_to_nt_driver, options=chrome_options)
    else:
        driver = webdriver.Chrome(chromedriver, options=chrome_options)

    return driver

def terminate(driver):
    driver.quit()

def check_slots():

    print("Are you buying from Amazon Fresh or Whole Foods?")
    user_input_for_amazon = input("Enter in either: \n  1) Amazon Fresh \n  2) Whole Foods\n\n Enter Here:-> ")

    selected = ""
    selected_type = ""

    while (selected == ""):
        if (user_input_for_amazon == "Amazon Fresh" or user_input_for_amazon == "1" or user_input_for_amazon == "amazon fresh"):
            selected_type = "Amazon Fresh"
            selected = "proceedToALMCheckout-QW1hem9uIEZyZXNo"
        elif (user_input_for_amazon == "Whole Foods" or user_input_for_amazon == "2" or user_input_for_amazon == "whole foods"):
            selected_type = "Whole Foods"
            selected = "proceedToALMCheckout-VUZHIFdob2xlIEZvb2Rz"
        elif (user_input_for_amazon == "q" or user_input_for_amazon == "quit" or user_input_for_amazon == "3" or
              user_input_for_amazon == "exit"
              or user_input_for_amazon == "exit python script"):
            sys.exit()
        else:
            print("\n\nPlease try again.")
            print("Are you buying from Amazon Fresh or Whole Foods?")
            user_input_for_amazon = input("Enter in either: \n  1) Amazon Fresh \n  2) Whole Foods \n  3) To exit Python script\n\n Enter Here:-> ")
    try:
        print('Creating Chrome Driver ...')
        driver = create_driver()

        print('\nLogging into Amazon ...')
        driver.get('https://www.amazon.com/gp/sign-in.html')
        email_field = driver.find_element_by_css_selector('#ap_email')
        email_field.send_keys(amazon_username)
        driver.find_element_by_css_selector('#continue').click()

        time.sleep(1.5)
        password_field = driver.find_element_by_css_selector('#ap_password')
        password_field.send_keys(amazon_password)
        driver.find_element_by_css_selector('#signInSubmit').click()

        print('\nGoing to Amazon Cart ...')
        time.sleep(1.5)
        driver.get('https://www.amazon.com/gp/cart/view.html?ref_=nav_cart')

        # Amazon Fresh element
        # driver.find_element_by_name('proceedToALMCheckout-QW1hem9uIEZyZXNo').click()

        # Whole Foods element
        # driver.find_element_by_name('proceedToALMCheckout-VUZHIFdob2xlIEZvb2Rz').click()


        if selected_type == "Amazon Fresh":
            print('\nSearching for Amazon Fresh cart ...')
            time.sleep(1.5)
            driver.find_element_by_name(selected).click()

            print('\nGoing to checkout ...')
            time.sleep(1.5)
            driver.find_element_by_name('proceedToCheckout').click()

            more_dows = True
            slots_available = False
            available_slots = ""
            while not slots_available:
                while more_dows:
                    time.sleep(1.5)
                    slots = driver.find_elements_by_css_selector('.ss-carousel-item')
                    for slot in slots:
                        if slot.value_of_css_property('display') != 'none':
                            slot.click()
                            date_containers = driver.find_elements_by_css_selector('.Date-slot-container')
                            for date_container in date_containers:
                                if date_container.value_of_css_property('display') != 'none':
                                    unattended_slots = date_container.find_element_by_css_selector(
                                        '#slot-container-UNATTENDED')
                                    if 'No doorstep delivery' not in unattended_slots.text:
                                        available_slots = unattended_slots.text.replace('Select a time', '').strip()
                                        slots_available = True
                                    else:
                                        print(unattended_slots.text.replace('Select a time', '').strip())

                    next_button = driver.find_element_by_css_selector('#nextButton')
                    more_dows = not next_button.get_property('disabled')
                    if more_dows: next_button.click()

                if slots_available:
                    client.messages.create(to=to_mobilenumber,
                                           from_=from_mobilenumber,
                                           body=available_slots)
                    print('\nSlots Available for Amazon Fresh!')
                else:
                    currentTime = dt.datetime.now()

                    if (currentTime.hour > 13):
                        date = "No available slots for Amazon Fresh as of {0} ".format(currentTime.strftime('%Y/%m/%d - %I:%Mpm'))
                    else:
                        date = "No available slots for Amazon Fresh as of {0} ".format(currentTime.strftime('%Y/%m/%d - %I:%Mam'))

                    client.messages.create(to=to_mobilenumber,
                                           from_=from_mobilenumber,
                                           body=date)
                    print('No slots available.')
                    break
                    # more_dows = True
                    # time.sleep(15)
                    # driver.refresh()

            terminate(driver)

        elif selected_type is "Whole Foods":
            print('\nSearching for Whole Foods cart ...')
            time.sleep(1.5)

            #Trying to extract the number of items in the Whole Foods cart
            contentText = driver.find_elements_by_id('sc-subtotal-label-buybox')
            num_of_WholeFoods_items = 0

            for i in contentText:
                temp = ""
                for j in range(len(i.text)):
                    if (temp != "Whole Foods"):
                        temp += i.text[j]
                    elif (temp == "Whole Foods"):
                        num_of_WholeFoods_items = int(''.join(k for k in i.text if k.isdigit()))
                        break

            driver.find_element_by_name(selected).click()

            print('\nGoing to checkout ...')
            time.sleep(1.5)
            driver.find_element_by_name('proceedToCheckout').click()

            time.sleep(1.5)

            #base cases

            # #one item
            # #/html/body/div[1]/div[2]/span/form/div[2]/div/div/div[2]/div[3]/span/div/label/input
            #
            #
            # #two items
            # #/html/body/div[1]/div[2]/span/form/div[2]/div[1]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[2]/div[2]/div/div[2]/div[3]/span/div/label/input
            #
            # #three items
            # #/html/body/div[1]/div[2]/span/form/div[2]/div[1]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[2]/div[2]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[3]/div/div/div[2]/div[3]/span/div/label/input
            #
            # #four items
            # #/html/body/div[1]/div[2]/span/form/div[2]/div[1]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[2]/div[2]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[3]/div[1]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[3]/div[2]/div/div[2]/div[3]/span/div/label/input
            #
            # #five items
            # #/html/body/div[1]/div[2]/span/form/div[2]/div[1]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[2]/div[2]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[3]/div[1]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[3]/div[2]/div/div[2]/div[3]/span/div/label/input
            # #/html/body/div[1]/div[2]/span/form/div[4]/div/div/div[2]/div[3]/span/div/label/input

            if (num_of_WholeFoods_items == 1):
                driver.find_element_by_xpath("/html/body/div[1]/div[2]/span/form/div[2]/div/div/div[2]/div[3]/span/div/label/i").click()
            elif (num_of_WholeFoods_items == 2):
                driver.find_element_by_xpath("/html/body/div[1]/div[2]/span/form/div[2]/div[1]/div/div[2]/div[3]/span/div/label/i").click()
                time.sleep(1)
                driver.find_element_by_xpath("/html/body/div[1]/div[2]/span/form/div[2]/div[2]/div/div[2]/div[3]/span/div/label/i").click()
            elif (num_of_WholeFoods_items == 3):
                driver.find_element_by_xpath("/html/body/div[1]/div[2]/span/form/div[2]/div[1]/div/div[2]/div[3]/span/div/label/i").click()
                time.sleep(1)
                driver.find_element_by_xpath("/html/body/div[1]/div[2]/span/form/div[2]/div[2]/div/div[2]/div[3]/span/div/label/i").click()
                time.sleep(1)
                driver.find_element_by_xpath("/html/body/div[1]/div[2]/span/form/div[3]/div/div/div[2]/div[3]/span/div/label/i").click()
            elif (num_of_WholeFoods_items > 3 and num_of_WholeFoods_items % 2 == 0):
                counter = 1
                divDownColumn = 2
                for wholefoods in range(num_of_WholeFoods_items):
                    str_of_button = "/html/body/div[1]/div[2]/span/form/div[{0}]/div[{1}]/div/div[2]/div[3]/span/div/label/i".format(divDownColumn, counter)
                    if (driver.find_element_by_xpath(str_of_button).is_selected() == False):
                        driver.find_element_by_xpath(str_of_button).click()
                        time.sleep(1)
                    else:
                        continue
                    counter += 1
                    if counter == 3:
                        divDownColumn += 1
                        counter = 1
            else:
                counter = 1
                divDownColumn = 2
                for wholefoods in range(num_of_WholeFoods_items):
                    if wholefoods != (num_of_WholeFoods_items - 1):
                        str_of_button = "/html/body/div[1]/div[2]/span/form/div[{0}]/div[{1}]/div/div[2]/div[3]/span/div/label/i".format(divDownColumn, counter)
                        if (driver.find_element_by_xpath(str_of_button).is_selected() == False):
                            driver.find_element_by_xpath(str_of_button).click()
                            time.sleep(1)
                        else:
                            continue
                        counter += 1
                        if counter == 3:
                            divDownColumn += 1
                            counter = 1
                    else:
                        str_of_button = "/html/body/div[1]/div[2]/span/form/div[{0}]/div/div/div[2]/div[3]/span/div/label/i".format(divDownColumn)
                        if (driver.find_element_by_xpath(str_of_button).is_selected() == False):
                            driver.find_element_by_xpath(str_of_button).click()
                        else:
                            continue
                        time.sleep(1)

        time.sleep(1)
        driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[2]/div[2]/div/div[2]/div/div/span/span/span/input").click()
        time.sleep(3)
        text1 = "/html/body/div[5]/div[1]/div/div[2]/div/div/div/div/div[1]/div[3]/div[2]/div/ul/li[1]/span/span/span/button/div"
        text2 = "/html/body/div[5]/div[1]/div/div[2]/div/div/div/div/div[1]/div[3]/div[2]/div/ul/li[2]/span/span/span/button/div"

        available_slots_whole_foods = [0, 0]


        if (driver.find_element_by_xpath(text1).text != ""):
            findAvailable = ""
            reserveTimeStrDay1 = driver.find_element_by_xpath(text1).text
            reserveTimeStrDay1New = reserveTimeStrDay1.replace('\n', ' : ')

            for i in range(len(reserveTimeStrDay1)):
                if (reserveTimeStrDay1[i] == "\n" or i == len(reserveTimeStrDay1) - 1):
                    findAvailable += reserveTimeStrDay1[i]
                    if (reserveTimeStrDay1 == "Not available"):
                        available_slots_whole_foods[0] = 0
                    elif (reserveTimeStrDay1 == "Available"):
                        available_slots_whole_foods[0] = 1
                        print(reserveTimeStrDay1New)
                    else:
                        findAvailable = ""
                else:
                    findAvailable += reserveTimeStrDay1[i]

        else:
            pass

        if (driver.find_element_by_xpath(text2) != ""):
            findAvailable = ""

            reserveTimeStrDay2 = driver.find_element_by_xpath(text2).text
            reserveTimeStrDay2New = reserveTimeStrDay2.replace('\n', ' : ')

            for i in range(len(reserveTimeStrDay2)):
                if (reserveTimeStrDay2[i] == "\n" or i == len(reserveTimeStrDay2) - 1):
                    findAvailable += reserveTimeStrDay2[i]
                    if (reserveTimeStrDay2 == "Not available"):
                        available_slots_whole_foods[0] = 0
                    elif (reserveTimeStrDay2 == "Available"):
                        available_slots_whole_foods[0] = 1
                        print(reserveTimeStrDay2New)
                    else:
                        findAvailable = ""
                else:
                    findAvailable += reserveTimeStrDay2[i]
        else:
            pass

        if (available_slots_whole_foods == [0,0]):
            currentTime = dt.datetime.now()

            if (currentTime.hour > 13):
                date = "No available slots for Whole Foods as of {0} ".format(currentTime.strftime('%Y/%m/%d - %I:%Mpm'))
            else:
                date = "No available slots for Whole Foods as of {0} ".format(currentTime.strftime('%Y/%m/%d - %I:%Mam'))

            client.messages.create(to=to_mobilenumber,
                                   from_=from_mobilenumber,
                                   body=date)
            print('No slots available.')
        elif (available_slots_whole_foods == [1,0]):
            currentTime = dt.datetime.now()

            if (currentTime.hour > 13):
                date = "There is an opening slot for Whole Foods - today as of {0} ".format(currentTime.strftime('%Y/%m/%d - %I:%Mpm'))
            else:
                date = "There is an opening slot for Whole Foods - today as of {0} ".format(currentTime.strftime('%Y/%m/%d - %I:%Mam'))

            client.messages.create(to=to_mobilenumber,
                                   from_=from_mobilenumber,
                                   body=date)
        elif (available_slots_whole_foods == [0,1]):
            currentTime = dt.datetime.now()

            if (currentTime.hour > 13):
                date = "There is an opening slot for Whole Foods - tomorrow as of {0} ".format(currentTime.strftime('%Y/%m/%d - %I:%Mpm'))
            else:
                date = "There is an opening slot for Whole Foods - tomorrow as of {0} ".format(currentTime.strftime('%Y/%m/%d - %I:%Mam'))

            client.messages.create(to=to_mobilenumber,
                                   from_=from_mobilenumber,
                                   body=date)
        else:
            currentTime = dt.datetime.now()

            if (currentTime.hour > 13):
                date = "There is an opening slot for Whole Foods for both days as of {0} ".format(
                    currentTime.strftime('%Y/%m/%d - %I:%Mpm'))
            else:
                date = "There is an opening slot for Whole Foods for both days as of {0} ".format(
                    currentTime.strftime('%Y/%m/%d - %I:%Mam'))

            client.messages.create(to=to_mobilenumber,
                                   from_=from_mobilenumber,
                                   body=date)

        terminate(driver)
    except Exception as e:
        terminate(driver)
        raise ValueError(str(e))


if __name__ == "__main__":
    check_slots()
