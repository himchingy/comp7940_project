from telegram import Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackContext)
# The messageHandler is used for all message updates
import configparser
import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

from ChatGPT_HKBU import HKBU_ChatGPT

def equiped_chatgpt(update,context, prompt, reply):
    global chatgpt 
    reply_message = chatgpt.submit(prompt)
    logging.info("Update: "+str(update))
    logging.info("context: "+str(context))
    if reply:
        context.bot.send_message(chat_id=update.effective_chat.id,text=reply_message)
    return reply_message

def main():
    # Load your token and create an Updater for your Bot
    config = configparser.ConfigParser()
    config.read('config.ini')
    updater = Updater(token = (config['TELEGRAM']['ACCESS_TOKEN']), use_context = True)
    dispatcher = updater.dispatcher

	# You can set this logging module, so you will know when and why things do not work as expected. Meanwhile, update your config.ini as:
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    global chatgpt 
    chatgpt=HKBU_ChatGPT()

    # Message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

	# Command Handlers
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("hello", hello_command))
    dispatcher.add_handler(CommandHandler("add", add_command))

	# To start the bot:
    updater.start_polling()
    updater.idle()
    
def echo(update, context):
	reply_message = update.message.text.upper()
	logging.info("Update: "+str(update))
	logging.info("context: "+str(context))
	context.bot.send_message(chat_id = update.effective_chat.id, text = reply_message)

# Provide help tips for /Help command
def help_command(update: Update, context: CallbackContext) -> None:
	"""Send a message when the command/ help is issued."""
	update.message.reply_text('Helping you helping you.')

# Inititate the chat for /Hello command    
def hello_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command/ hello is issued."""
    update.message.reply_text('Welcome to GoHiking chatbot.')
    update.message.reply_text('I can provide you advice on hiking routes and share your hiking photos with others.\nWhat would you like to do now?')

# Handle user's input
def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.lower()
    hiking_prompt = "if the user wants to express his intention to go hiking, then reply me 'go hiking'; "
    welcome_prompt = "if the user says greeting message, then reply me 'welcome'; "
    share_prompt = "if the user wants to share something with others, then reply me 'share'; "
    hiking_district_prompt = "if the user replies a place in Hong Kong, then reply me 'hiking location'; "
    add_record_prompt = "if the user want to add a hiking record, then reply me 'add'; "
    prompt = "Please analyze this user's input enclosed by **: **" + user_input +"**. " + welcome_prompt + hiking_prompt + share_prompt + hiking_district_prompt + add_record_prompt + " if none of the above, reply me 'none'. Please just give me the result keyword."
#    print(prompt)
    gptResult = equiped_chatgpt(update, context, prompt, False)
    print(gptResult)

    # Give response based on ChatGPT result
    if gptResult == 'welcome':
        update.message.reply_text('Welcome to GoHiking chatbot.')
        update.message.reply_text('I can provide you advice on hiking routes and share your hiking photos with others.\nWhat would you like to do now?')
    elif (gptResult == 'go hiking'):
        prompt = "Please act as a chatbot to provide a short answer to this statement: " + user_input +". And then ask the user which district does he want to go."
        gptResult = equiped_chatgpt(update, context, prompt, True)
    elif (gptResult == 'hiking location'):
        update.message.reply_text('Let me search...please wait for a while...')
        prompt = "Please list the hiking routes in the location mentioned **" + user_input + "**. PLease rate the hiking difficuty with 5 stars as the most difficult one and also enclose the route name with **"
        gptResult = equiped_chatgpt(update, context, prompt, True)
    elif (gptResult == 'add'):
        update.message.reply_text('Please add hiking record by /add command in the following format...')
        update.message.reply_text('e.g. /add (hiking date), (route name), (weather), (difficulty 1-5), (comment)')

    elif (gptResult == 'share'):
        update.message.reply_text('Please share the details of the hiking route, including the date, route name, weather, difficulty, and comments.')
    
    else:
        update.message.reply_text('I am sorry. As a hiking chatbot, I can only response to topics related to hiking. You can ask me questions or seek advice about hiking. :)')


def read_record(update, context):
    reply_message = update.message.text.lower()
    return reply_message

# Define the share command handler
def share(update: Update, context: CallbackContext) -> None:
    """Initiate the process of sharing a hiking route and photos."""
    update.message.reply_text('Please share the details of the hiking route, including the date, route name, weather, difficulty, and comments.')

# Define the record handler
def add_command(update: Update, context: CallbackContext) -> None:
    # Initialize Firebase
#    cred = credentials.Certificate('./serviceAccountKey.json')
#    firebase_admin.initialize_app(cred)

    # Create a Firestore client
    db = firestore.client()

    user_username = update.message.from_user.username
    date = update.message.date.strftime('%Y-%m-%d')
    record = update.message.text
    record = record.replace('/add ', '')
    split_data = record.split(',')
    print(user_username)
    print(date)
    print(split_data)
    
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y_%m_%d_%H_%M_%S")
    
    collection_name = 'hiking_record'
    document_name = 'record_' + formatted_datetime
    data = {
        'user': user_username,
        'date': split_data[0],
        'name': split_data[1],
        'weather': split_data[2],
        'difficulty': split_data[3],
        'comment': split_data[4],
    }
    
    doc_ref = db.collection(collection_name).document(document_name)
    doc_ref.set(data)
    print("Data saved successfully!")
    update.message.reply_text('Record saved!')
    
if __name__=='__main__':
    main()