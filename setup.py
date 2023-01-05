from Scraper.TwitterScraper import Scraper as TwitterScraper
from ConfigCelery.CeleryWorker import CeleryWorker
import os
import argparse
from decouple import config


worker = CeleryWorker(config('REDIS_URL'))
task_routes = (['Twitter Scraper','Twitter Queue'])
module_locations = ['setup']
worker.discover_and_set_task_routes(task_routes, module_locations)

def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user")
    return parser.parse_args()

@worker.app.task(name='Twitter Scraper')
def pusher(user):
    controller = TwitterScraper()
    if os.path.isfile('cookies.pkl'): controller.quick_login()
    else: controller.standard_login(config('TWITTER_USER'), config('TWITTER_PASS'))
    controller.scrape_followers(user)

if __name__ == '__main__':
    args = parser()
    user = args.user
    if user:
        worker.app.worker_main(worker.start_args)
        pusher.delay(args=([user]))