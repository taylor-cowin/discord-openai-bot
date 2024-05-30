'''
> Request passed to chatGPT w/ rate-limit per Discord user
'''
from multiprocessing import Pool
import multiprocessing.process
import os
import discord_bot
import openai_handler
import logging
import multiprocessing
import json
#import time

#Global variables
logger=None
queue_path="./chatgpt_requests.json"
discord_proc=None
openai_proc=None

def ensure_logger():
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)
        logging.basicConfig(filename='chatgpt-discord-bot.log', level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def delete_entry(id):
    ensure_logger()
    queued_files = read_queue_file()
    for item in queued_files:
        if str(id) == item["id"]:
            logger.debug(f"Deleting item: {item['id']}")
            queued_files.remove(item)
            write_json_to_file(queued_files)

def create_json(new_entry):
    ensure_logger()
    #get either a dict of existing entries or a blank dict []
    existing_json=read_queue_file()
    #Add the new entry to the list and forward whole list back for writing
    isResponse = False
    
    #check if entry matches -- if it matches, it's a response and we need to append the response information
    for index, item in enumerate(existing_json):
        if item["id"] == new_entry["id"]:
            existing_json[index] = new_entry
            isResponse = True
    #It didn't match, so it must be a new entry
    if not isResponse:
        existing_json.append(new_entry)
    logger.debug(f"Updated JSON: {existing_json}")    
    return existing_json

def check_for_responses(incoming_list_of_dicts, caller_id):
    ensure_logger()
    response_list = []
    #Add to gpt list if it doesn't have a response
    for item in incoming_list_of_dicts:
        if item["response"] is None:
            if caller_id == "gpt":
                response_list.append(item)
        #if it already has a response then add it to the list:
        else: 
            if caller_id == "disc":
                response_list.append(item)
    logger.debug(f"Responses for {caller_id}: {response_list}")
    return response_list


def write_json_to_file(incoming_array):
    ensure_logger()
    #Always rewrite the entire file
    json_to_write = json.dumps(incoming_array)
    with open(queue_path, "w+") as outfile:
        outfile.write(json_to_write)
    logger.debug(f"Written to file: {incoming_array}")    
        
def parse_json(_qf):
    ensure_logger()
    #pull the json into a list for manipulation
    queued_requests=[]
    if _qf is not None:
        if os.path.getsize(queue_path) > 0:
            for entry in _qf:
                queued_requests.append(entry)
    logger.debug(f"Parsed JSON: {queued_requests}")            
    return queued_requests    

def hook_queue_file():
    ensure_logger()
    queue_file=None
    _f=None
    try:
        #Try to open the file if it has a size >0, otherwise ignore it 
        if os.path.getsize(queue_path) > 0:
            _f = open(queue_path, "r")
            try:
                queue_file = json.loads(_f.read())
            except json.JSONDecodeError:
                queue_file = []
    #create file if it doesn't exist and then ignore it
    except IOError: 
        _f = open(queue_path, "w") #create empty file
    #Close the file if it ever opened at all
    if _f is not None:
        _f.close()
    logger.debug(f"Hooked queue file: {queue_file}")    
    return queue_file

def read_queue_file():
    queue_file = hook_queue_file()
    if queue_file is not None:
        return parse_json(queue_file)
    else:
        #return an empty array so we can write to it without a clusterfuck in the calling script
        return []

def startup_modules():
    ensure_logger()
    global discord_proc, openai_proc 

    discord_proc = multiprocessing.Process(target=discord_bot.initialize, args=(os.environ.get("DISCORD_API_KEY"),))
    logger.debug(f"Starting: {discord_proc}")
    discord_proc.start()
    
    openai_proc = multiprocessing.Process(target=openai_handler.initialize, args=(os.environ.get("OPENAI_API_KEY"),))
    logger.debug(f"Starting: {openai_proc}")
    openai_proc.start()
    
    logger.debug(f"Both processes started.")
    discord_proc.join()
    openai_proc.join()
    return 0

def kill_processes():
    if discord_proc != None:
        discord_proc.terminate()
    if openai_proc != None:
        openai_proc.terminate()

def main():
    ensure_logger()
    logger.debug(f"Starting Discord ChatGPT Bot v.99.")
    read_queue_file()
    startup_modules()
    
if __name__ == '__main__':
    try:
        main()
    finally:
        kill_processes()