from telegram import Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackContext)
import os
import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urljoin

from ChatGPT_HKBU import HKBU_ChatGPT

def equiped_chatgpt(update,context, prompt, reply):
    global chatgpt 
    reply_message = chatgpt.submit(prompt)
    logging.info("Update: "+str(update))
    logging.info("context: "+str(context))

    if reply:
        context.bot.send_message(chat_id=update.effective_chat.id,text=reply_message)
    return reply_message

# Get the image links from a URL
def get_image_links(url):
    # Send a GET request
    response = requests.get(url)

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table with the class 'content'
    table = soup.find('table')

    # Find all image tags within this table
    images = table.find_all('img')

    # Extract the 'src' attribute from each image tag
    image_links = [urljoin(url, img['src']) for img in images]

    # Filter the list to include only .jpg and .png images
    image_links = [link for link in image_links if link.endswith('.jpg') or link.endswith('.png')]

    return image_links

# Search for a specific text in the table and return the URL
def search_afcd(url, target_text):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    target_url = None

    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if cells:
            link = cells[0].find('a')
            if link and target_text in link.get_text():
                target_url = urljoin(url, link['href'])
                break

    if target_url:
        # print(f"URL for '{target_text}': {target_url}")
        return get_image_links(target_url)

    else:
        None

def main():
    # Load your token and create an Updater for your Bot
#    updater = Updater(token = (os.environ['TELEGRAM_ACCESS_TOKEN']), use_context = True)
    updater = Updater(token = (os.environ.get('TELEGRAM_ACCESS_TOKEN')), use_context = True)
    dispatcher = updater.dispatcher

	# You can set this logging module, so you will know when and why things do not work as expected. Meanwhile, update your config.ini as:
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Initialize Firebase
    try:
        cred = credentials.Certificate('./serviceAccountKey.json')
#        cred = credentials.Certificate(os.envirn['SERVICE_ACCOUNT_KEY'])
        firebase_admin.initialize_app(cred)    
    except:
        pass
    
    # Create a Firestore client
    global db
    db = firestore.client()

    global chatgpt 
    chatgpt=HKBU_ChatGPT()

    # Message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

	# Command Handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("add", add_command))
    dispatcher.add_handler(CommandHandler("record", show_record))

	# To start the bot:
    updater.start_polling()
    updater.idle()

