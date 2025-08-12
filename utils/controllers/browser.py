import json


class BrowserController(object):
    def __init__(self, browser):
        self.browser = browser

    def get_setup(self):
        settings = {}
        if self.browser.settings != None and self.browser.settings != "":
            try:
                settings = json.loads(self.browser.settings)
            except ValueError as E:
                print("Error")

        browser_config = {
            "crawler" : self.browser.crawler,
            "name" : self.browser.name,
            "priority" : self.browser.priority,
            "settings" : settings,
        }

        return browser_config
