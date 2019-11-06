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

# option headless untuk menjalankan chrome driver tanpa terbuka window chrome
# options = Options()
# options.headless = True

#nngecek ada apa ga chrome drivernya
try:
    driver = webdriver.Chrome()
except WebDriverException:
    print("Please download chromedriver executable and place it in the same directory as the python script or add it to your PATH")
    print("You can get the chromedriver here: https://sites.google.com/a/chromium.org/chromedriver/home")
    input("Press enter to continue...")
    quit()

#input email dan password user
print("Input your username: ", end='')
user_name = input()
password = getpass.win_getpass("Input your password: ")
driver.get('https://binusmaya.binus.ac.id/login/')
driver.find_element_by_css_selector("input[type='text']").send_keys(user_name)
driver.find_element_by_css_selector("input[type='password']").send_keys(password)
driver.find_element_by_css_selector("input[type='submit']").click()

#webdriverwait ini nunggu kalau css selector tersebut udah muncul di layar (soalnya loading bimay async), kalau lewat 30 detik bakal throw exception
try:
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[id='widget-current-courses'] li a")))
except TimeoutException:
    print("Loading took too long!")
    driver.quit()
    quit()

#ngambil link" courses pada homepage dengan module beautiful soup lalu dimasukin ke list
bimay_level1 = BeautifulSoup(driver.page_source, 'html.parser')
courses = bimay_level1.select("ul[id='widget-current-courses'] li a")

#buat folder baru
try:
    os.mkdir("./resources")
except FileExistsError as e:
    pass

#looping tiap link course yg ada di array courses
for course in courses:
    #course text itu kayak .textContent kalau javascript, intinya ambil text dari tag <a></a>
    course_name = course.text

    #buat folder dengan nama coursenya, terus namanya mesti di bersihkan, karena ada course dengan karakter terlarang kayak colon(:) dll
    pwd = "./resources/"
    pwd += cleanName(course_name)
    try:
        os.mkdir(pwd)
    except FileExistsError:
        pass


    #masuk ke dalam link course, dan lgsg nembak halaman resource
    driver.get('https://binusmaya.binus.ac.id/newStudent/') #mesti balik ke main page, kalau engga, kode class ga ganti
    url = course['href'].replace("info", "resources")
    driver.get(url)

    #cek kalau resource udah load karena loading async
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[id='listNav']")))
    except TimeoutException:
        print("Loading took too long!")
        driver.quit()
        quit()

    #masukin kelas" ke dalam list classes, karena ada matkul course 2, misal LAB dan LEC
    bimay_level2 = BeautifulSoup(driver.page_source, 'html.parser')
    classes = bimay_level2.select("select[id='ddlclasslist'] option") #ngeliat klo ad kelas
    for c in classes:
        #akses kelas" tersebut dengan masukin url manual
        c_value = c['value']
        c_id = c['ssr-id']
        link = changeUrl(url, c_id, c_value)
        driver.get('https://binusmaya.binus.ac.id/newStudent/') #mesti balik ke main page, kalau engga, resourcenya ga muncul
        driver.get(link)
        
        #buat folder untuk tiap class
        pwd2 = pwd + '/' + c.text
        print(course.text+" ("+c.text+")")
        try:
            os.mkdir(pwd2)
        except FileExistsError:
            pass
        
        #validasi dibawah ini untuk cek kalau misalnya matakuliah atau class gaad resourcenya sama sekali, misalnya EESE
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

        #masukin judul resource, sesi keberapa, dan tanggal
        bimay_level3 = BeautifulSoup(driver.page_source, 'html.parser')
        topics = bimay_level3.select("div[class='topic']>a>h4")
        sessions = bimay_level3.select("h3[class='iWeek']")
        dates = bimay_level3.select("h4[class='iWeekDescr']")
        resource_count = len(topics)
        sessions.pop(0) #index pertama di pop karena ada template yg punya css selector sama jadi dibersihkan
        dates.pop(0) #sama dengan sessions.pop(0)

        #masukin download link ke list files
        files = bimay_level3.select("li[class='detailFiles']>div>a[class='iDownload icon icon-download']")
        for i in range(int(resource_count)):

            #looping ini buat bikin nama file dengan format sesi, judul, tanggal + extension
            topic = topics[i].text
            session = sessions[i].text
            date = dates[i].text
            pfile = files[i]
            file_link = pfile['href']
            file_name = session+" "+topic+" ("+date+")"+"."+getExtension(file_link)
            file_name = cleanName(file_name)

            #download filenya secara binary, terus masukin ke folder
            download_file = requests.get(file_link, allow_redirects=True)
            print("Downloading "+file_name)
            with open(pwd2+"/"+file_name, "wb") as f:
                f.write(download_file.content)

print("Finished downloading!")
driver.quit()