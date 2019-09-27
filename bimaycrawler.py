from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from io import open
import os
import time
import requests
import getpass

def cleanName(name):
    banned = ['\\', '/', ':', '*', '?', '"', '<', '>', '|' ]
    for c in banned:
        name = name.replace(c, "")
    return name

def changeUrl(link, value, id):
    reversed_link = link[::-1]
    first_slash = reversed_link.index('/')
    removed_id_link = reversed_link[first_slash+1:]
    second_slash = removed_id_link.index('/')
    removed_value_link = removed_id_link[second_slash+1:]
    clean_link = removed_value_link[::-1]
    new_link = clean_link+'/'+value+'/'+id
    return new_link

def getExtension(link):
    link = link[::-1]
    dot_index = link.index('.')
    link = link[:dot_index]
    link = link[::-1]
    return link

print("Input your username: ", end='')
user_name = input()

password = getpass.win_getpass("Input your password: ")

# options = Options()
# options.headless = True
try:
    driver = webdriver.Chrome()
except WebDriverException:
    print("Please download chromedriver executable and place it in the same directory as the python script or add it to your PATH")
    print("You can get the chromedriver here: https://sites.google.com/a/chromium.org/chromedriver/home")
    input("Press enter to continue...")
    quit()
driver.get('https://binusmaya.binus.ac.id/login/')
driver.find_element_by_css_selector("input[type='text']").send_keys(user_name)
driver.find_element_by_css_selector("input[type='password']").send_keys(password)
driver.find_element_by_css_selector("input[type='submit']").click()


try:
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[id='widget-current-courses'] li a")))
except TimeoutException:
    print("Loading took too long!")
    driver.quit()
    quit()

bimay_level1 = BeautifulSoup(driver.page_source, 'html.parser')

courses = bimay_level1.select("ul[id='widget-current-courses'] li a")

try:
    os.mkdir("./resources")
except FileExistsError as e:
    pass

for course in courses:
    course_name = course.text
    pwd = "./resources/"
    pwd += cleanName(course_name)
    try:
        os.mkdir(pwd)
    except FileExistsError:
        pass
    #pindah ke course lain, dengan ganti url
    driver.get('https://binusmaya.binus.ac.id/newStudent/') #mesti balik ke main page, kalau engga, kode class ga ganti
    url = course['href'].replace("info", "resources")
    driver.get(url)

    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[id='listNav']")))
    except TimeoutException:
        print("Loading took too long!")
        driver.quit()
        quit()
    bimay_level2 = BeautifulSoup(driver.page_source, 'html.parser')
    classes = bimay_level2.select("select[id='ddlclasslist'] option") #ngeliat klo ad kelas
    for c in classes:
        c_value = c['value']
        c_id = c['ssr-id']
        link = changeUrl(url, c_id, c_value)
        driver.get('https://binusmaya.binus.ac.id/newStudent/') #mesti balik ke main page, kalau engga, resourcenya ga muncul
        driver.get(link)
        pwd2 = pwd + '/' + c.text
        print(course.text+" ("+c.text+")")
        try:
            os.mkdir(pwd2)
        except FileExistsError:
            pass
        
        no_data = False

        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='topic']>a>h4")))
        except TimeoutException:
            if EC.presence_of_element_located((By.CSS_SELECTOR, "div[id='resource']>article[class='iLoading']>p")):
                print("The class "+course.text+" has no resources!")
                no_data = True
            else:
                print("Loading took too long!")
                driver.quit()
                quit()
        if no_data:
            continue
        bimay_level3 = BeautifulSoup(driver.page_source, 'html.parser')
        topics = bimay_level3.select("div[class='topic']>a>h4")
        sessions = bimay_level3.select("h3[class='iWeek']")
        dates = bimay_level3.select("h4[class='iWeekDescr']")
        resource_count = len(topics)
        sessions.pop(0) #index pertama di pop karena ada template yg punya css selector sama jadi dibersihkan
        dates.pop(0) #sama dengan sessions.pop(0)
        files = bimay_level3.select("li[class='detailFiles']>div>a[class='iDownload icon icon-download']")
        for i in range(int(resource_count)):
            topic = topics[i].text
            session = sessions[i].text
            date = dates[i].text
            pfile = files[i]
            file_link = pfile['href']
            file_name = session+" "+topic+" ("+date+")"+"."+getExtension(file_link)
            file_name = cleanName(file_name)

            download_file = requests.get(file_link, allow_redirects=True)

            print("Downloading "+file_name)
            with open(pwd2+"/"+file_name, "wb") as f:
                f.write(download_file.content)

print("Finished downloading!")
driver.quit()