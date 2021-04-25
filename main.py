# This is a sample Python script.
import pyppeteer
import asyncio
from pyppeteer import launch

SHERDOG_UFC_EVENTS: str = 'https://www.sherdog.com/organizations/Ultimate-Fighting-Championship-UFC-2'
UFC_EVENTS_URL = 'https://www.ufc.com/events'
UFC_EVENTS_WRAPPER: str = "c-listing__wrapper--horizontal-tabs horizontal-tabs-panes"
PRODUCTION: bool = False


# Possible RECORD standard for fighters = https://www.sherdog.com/fighter/$NAME


class UFC:
    # __events = []
    _event = None
    # __fights = []
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
        fights_table = await page.querySelector("#upcoming_tab")
        print(fights_table)
        fights_rows = await fights_table.querySelectorAll(".odd, .even")
        print(fights_rows)
        for fight_row in fights_rows:
            fight_date = await fight_row.querySelectorEval('td:nth-child(1)', '''(el) => {
                return el.querySelector(".month") + el.querySelector(".day");
            }''')
            fight_td = await fight_row.querySelectorEval('td:nth-child(2)', '''(el) => {
                return [el.querySelector("a").getAttribute("href"), el.querySelector("span").innerText];
            }''')

        await browser.close()


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
        return answer


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    UFC()
