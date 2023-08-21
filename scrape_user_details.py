import requests
import yaml
from telethon import TelegramClient, errors, events, sync
from telethon.tl.types import InputPhoneContact
from telethon import functions, types
import phonenumbers
from utils import getNumber
from getpass import getpass
import csv
import os
from skpy import Skype
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from collections import defaultdict
from utils import check_file_exists


with open("credentials.yml", "r") as file:
    cred_data = yaml.safe_load(file)


data_file = open(cred_data["file"], "+a", newline="")
datawriter = csv.writer(data_file)
datawriter.writerow(
    [
        "Platform",
        "Name",
        "Phone",
        "Email",
        "Carrier",
        "CountryCode",
        "Address",
        "City",
        "Zipcode",
        "street",
        "Lastseen",
        "Gender",
        "Verified",
    ]
)


def get_user_truecaller_details(
    regionCode,
    cred_data,
    phoneNumber=None,
    phoneNumbers=None,
):
    file_name = "TruecallerUserData.csv"
    check_file_exists(file_name)
    with open(file_name, "w", newline="") as file:
        data_writer = csv.writer(file)
        phoneNumber = phoneNumber.split(",")
        print(phoneNumber)
        for curr_phno in phoneNumber:
            platform = "TrueCaller"
            params = {
                "q": "q",
                "countryCode": "countryCode",
                "type": "4",
                "placement": "SEARCHRESULTS,HISTORY,DETAILS",
                "encoding": "json",
            }
            headers = {
                "content-type": "application/json; charset=UTF-8",
                "accept-encoding": "gzip",
                "user-agent": "Truecaller/11.75.5 (Android;10)",
                "clientsecret": "lvc22mp3l1sfv6ujg83rd17btt",
                "authorization": "Bearer " + cred_data["Truecaller"]["api_id"],
            }
            if phoneNumber:
                phNumber = phonenumbers.parse(curr_phno, regionCode)
                print(phNumber)
                nationalPhoneNumber = phonenumbers.format_number(
                    phNumber, phonenumbers.PhoneNumberFormat.NATIONAL
                )
                params["q"] = getNumber(nationalPhoneNumber)
                params["countryCode"] = "{}".format(
                    phonenumbers.region_code_for_number(phNumber)
                )
            try:
                if phoneNumbers:
                    bulk_resp = requests.get(
                        cred_data["Truecaller"]["bulk_search"],
                        headers=headers,
                        params=params,
                    )
                    if bulk_resp.status_code == 200:
                        bulk_data = bulk_resp.json()
                        print(bulk_data)
                resp = requests.get(
                    cred_data["Truecaller"]["search"], headers=headers, params=params
                )
                if resp.status_code == 200:
                    data = resp.json()
                    user_data = data["data"][0]
                    data_writer.writerow(
                        [
                            platform,
                            user_data["internetAddresses"][0].get("caption")
                            if len(user_data["internetAddresses"]) > 0
                            else "" or user_data["name"],
                            user_data["phones"][0]["e164Format"],
                            user_data["internetAddresses"][0].get("id")
                            if len(user_data["internetAddresses"]) > 0
                            else "",
                            user_data["phones"][0]["carrier"],
                            user_data["addresses"][0]["countryCode"],
                            user_data["addresses"][0].get("address"),
                            user_data["addresses"][0]["city"],
                            user_data["addresses"][0].get("zipCode"),
                            user_data["addresses"][0].get("street"),
                            None,
                            user_data.get("gender"),
                            " ".join(user_data.get("badges")),
                        ]
                    )
                else:
                    print("Enter a correct number and correct regioncode")
            except Exception as Error:
                print(Error)


def get_telegram_user_details(phone_no):
    file_name = "TelegramUserData.csv"
    check_file_exists(file_name)
    with open(file_name, "w", newline="") as file:
        data_writer = csv.writer(file)
        data_writer.writerow(["Platform", "name", "lastseen", "registered"])
        phone_nos = phone_no.split(",")
        for curr_phno in phone_nos:
            try:
                contact = InputPhoneContact(
                    client_id=0,
                    phone=curr_phno,
                    first_name="",
                    last_name="",
                )
                get_contacts = client(
                    functions.contacts.ImportContactsRequest([contact])
                )
                if len(get_contacts.users) > 0:
                    user_data = get_contacts.users[0]
                    platform, name, lastseen, registered = (
                        "Telegram",
                        user_data.first_name,
                        user_data.status.was_online.strftime("%m-%d-%Y, %H:%M:%S"),
                        "Yes",
                    )
                else:
                    platform, name, lastseen, registered = "Telegram", "", "", "No"
                data_writer.writerow([platform, name, lastseen, registered])
            except Exception as Error:
                print(Error)


