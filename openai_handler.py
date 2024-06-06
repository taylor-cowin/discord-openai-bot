###################
###################
###### DEV ########
###################
###################

import logging
from openai import OpenAI
import os
import main
import discord_bot

#Global Variables
logger = None
gpt_client = None
thread = None
    
gpt_client = OpenAI()
#logger.debug(f"gpt_client: {gpt_client}")

#thread = gpt_client.beta.threads.create()

#logger.debug(f"thread: {thread}")

'''
***************************
NEED TO ADD PER-USER THREADS IN OPENAI
***************************
'''

def ensure_logger():
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)
        logging.basicConfig(filename='chatgpt-discord-bot.log', level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def ask_chatgpt(question_dict):
    ensure_logger()
    #Global thread for now -- need to add threads per user or command to start a new thread
    logger.debug(f"Asking ChatGPT: {question_dict}")
    
    message = gpt_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a very knowledgeable and helpful, but rude, assistant. You frequently belittle people in your responses and you make them feel inadequate."},
            {"role": "user", "content": question_dict["contents"]}
        ])

    if message is not None:
        logger.debug(f"Message: {message}")
        if message['choices'][0]['text'] is not None:
            response = message['choices'][0]['text']
            logger.debug(f"Received response from OpenAI: {response}")
            return response
        logger.debug(f"Message: {message}")    
   
def create_active_queue(incoming_json_list_of_dicts):
    return main.check_for_responses(incoming_json_list_of_dicts, "gpt")

def process_questions(incoming_json_list_of_dicts):
    active_queue = create_active_queue(incoming_json_list_of_dicts)
    for question in active_queue:
        response = ask_chatgpt(question)
        #Set the response in the dict and then re-send for updating the file.
        question["response"] = response
        jsonified_string = main.create_json(question)
        logger.debug(f"Updated JSON with response: {jsonified_string}")
        main.write_json_to_file(jsonified_string)
        discord_bot.remote_trigger()

def check_for_pending_queue():
    ensure_logger()
    logger.debug("Checking for pending queue. (openai_handler.py)")
    if os.path.getsize(main.queue_path) > 0:
        incoming_json = main.read_queue_file() #should have a list of dicts here
        if incoming_json != []:
            process_questions(incoming_json)

def initialize(api_key):
    ensure_logger()
    logger.info("Starting OpenAI handler.")

    #check for leftover questions in file (returns the json if they exist) and answer on startup
    check_for_pending_queue()
    return 0

