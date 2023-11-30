import time
from datetime import datetime
import colorama as colorama
import subprocess
import platform
from tqdm import tqdm
from mysql.connector import connect, Error
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv
import os
import schedule


previous_state = []
should_continue = True


def play_beep_sound(duration_seconds=1):
    # Play a longer beep sound using the 'osascript' command-line tool and AppleScript
    if platform.system() == 'Darwin':
        script = '''
            repeat {}
                set volume 5
                beep
                delay 1.5
            end repeat
        '''.format(duration_seconds)
        subprocess.call(["osascript", "-e", script])  # Play longer beep sound on macOS osascript


def fill_input_field(element, value):
    if value is not None:
        element.clear()
        element.send_keys(value)


def uncheck_all_checkboxes():
    checkboxes = driver.find_elements(By.XPATH, '//input[@type="checkbox"]')
    # Iterate over checkboxes
    for checkbox in checkboxes:
        # Unselect checkbox if already selected
        if checkbox.is_selected():
            checkbox.click()
            print(f"{checkbox.get_attribute('value')} checkbox is unselected.")
        else:
            print(f"{checkbox.get_attribute('value')} checkbox is already unselected.")


def fill_checkbox_field(element, value):
    value_to_set = value
    array_values = ['Yes']

    # Check the checkbox if the value_to_set exists in the array values, uncheck it otherwise
    if value_to_set in array_values:
        if not element.is_selected():
            element.click()
    else:
        if element.is_selected():
            element.click()


def form_values(rows: list = []):
    try:
        wait = WebDriverWait(driver, 10)  # Wait up to 10 seconds for elements to be ready
        try:
            firstName = wait.until(EC.presence_of_element_located((By.ID, "root_firstName")))
            lastName = wait.until(EC.presence_of_element_located((By.ID, "root_lastName")))
            mobileNumber = wait.until(EC.presence_of_element_located((By.ID, "root_mobileNumber")))
            emailAddress = wait.until(EC.presence_of_element_located((By.ID, "root_email")))
            firstBarcode = wait.until(EC.presence_of_element_located((By.ID, "root_questionAnswerPair_4006")))
            # gender = Select(genderSelect)
            # proviceSelect = wait.until(EC.presence_of_element_located((By.ID, "root_stateOrProvince")))
            # province = Select(proviceSelect)
            ageConsent = wait.until(EC.presence_of_element_located((By.ID, 'root_optins_legalAgeConsent')))
            emailConsent = wait.until(EC.presence_of_element_located((By.ID, 'root_optins_unileverEmailConsent')))
            smsConsent = wait.until(EC.presence_of_element_located((By.ID, 'root_optins_unileverSMSConsent')))
            button = driver.find_element(By.TAG_NAME, 'button')

            # Fill in form fields
            fill_input_field(firstName, rows['name'])
            fill_input_field(lastName, rows['surname'])
            fill_input_field(mobileNumber, rows['msisdn'])
            fill_input_field(emailAddress, rows['email'])
            fill_input_field(firstBarcode, rows['first_barcode'])

            # if rows[7] == "Prefer not say":
            # gender.select_by_value("N")

            # if rows[7] == "Male":
            # gender.select_by_value("M")

            # if rows[7] == "Female":
            # gender.select_by_value("F")

            # if rows[7] == "None":
            # gender.select_by_value("O")

            # if rows[8] == "KZN":
            # province.select_by_value("KwaZulu-Natal")
            # elif rows[8] == "None":
            # print("nothing")
            # else:
            # province.select_by_value(rows[8])

            fill_checkbox_field(ageConsent, rows['are_you_older_than_18'])
            fill_checkbox_field(emailConsent, rows['receive_offers_via_email'])
            fill_checkbox_field(smsConsent, rows['receive_offers_via_sms'])

            # Click the button
            actions = ActionChains(driver)
            actions.move_to_element(button).click().perform()
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            fill_checkbox_field(ageConsent, rows['are_you_older_than_18'])
            fill_checkbox_field(emailConsent, rows['receive_offers_via_email'])
            fill_checkbox_field(smsConsent, rows['receive_offers_via_sms'])

            # Click the button
            actions = ActionChains(driver)
            actions.move_to_element(button).click().perform()

    except TimeoutException:
        # Handle the TimeoutException
        print("Element not found or not visible within the specified timeout.")
        play_beep_sound(5)


def post_entry_details(rows: list = []):
    try:
        form_values(rows)
    except StaleElementReferenceException:
        form_values(rows)
        # play_beep_sound(5)


