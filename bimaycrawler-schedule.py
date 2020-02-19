from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from io import open
from ics import Calendar, Event
from ics.alarm import AudioAlarm
from datetime import timedelta

c = Calendar()
e = Event()
c.creator = "cher"
e.name = 'First Event'
e.begin = '2019-11-08T22:00:00+07'
e.duration = {"minutes":100}
e.description = "This is my first event"
e.location = "404-Not Found"
c.events.add(e)

# print(c)

with open('my.ics', 'w') as f:
    f.writelines(c)