def scrape_skype_details(phone_nos, cred_data):
    file_name = "SkypeUserDetails.csv"
    CHROMEDRIVER = "C:\\Users\\admin\\Downloads\\chromedriver.exe"
    driver = webdriver.Chrome(CHROMEDRIVER)
    check_file_exists(file_name)
    with open(
        file_name,
        "w",
        newline="",
    ) as file:
        data_writer = csv.writer(file)
        data_writer.writerow(["Platform", "Name", "Skype_id", "Location", "Verified"])
        phone_nos = phone_nos.split(",")
        for idx, curr_phone in enumerate(phone_nos):
            results = defaultdict(list)
            driver.get("https://web.skype.com/")
            time.sleep(3)
            skype = cred_data["Skype"]
            if idx < 1:
                username_input = driver.find_element(
                    By.XPATH,
                    skype["username_box"],
                )
                username_input.send_keys(skype["username"])
                driver.find_element(By.ID, skype["nxt_btn"]).click()
                time.sleep(2)
                user_password_input = driver.find_element(
                    By.XPATH,
                    skype["password_box"],
                )
                user_password_input.send_keys(skype["passwd"])
                driver.find_element(By.ID, skype["nxt_btn"]).click()
                time.sleep(2)
                driver.find_element(By.ID, skype["no_btn"]).click()

                driver.implicitly_wait(10)

                pop_up = driver.find_element(
                    By.XPATH,
                    skype["pop_up"],
                )
                pop_up.click()
            driver.find_element(By.CSS_SELECTOR, skype["search"]).click()
            driver.implicitly_wait(1)
            input_text = driver.find_element(By.CSS_SELECTOR, skype["inner_search"])
            input_text.send_keys(curr_phone)
            time.sleep(8)
            user_data = driver.find_elements(By.XPATH, skype["listitem"])
            texts = [curr_data.get_attribute("aria-label") for curr_data in user_data]
            print(texts)
            for curr_txt in texts:
                if curr_txt:
                    u_data = curr_txt.split(",")
                    results["name"].append(u_data[0])
                    results["skype_id"].append(u_data[1].split(":", 1)[1].strip())
                    results["location"].append(
                        u_data[2].split(":")[1].strip()
                        if u_data[2].find(":") != -1
                        else ""
                    )
            if results.get("skype_id"):
                platform, name, skype_id, location, verified = (
                    "Skype",
                    ",".join(results.get("name")),
                    ",".join(results["skype_id"]),
                    ",".join(results.get("location")),
                    "Yes",
                )
            else:
                platform, name, skype_id, location, verified = "Skype", "", "", "", "No"
            data_writer.writerow([platform, name, skype_id, location, verified])


if __name__ == "__main__":
    PHONE_NUMBER = cred_data["Telegram"]["phone_no"]
    API_ID = cred_data["Telegram"]["api_id"]
    API_HASH = cred_data["Telegram"]["api_hash"]
    client = TelegramClient(PHONE_NUMBER, API_ID, API_HASH)
    client.connect()
    print(client)
    if not client.is_user_authorized():
        client.send_code_request(PHONE_NUMBER)
        try:
            client.sign_in(PHONE_NUMBER, input("Enter the code (sent on telegram): "))
        except errors.SessionPasswordNeededError:
            pw = getpass(
                "Two-Step Verification enabled. Please enter your account password: "
            )
            client.sign_in(password=pw)
    # get_telegram_user_details("+918879007530,+918268291167,+919987773635")
    # get_user_truecaller_details(
    #     "IN",
    #     cred_data=cred_data,
    #     phoneNumber="+918879007530,+918268291167,+919987773635",
    # )
    # get_skype_details(cred_data)
    scrape_skype_details(
        "+918879007530,+918268291167,+919987773635", cred_data
    )  # +918976018468