def progress_bar(progress, total, color=colorama.Fore.YELLOW):
    percent = 100 * (progress / float(total))
    bar = '▌' * int(percent) + '-' * (100 - int(percent))
    print(color + f"\r|{bar}| {percent:.2f}%", end="\r")
    if progress == total:
        print(colorama.Fore.GREEN + f"\r|{bar}| {percent:.2f}%", end="\r")


def main():
    print("running")
    global should_continue
    global previous_state
    try:
        print("****************Initializing**************************")
        # Define the target date to stop the loop
        target_date = datetime(2023, 10, 27)
        # while START_PROCESS:

        # Connect to the database
        with connect(
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'),
                user=os.getenv('DB_USERNAME'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
        ) as connection:
            cursor = connection.cursor()  # Create a cursor

            query = "SELECT DISTINCT " \
                    "id, " \
                    "msisdn, " \
                    "are_you_older_than_18, " \
                    "receive_offers_via_sms, " \
                    "receive_offers_via_email, " \
                    "name, " \
                    "surname, " \
                    "email " \
                    "FROM dovemenpluscareussd_surveys " \
                    "WHERE are_you_older_than_18='Yes' " \
                    "AND msisdn IS NOT NULL AND msisdn != '' " \
                    "AND receive_offers_via_sms='Yes' " \
                    "AND receive_offers_via_email='Yes' " \
                    "AND email IS NOT NULL AND email != ''"

            # Execute the SELECT query
            cursor.execute(query)

            # Fetch the current state
            current_state = cursor.fetchall()
            print(current_state)

            # Compare with the previous state
            if current_state != previous_state:
                new_updates = [record for record in current_state if record not in previous_state]

                with tqdm(total=len(new_updates), desc="Progress per hour", unit="record", colour="yellow") as pbar:
                    for i, update in enumerate(new_updates):
                        msisdn_value = update[1]
                        query_two = f"SELECT * FROM dovemenpluscareussd_logs WHERE msisdn = '{msisdn_value}'"

                        cursor.execute(query_two)
                        result_two = cursor.fetchone()

                        update_dict = {
                            'id': update[0],
                            'msisdn': update[1],
                            'are_you_older_than_18': update[2],
                            'receive_offers_via_sms': update[3],
                            'receive_offers_via_email': update[4],
                            'name': update[5],
                            'surname': update[6],
                            'email': update[7]
                        }

                        merged_data = {
                            **update_dict,
                            'first_barcode': result_two[4],
                            'second_barcode': result_two[5]
                        }

                        post_entry_details(merged_data)
                        time.sleep(0.1)  # Simulate some processing time
                        pbar.update(1)  # Increment the progress bar

                        try:
                            # Wait for the redirect to the loader page
                            WebDriverWait(driver, 180).until(EC.url_contains("success-page.html"))
                            driver.implicitly_wait(3)
                            uncheck_all_checkboxes()

                            # navigate back to the form page for the next iteration
                            driver.get(base_url)
                        except (NoSuchWindowException, TimeoutException) as e:

                            # Handle the NoSuchWindowException and TimeoutException by waiting
                            # and navigating back to the
                            driver.implicitly_wait(100)
                            driver.get(base_url)
            else:
                print("State didn't change")
        # Update the previous state
        previous_state = current_state
        cursor.close()
        connection.close()

        # Check if the target date is reached
        if datetime.now().date() >= target_date.date():
            # Close the cursor,driver, stop the process and connection
            should_continue = False
            cursor.close()
            connection.close()
            driver.close()
            print("**************************End**************************")

        # Update after an hour Sleep and Reset the color
        # time.sleep(3600)
        print(colorama.Fore.RESET)

    except Error as e:
        print(e)


if __name__ == '__main__':
    load_dotenv()
    base_url = "https://forms-widget.unileversolutions.com/?id=7281c554"
    # this leaves the browser open even after I'm done sending requests
    options = Options()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(100)
    driver.get(base_url)
    driver.maximize_window()

    # Create a tqdm progress bar that spans an hour
    total_duration = 60  # 60 seconds * 60 minutes = 3600 seconds
    while should_continue:
        if should_continue:
            with tqdm(total=total_duration, desc="Waiting period per hour", unit='s', colour="blue") as pbar:
                # Schedule the task to run every second
                schedule.every().minute.do(main)

                start_time = time.time()

                while pbar.n < pbar.total:
                    # Update the progress bar
                    elapsed_time = time.time() - start_time
                    pbar.n = min(int(elapsed_time), total_duration)
                    pbar.last_print_n = pbar.n
                    pbar.update(0)

                    # Run pending scheduled tasks
                    schedule.run_pending()
                    time.sleep(1)

                # Complete the progress bar when the hour is up
                pbar.update(total_duration - pbar.n)

            print("Progress bar finished.")