# Inititate the chat for /Start command    
def start_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command/ start is issued."""
    update.message.reply_text('Welcome to GoHiking chatbot.')
    
#    legend_path = os.path.join('imgs', 'AFCD_Country_Park_Map_Legend.jpg')
#    resized_image_path = os.path.join('imgs', 'resized_image.jpg')

    # Open the image file
#    with Image.open(image_path) as img:
#        # Resize the image
#        max_size = (5000, 5000)  # Max width and height
#        img.thumbnail(max_size)

        # Save the resized image to a new file
#        img.save('.\APP\imgs\resized_image.jpg')

    # Open the resized image file in binary mode
    with open('./imgs/resized_image.jpg', 'rb') as photo:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)
    
    with open('./imgs/AFCD_Country_Park_Map_Legend.jpg', 'rb') as photo:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)

    update.message.reply_text('\n\nI can recommend Hong Kong hiking routes based on your preference. Please select a location based on Agriculture, Fisheries and Conservation Department offical country park map and your preferred difficulty.\n\n(Location)\n(Difficulty)')

# Handle user's input
def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.lower()
    welcome_prompt = "if the user says greeting message, then reply me 'welcome'; "
    hiking_district_prompt = "if the user replies a place or a country park in Hong Kong, then reply me 'hiking location'; "
    add_record_prompt = "if the user want to add a hiking record, then reply me 'add'; "
    search_record_prompt = "if the user want to search hiking records, then reply me 'search'; "
    prompt = "Please analyze this user's input enclosed by **: **" + user_input +"**. " + welcome_prompt + hiking_district_prompt + add_record_prompt + search_record_prompt + " if none of the above, reply me 'none'. Please just give me the result keyword."
    gptResult = equiped_chatgpt(update, context, prompt, False)
    
    print(prompt, gptResult)

    # Give response based on ChatGPT result
    if gptResult == 'welcome':
        update.message.reply_text('Welcome to GoHiking chatbot.')
        update.message.reply_text('I can provide you advice on hiking routes.\nWhich trail would you like to explore?')
    elif (gptResult == 'hiking location'):
        update.message.reply_text('Let me think...please wait for a while...')
        prompt = "Please recommend a hiking route in the location mentioned **" + user_input + "**. PLease rate the hiking difficuty with 5 stars as the most difficult one and also enclose the route name with **"
        gptResult = equiped_chatgpt(update, context, prompt, True)

        # See if there are any photos for the location
        update.message.reply_text('Looking for country park photos...please wait for a while...')
        identify_country_park_prompt = "Please identify the country park in recommended by gptResult **" + gptResult + "**. If the result is not a country park in Hong Kong, then reply me with the name of the country park but without adding the word country park in it. If it is not a country park in Hong Kong, then reply me 'none'."
        identify_country_park_prompt_result = equiped_chatgpt(update, context, identify_country_park_prompt, False)
        print(identify_country_park_prompt_result)

        img_urls = search_afcd('https://www.afcd.gov.hk/english/country/cou_lea/the_facts.html', identify_country_park_prompt_result)
        print(img_urls)
        if img_urls != None:
            update.message.reply_text('Here are some photos of the country park:')
            for img_url in img_urls:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=img_url)
        else:
            update.message.reply_text("No official photos from AFCD are available for the trail you have chosen.")

    elif (gptResult == 'add'):
        update.message.reply_text('Please add hiking record by /add command in the following format...')
        update.message.reply_text('e.g. /add 01/11/2011, Shing Mun, Sunny, 3, Nice weather hiking with friends')
    elif (gptResult == 'search'):
        update.message.reply_text('Please use /search command in the following format to search hiking record(s)...')
        update.message.reply_text('e.g. /record Lion Rock')

    else:
        update.message.reply_text('I am sorry. As a hiking chatbot, I can only response to topics related to hiking. You can ask me questions or seek advice about hiking. :)')

# Define the record handler
def add_command(update: Update, context: CallbackContext) -> None:
    user_username = update.message.from_user.username
    date = update.message.date.strftime('%Y-%m-%d')
    record = update.message.text
    record = record.replace('/add', '')
    split_data = record.split(',')
    print(user_username)
    print(date)
    print(split_data)
    
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y_%m_%d_%H_%M_%S")
    
    # Check if all required information is included
    if len(split_data) != 5:
        update.message.reply_text('Please include all required information: date, route, weather, difficulty, and comment.')
        update.message.reply_text('Usage: e.g. /add 01/11/2011, Shing Mun, Sunny, 3, Nice weather hiking with friends')
        return
    
    collection_name = 'hiking_record'
    document_name = 'record_' + formatted_datetime
    data = {
        'user': user_username,
        'date': split_data[0].strip(),
        'name': split_data[1].strip(),
        'weather': split_data[2].strip(),
        'difficulty': split_data[3].strip(),
        'comment': split_data[4].strip(),
    }
    
    doc_ref = db.collection(collection_name).document(document_name)
    doc_ref.set(data)
    print("Data saved successfully!")
    update.message.reply_text('Hiking record added successfully!')
    
# Define the record handler
def show_record(update: Update, context: CallbackContext) -> None: 
    userinput = update.message.text
    search_RouteName = userinput.replace('/record', '').strip()
    
    # Check if all required information is included
    if (len(search_RouteName) == 0):
        update.message.reply_text('Please provide the route name after command /record.')
        update.message.reply_text('Usage: e.g. /record Shing Mun River')
        return
    
    collection_name = 'hiking_record'
    
    # Define the query
    query = db.collection(collection_name).where('name', '==', search_RouteName.strip())
    
    # Retrieve the documents that match the query
    docs = query.get()
    print(docs)
    print(len(docs))
    
    if (len(docs) == 0):
        update.message.reply_text('No such record.')
    else:
        # Iterate over the documents and extract the data
        for doc in docs:
            record_data = doc.to_dict()
            
            # Access individual fields from the record_data dictionary
            comment = record_data.get('comment', '')
            date = record_data.get('date', '')
            difficulty = record_data.get('difficulty', '')
            name = record_data.get('name', '')
            weather = record_data.get('weather', '')
            print("Date:", date)
            print("Name:", name)
            print("Weather:", weather)
            print("Difficulty:", difficulty)
            print("Comment:", comment)    
            print("-"*15)
            
            # Reply to the user with the extracted fields
            reply_message = (
                f"Date: {date}\n"
                f"Name: {name}\n"
                f"Weather: {weather}\n"
                f"Difficulty: {difficulty}\n"
                f"Comment: {comment}"
            )
            update.message.reply_text(reply_message)
        print("Data extracted successfully!")
        
if __name__=='__main__':
    main()