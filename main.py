import dotenv, os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes
import asyncio
import random, time
import logging
import json

dotenv.load_dotenv()
TOKEN = os.getenv('TG_TOKEN')
CHANNEL_ID_MAIN = int(os.getenv('TG_CHANNEL'))
CHANNEL_ID_TEST = int(os.getenv('TG_CHANNEL_TEST'))
MY_ID = int(os.getenv('TG_MY_ID'))
PATH = 'sauce'
BOT_NAME = os.getenv('BOT_NAME')
MAX_IMAGES = 3

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

banned_users = []

with open('banned_users.txt', 'r') as f:
    banned_users = f.read().splitlines()
banned_users = [int(user) for user in banned_users]

user_amounts = {}

user_total = {}
with open('user_total.json', 'r') as f:
    user_total = json.load(f)

# forward photos to MY_ID
async def forward_photo(update: Update, context):
    if time.localtime().tm_hour == 0 and time.localtime().tm_min == 0: # loading banned_users is done at midnight and is not thread safe
        await update.message.reply_text('It is midnight, please wait a minute to avoid glitches :3')
        return
    if str(update.message.from_user.id) in banned_users:
        await update.message.reply_text('This account is not allowed to suggest images')
        return
    user_amounts[update.message.from_user.id] = user_amounts.get(update.message.from_user.id, 0) + 1
    if user_amounts[update.message.from_user.id] == MAX_IMAGES * 3:
        await update.message.reply_text(f'Dude, slow down, the limit is {MAX_IMAGES} images per day, which will reset at midnight UK time')
        return
    if user_amounts[update.message.from_user.id] == MAX_IMAGES:
        await update.message.reply_text(f'You have reached the limit of {MAX_IMAGES} images per day, run /get_limit to see when the limit resets')
        return
    
    photo = update.message.photo[-1].file_id

    caption = f'From: {update.message.from_user.username} ({update.message.from_user.id})'

    keyboard = [
        [InlineKeyboardButton('Approve', callback_data='approve'), InlineKeyboardButton('Reject', callback_data='reject')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(chat_id=MY_ID, photo=photo, caption=caption, reply_markup=reply_markup)

async def verif_button(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == 'approve':
        user_total[int(query.message.caption.split('\n')[0].split(' ')[1])] = user_total.get(int(query.message.caption.split('\n')[0].split(' ')[1]), 0) + 1
        await context.bot.send_photo(chat_id=CHANNEL_ID_MAIN, photo=query.message.photo[-1].file_id)
    else:
        await query.message.delete()

async def get_limit(update: Update, context):
    if update.message.from_user.id not in user_amounts:
        user_amounts[update.message.from_user.id] = 0
    if user_amounts[update.message.from_user.id] >= MAX_IMAGES:
        time_until_midnight = 24 - time.localtime().tm_hour
        await update.message.reply_text('You have reached the limit of 3 images per day, the limit will reset in ' + str(time_until_midnight) + ' hours')
    else:
        await update.message.reply_text('You have ' + str(MAX_IMAGES - user_amounts[update.message.from_user.id]) + ' images left today')

async def start(update: Update, context):
    await update.message.reply_text('Hi there, please send me a photo you would like to be featured')

def pick_random_file(path):
    with open('sent_images.txt', 'r') as f:
        sent_images = f.read().splitlines()
    files = os.listdir(path)
    random.shuffle(files)
    for file in files:
        if file not in sent_images:
            return file
    return None

async def new_channel_photo(update: Update, context):
    if update.message.from_user.id != MY_ID:
        await update.message.reply_text('You are not authorized to send photos')
        return
    file = pick_random_file(PATH)
    if file:
        with open(f'{PATH}/{file}', 'rb') as f:
            await context.bot.send_photo(chat_id=CHANNEL_ID_MAIN, photo=f)
        with open('sent_images.txt', 'a') as f:
            f.write(f'{file}\n')

async def advertise_bot(update: Update, context):
    if update.message.from_user.id != MY_ID:
        await update.message.reply_text('You are not authorized to send photos')
        return
    
    keyboard = [
        [InlineKeyboardButton('Message me', url=f'https://t.me/{BOT_NAME}')]
    ]
    await context.bot.send_message(chat_id=CHANNEL_ID_MAIN, text=f'Message @{BOT_NAME} to suggest images for this channel!', reply_markup=InlineKeyboardMarkup(keyboard))

async def midnight_check_loop():
    while True:
        await asyncio.sleep(60)
        if time.localtime().tm_hour == 0 and time.localtime().tm_min == 0:
            user_amounts.clear()
        with open('banned_users.txt', 'r') as f:
            banned_users = f.read().splitlines()
            banned_users = [int(user) for user in banned_users]

class MyIDFilter(filters.MessageFilter):
    def filter(self, message):
        return message.chat.id == MY_ID

def main():
    app = Application.builder().token(TOKEN).concurrent_updates(5).read_timeout(20).write_timeout(20).build()
    app.add_handler(MessageHandler(filters.PHOTO, forward_photo))
    app.add_handler(CallbackQueryHandler(verif_button))
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('new_photo', new_channel_photo, filters=MyIDFilter()))
    app.add_handler(CommandHandler('advertise', advertise_bot, filters=MyIDFilter()))
    app.add_handler(CommandHandler('get_limit', get_limit))

    loop = asyncio.get_event_loop()
    loop.create_task(midnight_check_loop())
    app.run_polling()

    print('Saving user_total')
    with open('user_total.json', 'w') as f:
        json.dump(user_total, f)

if __name__ == '__main__':
    main()