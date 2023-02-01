from Scraper.TwitterScraper import Scraper as TwitterScraper
import json
import argparse
from decouple import config

parser = argparse.ArgumentParser(
    prog = 'Twitter Follower Scraper',
)
parser.add_argument('--enable-gui', action='store_true')
parser.add_argument('--start-sync', action='store_true')

def twitter_main(user, enable_gui, start_sync):
    controller = TwitterScraper(enable_gui, start_sync)
    login_success = controller.quick_login()
    if not login_success:
        login_success = controller.standard_login(
            config('TWITTER_USER'),
            config('TWITTER_PASS'),
            config('TWITTER_USER_NAME')
        )
    if login_success:
        controller.scrape_followers(user)
    controller.dispose_session()
    print(f'successfully finished scraping [{user}]')

if __name__ == '__main__':
    args = parser.parse_args()
    users = json.loads(open('search.json','r').read())['users']
    for user in users:
        print(f'[USER] -> [{user}]')
        twitter_main(user, args.enable_gui, args.start_sync)