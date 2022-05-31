from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot, Message
import sqlite3, logging, cv2, os, datetime, pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials

updater = Updater(token='your token', use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

####################Database functions######################

def enter_customer_database(user_name, table_number, verified):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    cursor.execute("INSERT INTO liveorder VALUES(?,?,?,?,?,?)", (user_name, table_number, 'none', 0, 0, verified))
    connect.commit()
    connect.close()


def verified_database(user_name):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    # magic :)))
    query = "SELECT EXISTS(SELECT 1 FROM liveorder WHERE username = '{}' AND isverified = 'True')".format(user_name)
    verify = cursor.execute(query).fetchall()
    connect.commit()
    connect.close()
    return verify


def category_database(category):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    query = "SELECT *, rowid FROM menu WHERE category = '{}'".format(category)
    items = cursor.execute(query).fetchall()
    connect.commit()
    connect.close()
    return items


def fetch_food_data_database(foodnum):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    query = "SELECT * FROM menu WHERE rowid = {}".format(foodnum)
    items = cursor.execute(query).fetchall()
    connect.commit()
    connect.close()
    return items


def add_order_database(user_name, food, number, price):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    cursor.execute("INSERT INTO liveorder VALUES(?,?,?,?,?,?)", (user_name, 0, food, number, price, 'none'))
    connect.commit()
    connect.close()
    return f"{number} {food}(s) added to your list."


def myorder_database(user_name):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    query = "SELECT * FROM liveorder WHERE username = '{}' AND tablenum = 0".format(user_name)
    items = cursor.execute(query).fetchall()
    connect.commit()
    connect.close()
    return items


def delete_orders_database(user_name):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    query = "DELETE FROM liveorder WHERE username = '{}' AND tablenum = 0".format(user_name)
    cursor.execute(query)
    connect.commit()
    connect.close()
    return 'Your order list is deleted'


def select_order_database(user_name):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    query = "SELECT * FROM liveorder WHERE username = '{}'".format(user_name)
    items = cursor.execute(query).fetchall()
    connect.commit()
    connect.close()
    return items


def logout_database(user_name):
    connect = sqlite3.connect('restaurant.db')
    cursor = connect.cursor()
    query = "DELETE FROM liveorder WHERE username = '{}'".format(user_name)
    cursor.execute(query)
    connect.commit()
    connect.close()
    return 'Goodbye\nHope you enjoyed your meal.'


##################Bot functions#############################

def start(update, context):
    name = update.message.chat.first_name
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Welcome {name}')
    context.bot.send_message(chat_id=update.effective_chat.id,
    text='Please take a picture of the QR code which is on your table and send it to me.')


def register(update, context):
    is_verified = True
    user_name = update.message.chat.username
    if user_name == None:
        user_name = update.message.chat.first_name
    photo = update.message.photo
    photo_id = photo[-1].file_id
    context.bot.get_file(photo_id).download(f"{user_name}.jpg")
    table_number = qr_decoder(user_name)
    if table_number == '':
        update.message.reply_text("Picture in not clear try again.")
        return

    table_number = int(table_number)
    verified = 'True'
    enter_customer_database(user_name, table_number, verified)

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Menu', callback_data='menu')]])
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"So you are sitting at table number {table_number}",
    reply_markup=keyboard)


def qr_decoder(user_name):
    detect = cv2.QRCodeDetector()
    decode = detect.detectAndDecode(cv2.imread(f"{user_name}.jpg"))
    os.remove(f"{user_name}.jpg")
    return decode[0]


def menu (update, context):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Pizza', callback_data = 'pizza'),
            InlineKeyboardButton('Burger', callback_data = 'burger')
            ],
        [
            InlineKeyboardButton('Appetizer', callback_data = 'appetizer'),
            InlineKeyboardButton('Beverage', callback_data = 'beverage')
            ]
        ])
    context.bot.send_message(chat_id=update.effective_chat.id, text='Please choose a category:', reply_markup=keyboard)


