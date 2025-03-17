from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import credentials
import re
import os
import datetime

# Global Variables
username = credentials.username
password = credentials.password
firefox_options = Options()
firefox_options.add_argument("--headless")
driver = webdriver.Firefox(options=firefox_options)
today = datetime.datetime.today()
current_week = today.isocalendar()[1]
numer_weeks = 5

def login():
    driver.get("https://app.shkolo.bg")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "login-username")))
    driver.find_element(By.ID, "login-username").send_keys(username)
    driver.find_element(By.ID, "passwordField").send_keys(password, Keys.RETURN)

    WebDriverWait(driver, 15).until(EC.url_contains("/dashboard"))

def create_unique_file_name():
    return "schedule.html"

def get_schedule(week):
    url = (f"https://app.shkolo.bg/ajax/diary/getScheduleForClass?"
           f"pupilx_id=2400236422&year=25&week={week}&class_year_id=2400011867")
    driver.get(url)

def extract_schedule_data(file_name):
    for week in range(current_week, current_week + numer_weeks):
        get_schedule(week)

        previous_first_char = None
        date = None
        time_range = None
        last_class_time_range = None

        try:
            schedule_table = driver.find_element(By.CLASS_NAME, "scheduleTable")
            columns = schedule_table.find_elements(By.CLASS_NAME, "scheduleTableColumn")

            with open(file_name, 'a', encoding='utf-8') as f:
                for column in columns:
                    heading_elements = column.find_elements(By.CLASS_NAME, "scheduleTableHeading")
                    schedule_date = [row.text for row in heading_elements]
                    date = extract_date(schedule_date)

                    body_elements = column.find_elements(By.CLASS_NAME, "scheduleTableBody")
                    schedule_body = ''.join([row.text for row in body_elements])
                    lines = schedule_body.split('\n')

                    f.write(f"Date: {date}\n")
                    for line in lines:
                        current_first_char = line[0]
                        if current_first_char != previous_first_char:
                            time_range = extract_time_range(line)

                            class_info = re.sub(r' \d{2}:\d{2} - \d{2}:\d{2}$', '', line).strip()
                            last_class_time_range = time_range

                            f.write(f"Class: {class_info}\nTime range: {time_range}\n")
                            previous_first_char = current_first_char
        except Exception as e:
            print(f"Error: {e}")

def extract_date(schedule_date):
    date_pattern = r'\d{2}\.\d{2}\.\d{4}'
    for row in schedule_date:
        match = re.search(date_pattern, row)
        if match:
            return match.group()
    return None

def extract_time_range(line):
    time_pattern = r'\d{2}:\d{2} - \d{2}:\d{2}'
    match = re.search(time_pattern, line)
    return match.group() if match else "08:00 - 13:55"

def delete_schedule_file(file_path):
    if os.path.exists(file_path): 
        os.remove(file_path)

def main():
    try:
        login()
        delete_schedule_file('schedule.html')
        file_name = create_unique_file_name()
        extract_schedule_data(file_name)
    finally:
        driver.quit()

# Run the main function
if __name__ == "__main__":
    main()
