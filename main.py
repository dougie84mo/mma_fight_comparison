# This is a sample Python script.
import pyppeteer
import asyncio
from pyppeteer import launch

SHERDOG_UFC_EVENTS: str = 'https://www.sherdog.com/organizations/Ultimate-Fighting-Championship-UFC-2'
SHERDOG: str = 'https://www.sherdog.com'
# UFC_EVENTS_URL = 'https://www.ufc.com/events'
# UFC_EVENTS_WRAPPER: str = "c-listing__wrapper--horizontal-tabs horizontal-tabs-panes"
PRODUCTION: bool = False
MAX_EVENTS = 20


# Possible RECORD standard for fighters = https://www.sherdog.com/fighter/$NAME


class UFC:
    __events = {}
    _event = None
    __fights = {}
    _fight = None

    def __init__(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.ufc_fight_comparison())
        loop.close()

    async def ufc_fight_comparison(self):
        browser = await pyppeteer.launch(headless=PRODUCTION, defaultViewport=None)
        page = await browser.newPage()
        await page.goto(SHERDOG_UFC_EVENTS)
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
        print(f'{SHERDOG}{self._event}')
        await page.goto(f'{SHERDOG}{self._event}')
        await asyncio.sleep(5)
        await page.waitForSelector(".col_left")
        # No need for headline fight for now
        main = await page.querySelector('.module.fight_card')
        # Lets try this one first.
        card_fights = await page.querySelectorAll('.module.event_match tr.odd, tr.even')
        for fight in card_fights:
            fighter_one = await fight.querySelectorEval('td.text_right a', '''(el) => {
                return [el.getAttribute("href"), el.querySelector("span").innerText]
            }''')
            fighter_two = await fight.querySelectorEval('td.text_left a', '''(el) => {
                return [el.getAttribute("href"), el.querySelector("span").innerText]
            }''')
            fight_name = f'{fighter_one[1]} v. {fighter_two[1]}'
            self.__fights[fight_name] = (fighter_one, fighter_two)
        self._fight = self.choosable_list(self.__fights, "Which fight would you like to repair?  ")
        print(self._fight)
        await browser.close()

    @staticmethod
    async def open_fighter_browser(fighter: list):
        url = fighter[0]
        name = fighter[1]
        browser = await pyppeteer.launch(headless=False, defaultViewport=None)
        pages = await browser.pages()
        await pages[0].goto(f'{SHERDOG}{url}')
        #  I need youtube
        #    - 'Search'
        #    - 'Highlights'
        #    - 'Top - Finishes'
        #    - 'Free Fight'

    @staticmethod
    async def search_fighter_term_videos(browser, fighter_name, search_term="highlights"):
        page = await browser.newPage()
        await page.goto("https://youtube.com")
        



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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    UFC()
