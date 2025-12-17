import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

class ll_ATS(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()

    def test_ll(self):
        user = "testuser"
        pwd = "test123"

        driver = self.driver
        driver.maximize_window()
        driver.get("http://127.0.0.1:8000/admin")

        elem = driver.find_element(By.ID,"id_username")
        elem.send_keys(user)
        elem = driver.find_element(By.ID,"id_password")
        elem.send_keys(pwd)
        time.sleep(3)
        elem.send_keys(Keys.RETURN)
        driver.get("http://127.0.0.1:8000")
        time.sleep(3)

        try:
             # attempt to find the 'Logout' button - if found, logged in
            elem = driver.find_element(By.ID, "Login")
            driver.close()
            self.fail("Login Failed - user may not exist")
            assert False
        except NoSuchElementException:
            driver.close()
            assert True
        time.sleep(3)

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main(warnings='ignore')