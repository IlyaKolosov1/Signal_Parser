import requests
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
import time
import pytz
import dotenv
import os

dotenv.load_dotenv()
msc = pytz.timezone('Europe/Moscow')
CHAT_ID = os.getenv('CHAT_ID').split(',')
CHAT_ID = [int(chat_id) for chat_id in CHAT_ID if chat_id.isdigit()]
cheapest_price = float('inf')

bot = Bot(token=os.getenv('BOT_TOKEN'))

url = 'https://web.vibeapp.ru/api/customers/v2/events/577941236/tickets?sort=sale_price&where='

categories = ['%7B%22category%22%3A%22Early+Bird%22%7D', '%7B%22category%22%3A%22Super+Early+Bird%22%7D', '%7B%22category%22%3A%22Standard%22%7D']

dictionary = {
    '%7B%22category%22%3A%22Early+Bird%22%7D': 'Early Bird',
    '%7B%22category%22%3A%22Super+Early+Bird%22%7D': 'Super Early Bird',
    '%7B%22category%22%3A%22Standard%22%7D': 'Standard'
}
def get_cheapest_ticket():

    min_price = float('inf')
    min_url = ''

    for category in categories:
        try:
            response = requests.get(url + category)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    for chat_id in CHAT_ID:
                        bot.send_message(chat_id=chat_id, text=f'No tickets found in {dictionary[category]} category.')
                    continue

                for price in data:
                    if price['total_price'] < min_price:
                        min_price = price['total_price']
                        min_url = price.get('sale_url', 'No URL available')
            else:
                continue
        except Exception as e:
            for chat_id in CHAT_ID:
                bot.send_message(chat_id=chat_id, text=f'Error fetching data: {e}')    

    # min_price = str(min_price)
    # min_price = f'{min_price[:-2]} . {min_price[-2:]}'
    return min_price, min_url

def check_price():
    global cheapest_price
    try:
        min_price, min_url = get_cheapest_ticket()
        if min_price < cheapest_price:
            cheapest_price = min_price
            rub = cheapest_price // 100
            kop = cheapest_price % 100

            message = f'Срочно! Найден билет дешевле!!! ---> : {rub}.{kop:02d} rubles. \n Оплата -->: {min_url}'
            for chat_id in CHAT_ID:
                bot.send_message(chat_id=chat_id, text=message)
        else:
            return

    except Exception as e:
        for chat_id in CHAT_ID:
            bot.send_message(chat_id=chat_id, text=f'Error in check_price: {e}')

def main():   
    scheduler = BackgroundScheduler(timezone=msc)
    scheduler.add_job(check_price, 'interval', minutes=10)
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped.")

if __name__ == '__main__':
    main()
