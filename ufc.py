# This is a sample Python script.
import pyppeteer
import asyncio
import sys, os
import json
from table_logger import TableLogger
from pyppeteer import launch

SHERDOG_UFC_EVENTS: str = 'https://www.sherdog.com/organizations/Ultimate-Fighting-Championship-UFC-2'
SHERDOG: str = 'https://www.sherdog.com'
UFC_FP = "https://ufcfightpass.com/home#search"
PRODUCTION: bool = False
SEARCH_TERMS = ['highlights', 'free fight', 'interview', ]
TIMEOUT_UNTIL_LOAD_FLAG = {'waitUntil': 'load', 'timeout': 0}
VIDEO_SEARCH_WRAPPER = "#content.style-scope.ytd-app"


# Possible RECORD standard for fighters = https://www.sherdog.com/fighter/$NAME


class UFC:
    __events = {}
    _event = None
    __fights = {}
    __cache = None
    _fight = None
    config = None

    def __init__(self):
        if os.path.exists('config.json'):
            with open('config.json') as f:
                data = json.load(f)
                self.config = data
        if os.path.exists('cache.json'):
            with open('cache.json') as f:
                data = json.load(f)
                self.__cache = data
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.ufc_fight_comparison())
                loop.close()
            except Exception as e:
                print(e)

    async def ufc_fight_comparison(self):
        # introduce process args
        args = sys.argv
        print(args)
        browser = await pyppeteer.launch(headless=PRODUCTION, defaultViewport=None)
        page = await browser.newPage()
        arg_len = len(args)
        event = int(args[1]) if arg_len >= 2 else -1
        print(event == -1)

        await page.goto(SHERDOG_UFC_EVENTS, TIMEOUT_UNTIL_LOAD_FLAG)
        await page.waitForSelector("#upcoming_tab")
        events_rows = await page.querySelectorAll("#upcoming_tab tr")
        # print(events_rows)
        i = 0
        # Get event name and dates
        FIGHT_DATE_JS = 'el => el.querySelector("div:nth-child(1)").innerText + el.querySelector("div:nth-child(2)").innerText'
        EVENT_NAME_JS = 'el => [el.getAttribute("href"), el.querySelector("span").innerText]'
        eventTable = TableLogger(columns=['event_id', 'date', 'name', 'location'],
                                 colwidth={'event_id': 3, 'date': 5, 'name': 30, 'location': 30})
        for event_row in events_rows:
            if i != 0:
                event_date = await event_row.querySelectorEval('.calendar-date', FIGHT_DATE_JS)
                event_td = await event_row.querySelectorEval('td:nth-child(2) > a:nth-child(1)', EVENT_NAME_JS)
                location = await event_row.querySelectorEval("td:nth-child(3)", 'el => el.innerText')
                eventTable(i, event_date, event_td[1], location)
                # event_name = f'{event_date} {event_td[1]} @ {location}'
                self.__events[i] = event_td[0]
            i += 1

        if event == -1:
            self._event = UFC.basic_list(self.__events, "Which event are you looking for?  ")
        else:
            self._event = self.__events[event]
        with open('cache.json', 'w') as cache_file:
            json.dump(self.__events, cache_file)

        print(f'{SHERDOG}{self._event}')

        await page.goto(f'{SHERDOG}{self._event}', TIMEOUT_UNTIL_LOAD_FLAG)
        await page.waitForSelector(".col-left")

        i = 0
        fightersTable = TableLogger(columns=['id', 'fighter 1', 'fighter 2', 'weight_class'],
                                    colwidth={'id': 3, 'fighter 1': 20, 'fighter 2': 20, 'weight_class': 15})
        FIGHTER_JS = 'el => [el.getAttribute("href"), el.querySelector("span").innerText.replace(/\\r?\\n|\\r/g, " ")]'
        headliner_one = await page.querySelectorEval('div.fighter.left_side > h3 > a', FIGHTER_JS)
        headliner_two = await page.querySelectorEval('div.fighter.right_side > h3 > a', FIGHTER_JS)
        weight_class = await page.querySelectorEval('div.versus .weight_class', 'el => el.innerText')
        fightersTable(i, headliner_one[1].replace("\n", " "), headliner_two[1].replace("\n", " "), weight_class)
        self.__fights[i] = (headliner_one, headliner_two)
        i += 1
        card_fights = await page.querySelectorAll('.new_table_holder [itemprop="subEvent"]')
        # Get the fight card.
        for fight in card_fights:
            fighter_one = await fight.querySelectorEval('.fighter_list.right a', FIGHTER_JS)
            fighter_two = await fight.querySelectorEval('.fighter_list.left a', FIGHTER_JS)
            weight_class = await fight.querySelectorEval('.text_center span.weight_class', 'el => el.innerText')
            fightersTable(i, fighter_one[1], fighter_two[1], weight_class)
            self.__fights[i] = (fighter_one, fighter_two)

            i += 1

        # if arg_len >= 3 and str(args[3]) in self.__fights:
        #     self._fight = self.__fights[str(args[3])]
        # else:
        self._fight = UFC.basic_list(self.__fights, "Which fight would you like to research? ")
        await browser.close()
        for fighter in self._fight:
            print(fighter)
            await self.open_fighter_browser(fighter)
        await asyncio.sleep(5)

        print('Shutting Down Correctly')

    # @staticmethod
    # def fight_name(fighter_one, fighter_two):
    #     return f'{fighter_one[1]} v. {fighter_two[1]}'

    async def open_fighter_browser(self, fighter: list):
        url = fighter[0]
        name = fighter[1]
        browser = await pyppeteer.launch(headless=False, defaultViewport=None)
        pages = await browser.pages()
        await pages[0].goto(f'{SHERDOG}{url}', TIMEOUT_UNTIL_LOAD_FLAG)
        # fight_pass_page = await browser.newPage()
        # if self.config is not None and "fp_email" in self.config and "fp_password" in self.config:
        #     if "@gmail.com" in self.config["fp_email"]:
        #         try:
        #             await fight_pass_page.goto("https://ufcfightpass.com/login")
        #             await fight_pass_page.waitForSelector("#email")
        #             await fight_pass_page.type("#email", self.config["fp_email"])
        #             await asyncio.sleep(1)
        #             await fight_pass_page.type("#secret", self.config["fp_password"])
        #             await asyncio.sleep(1)
        #         except Exception as e:
        #             print(e)
        #     else:
        #         print("Invalid email string or just not a gmail")
        for term in SEARCH_TERMS:
            await UFC.youtube_video_search(browser, name, term)

    @staticmethod
    async def youtube_video_search(browser, fighter_name, search_term="highlights"):
        search_for = f'{fighter_name} {search_term}'
        page = await browser.newPage()
        print(search_for)
        page_url = UFC.search_url(search_for)
        await page.goto(page_url)
        await asyncio.sleep(2)
        await page.waitForSelector(VIDEO_SEARCH_WRAPPER)
        FIRST_VIDEO = 'ytd-page-manager > ytd-search ytd-two-column-search-results-renderer ytd-item-section-renderer ytd-video-renderer:nth-child(1) ytd-thumbnail'
        # content
        await page.click(FIRST_VIDEO)
        await asyncio.sleep(2)
        if search_term == "highlights":
            await page.keyboard.press("m")
        # if search_term == "highlights":

    @staticmethod
    def choosable_list(choices: dict, question: str = 'What choice do you pick?'):
        i = 0
        temp_arr = []
        for choice, rvalue in choices.items():
            # print(f'[{i}]: {choice}')
            i += 1
            temp_arr.append(rvalue)
        answer = None
        while answer is None:
            response = int(input(question))
            if response <= len(temp_arr) - 1:
                answer = temp_arr[response]
            else:
                print('Choice is not available')
        return answer

    @staticmethod
    def basic_list(choices: dict, question: str = 'What choice do you pick?'):
        answer = None
        while answer is None:
            response = int(input(question))
            if response <= len(choices) - 1:
                answer = choices[response]
            else:
                print('Choice is not available')
        return answer

    @staticmethod
    def get_choice(choices, event_num):
        temp = []
        for choice, rv in choices.items():
            temp.append(choice)
        temp_id = event_num if len(temp) - 1 >= event_num >= 0 else 0
        return choices[temp[temp_id]]

    @staticmethod
    def search_url(term):
        return f'https://www.youtube.com/results?search_query={term.replace(" ", "+")}'


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    UFC()