def pizza (update, context):
    items = category_database('pizza')
    for item in items:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=item[1],
        caption=f"{item[5]}. {item[2]}\n\nToppings:\n{item[3]}\n\nPrice: ${item[4]}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Back to category", callback_data = 'menu')],
        [InlineKeyboardButton("Order", callback_data = 'order')]
        ])
    context.bot.send_message(chat_id=update.effective_chat.id, text='Want to see other categories?\nor want to order?',
    reply_markup=keyboard)


def burger(update, context):
    items = category_database('burger')
    for item in items:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=item[1],
        caption=f"{item[5]}. {item[2]}\n\nToppings:\n{item[3]}\n\nPrice: ${item[4]}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Back to category", callback_data = 'menu')],
        [InlineKeyboardButton("Order", callback_data = 'order')]
        ])
    context.bot.send_message(chat_id=update.effective_chat.id, text='Want to see other categories?\nor want to order?',
    reply_markup=keyboard)


def appetizer(update, context):
    items = category_database('appetizer')
    for item in items:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=item[1],
        caption=f"{item[5]}. {item[2]}\n\nPrice: ${item[4]}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Back to category", callback_data = 'menu')],
        [InlineKeyboardButton("Order", callback_data = 'order')]
        ])
    context.bot.send_message(chat_id=update.effective_chat.id, text='Want to see other categories?\nor want to order?',
    reply_markup=keyboard)


def beverage(update, context):
    items = category_database('beverage')
    for item in items:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=item[1],
        caption=f"{item[5]}. {item[2]}\n\nPrice: ${item[4]}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Back to category", callback_data = 'menu')],
        [InlineKeyboardButton("Order", callback_data = 'order')]
        ])
    context.bot.send_message(chat_id=update.effective_chat.id, text='Want to see other categories?\nor want to order?',
    reply_markup=keyboard)


def order_structure (update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
    text='''To order use this structure:
Number of the food - How many you want

For example:
3 - 2  -> means you want 2 Pepperoni pizzas
7 - 1  -> means you want a cheese burger

Enjoy ordering ...''')


def order(update, context):
    items = update.message.text
    user_name = update.message.chat.username
    if user_name == None:
        user_name = update.message.chat.first_name

    verify = verified_database(user_name)
    verified = None
    for i in verify:
        verified = i[0]
    if not verified:
        update.message.reply_text("I don't know which table you're sitting at. Please hit /start first.")
        return

    try:
        order = []
        for item in items:
            if item == ' ':
                pass
            else:
                order.append(item)

        index = order.index('-')
        foodnum = int(''.join(order[:index]))

        nums = order[index:]
        newnums = []
        for num in nums:
            if num == '-':
                pass
            else:
                newnums.append(num)
        number = int(''.join(newnums))
    except ValueError:
        update.message.reply_text("Usage error:\nNumber of the food - How many you want")
        return

    food_data = fetch_food_data_database(foodnum)
    food = None
    price = None
    for item in food_data:
        food = item[2]
        price = item[4]

    added = add_order_database(user_name, food, number, price)

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Back to category", callback_data = 'menu')]])
    update.message.reply_text(f'''{added}\n
If you want to see your list use /myorder commend.
When you're done ordering use /done command.
You can /delete your order list and start over.''', reply_markup=keyboard)


def myorder(update, context):
    user_name = update.message.chat.username
    if user_name == None:
        user_name = update.message.chat.first_name

    verify = verified_database(user_name)
    verified = None
    for i in verify:
        verified = i[0]
    if not verified:
        update.message.reply_text("I don't know which table you're sitting at. Please hit /start first.")
        return

    items = myorder_database(user_name)
    orders = 'You orderd:\n'
    cost = 0
    for item in items:
        order = f'{item[3]} {item[2]}(s)\n'
        orders = orders + order
        cost = cost + item[4] * item[3]
    orders = orders + f'Total cost: ${cost}'

    update.message.reply_text(orders)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Back to category", callback_data = 'menu')]])
    update.message.reply_text("Let me know if you're /done.\nYou can /delete your order list if you want.",
    reply_markup=keyboard)


