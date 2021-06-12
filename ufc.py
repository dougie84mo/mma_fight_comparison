# This is a sample Python script.
import pyppeteer
import asyncio
import sys
import json
from pyppeteer import launch

SHERDOG_UFC_EVENTS: str = 'https://www.sherdog.com/organizations/Ultimate-Fighting-Championship-UFC-2'
SHERDOG: str = 'https://www.sherdog.com'
PRODUCTION: bool = False
SEARCH_TERMS = ['highlights', 'free fight']
TIMEOUT_UNTIL_LOAD_FLAG = {'waitUntil': 'load', 'timeout': 0}
HEADLINER_JS = '''(el) => {
            let name = el.querySelector("h3 a")
            return [name.getAttribute("href"), name.querySelector("span").innerText]
        }'''

# Possible RECORD standard for fighters = https://www.sherdog.com/fighter/$NAME


class UFC:
    __events = {}
    _event = None
    __fights = {}
    _fight = None

    def __init__(self):

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.ufc_fight_comparison())
            loop.close()
        finally:
            with open('cache.json', 'w') as cache_file:
                json.dump(self.__events, cache_file)

    async def ufc_fight_comparison(self):
        # introduce process args
        args = sys.argv
        browser = await pyppeteer.launch(headless=PRODUCTION, defaultViewport=None)
        page = await browser.newPage()
        arg_len = len(args)
        event = int(args[1]) if arg_len >= 2 else -1
        print(event == -1)
        if event == -1:
            print(event == -1)
            await page.goto(SHERDOG_UFC_EVENTS, TIMEOUT_UNTIL_LOAD_FLAG)
            await page.waitForSelector("#upcoming_tab")
            events_rows = await page.querySelectorAll("#upcoming_tab tr.odd, #upcoming_tab tr.even")
            # print(events_rows)
            for event_row in events_rows:
                event_date = await event_row.querySelectorEval('td:nth-child(1)', '''(el) => {
                                    return el.querySelector(".month").innerText + el.querySelector(".day").innerText;
                                }''')
                event_td = await event_row.querySelectorEval('td:nth-child(2)', '''(el) => {
                                    return [el.querySelector("a").getAttribute("href"), el.querySelector("span").innerText];
                                }''')
                event_name = f'{event_date} {event_td[1]}'
                self.__events[event_name] = event_td[0]

            self._event = UFC.choosable_list(self.__events, "Which event are you looking for?  ")
            with open('cache.json', 'w') as cache_file:
                json.dump(self.__events, cache_file)
        else:
            with open('cache.json') as cache_file:
                cache_json = json.load(cache_file)
                self.__events = cache_json
            self._event = UFC.get_choice(self.__events, event)
            print(f'{SHERDOG}{self._event}')
        print(self._event)
        await page.goto(f'{SHERDOG}{self._event}', TIMEOUT_UNTIL_LOAD_FLAG)

        await page.waitForSelector(".col_left")
        headliner_one = await page.querySelectorEval('div.fighter.left_side', HEADLINER_JS)
        headliner_two = await page.querySelectorEval('div.fighter.right_side', HEADLINER_JS)
        self.__fights[UFC.fighter_name(headliner_one, headliner_two)] = (headliner_one, headliner_two)
        card_fights = await page.querySelectorAll('.module.event_match tr.odd, tr.even')
        for fight in card_fights:
            fighter_one = await fight.querySelectorEval('td.text_right a', '''(el) => {
                return [el.getAttribute("href"), el.querySelector("span").innerText]
            }''')
            fighter_two = await fight.querySelectorEval('td.text_left a', '''(el) => {
                return [el.getAttribute("href"), el.querySelector("span").innerText]
            }''')
            fight_name = UFC.fighter_name(fighter_one, fighter_two)
            self.__fights[fight_name] = (fighter_one, fighter_two)

        if arg_len >= 3 and str(args[3]) in self.__fights:
            self._fight = self.__fights[str(args[3])]
        else:
            self._fight = self.choosable_list(self.__fights, "Which fight would you like to research? ")
        await browser.close()
        for fighter in self._fight:
            print(fighter)
            await UFC.open_fighter_browser(fighter)
        await asyncio.sleep(5)

        print('Shutting Down Correctly')

    @staticmethod
    def fighter_name(fighter_one, fighter_two):
        return f'{fighter_one[1]} v. {fighter_two[1]}'

    @staticmethod
    async def open_fighter_browser(fighter: list):
        url = fighter[0]
        name = fighter[1]
        browser = await pyppeteer.launch(headless=False, defaultViewport=None)
        pages = await browser.pages()
        await pages[0].goto(f'{SHERDOG}{url}', TIMEOUT_UNTIL_LOAD_FLAG)
        for term in SEARCH_TERMS:
            await UFC.fighter_video(browser, name, term)

    @staticmethod
    async def fighter_video(browser, fighter_name, search_term="highlights"):
        search_for = f'{fighter_name} {search_term}'
        page = await browser.newPage()
        await page.goto("https://youtube.com")
        await page.waitForSelector("#search")
        await page.type("#search", search_for)
        await asyncio.sleep(4)
        await page.click("#search-icon-legacy")
        print(search_for)
        if search_term == "highlights":
            await page.waitForSelector("ytd-video-renderer")
            await asyncio.sleep(2)
            await page.click("ytd-video-renderer")
            await asyncio.sleep(4)
            await page.keyboard.press("m")

    @staticmethod
    def choosable_list(choices: dict, question: str = 'What choice do you pick?'):
        i = 0
        temp_arr = []
        for choice, rvalue in choices.items():
            print(f'[{i}]: {choice}')
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
    def get_choice(choices, event_num):
        temp = []
        for choice, rv in choices.items():
            temp.append(choice)
        temp_id = event_num if len(temp) - 1 >= event_num >= 0 else 0
        return choices[temp[temp_id]]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    UFC()