def delete(update, context):
    user_name = update.message.chat.username
    if user_name == None:
        user_name = update.message.chat.first_name

    verify = verified_database(user_name)
    verified = None
    for i in verify:
        verified = i[0]
    if not verified:
        update.message.reply_text("I don't know which table you're sitting at. Please hit /start first.")
        return

    delete = delete_orders_database(user_name)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Back to category", callback_data = 'menu')]])
    update.message.reply_text(delete, reply_markup=keyboard)


def done(update, context):
    time = datetime.datetime.now(pytz.timezone('Asia/Tehran'))
    user_name = update.message.chat.username
    if user_name == None:
        user_name = update.message.chat.first_name

    verify = verified_database(user_name)
    verified = None
    for i in verify:
        verified = i[0]
    if not verified:
        update.message.reply_text("I don't know which table you're sitting at. Please hit /start first.")
        return

    items = select_order_database(user_name)
    table_number = 0
    cost = 0
    orders = ""
    for item in items:
        if not item[1] == 0:
            table_number = item[1]
        else:
            cost = cost + item[4] * item[3]
            orders = orders + str(item[3]) + ' ' + item[2] + '(s)' + '\n'

    done = add_to_sheet(str(time), user_name, table_number, orders, str(cost))
    delete_orders_database(user_name)
    update.message.reply_text(done)
    update.message.reply_text(f'{orders}For table number {table_number}\nTotal cost: ${cost}')
    update.message.reply_text('Please /logout when you want to leave the restaurant')


def logout(update, context):
    user_name = update.message.chat.username
    if user_name == None:
        user_name = update.message.chat.first_name

    verify = verified_database(user_name)
    verified = None
    for i in verify:
        verified = i[0]
    if not verified:
        update.message.reply_text("I don't know which table you're sitting at. Please hit /start first.")
        return

    logout = logout_database(user_name)
    update.message.reply_text(logout)
    update.message.reply_text('Please hit /start when you came back.')


#############Google sheet functions#################

def add_to_sheet(time, user_name, table_number, orders, cost):
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open('Orders').sheet1

    row = [time, user_name, table_number, orders, '$'+cost]
    sheet.append_row(row)
    return "Done!\nYour order is being processed ..."

def clear_sheet(update, context):
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open('Orders').sheet1
    sheet.clear()
    row = ['Date/Time', 'User name', 'Table number', 'Order', 'Total cost']
    sheet.append_row(row)
    update.message.reply_text('ADMIN MODE:\n\nYour sheet is clear now.')


################Handlers######################
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('myorder', myorder))
dispatcher.add_handler(CommandHandler('done', done))
dispatcher.add_handler(CommandHandler('delete', delete))
dispatcher.add_handler(CommandHandler('logout', logout))
dispatcher.add_handler(CallbackQueryHandler(pizza, pattern='pizza'))
dispatcher.add_handler(CallbackQueryHandler(burger, pattern='burger'))
dispatcher.add_handler(CallbackQueryHandler(appetizer, pattern='appetizer'))
dispatcher.add_handler(CallbackQueryHandler(beverage, pattern='beverage'))
dispatcher.add_handler(CallbackQueryHandler(menu, pattern='menu'))
dispatcher.add_handler(CallbackQueryHandler(order_structure, pattern='order'))
dispatcher.add_handler(MessageHandler(Filters.text & (~ Filters.command), order))
dispatcher.add_handler(MessageHandler(Filters.photo, register))
dispatcher.add_handler(CommandHandler('clearsheetadminmode', clear_sheet))

updater.start_polling()
updater.idle()
