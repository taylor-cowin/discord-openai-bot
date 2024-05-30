import discord
import logging
import time
import main
import openai_handler
import asyncio

logger = None
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

monitor_channel="chatgpt-under-construction"
channel_id = 1242325275119714324

'''
****************************
SANITIZE YOUR FUCKING INPUTS
****************************
'''

def ensure_logger():
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)
        logging.basicConfig(filename='chatgpt-discord-bot.log', level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def send_message(_msg):
        channel=discord_client.get_channel(1242325275119714324)
        asyncio.create_task(channel.send(_msg))
        return
    
def check_for_responses():
    #TODO
    #This is wrong -- this is going to reset every time this code loops
    #If there are any responses, they need to be sent
    response_list = main.check_for_responses(main.read_queue_file(), "disc") #Gets list of questions with responses
    for response_item in response_list:
        send_message(response_item["response"])
        main.delete_entry(response_item["id"])
        check_for_responses()

def create_hash(message: str):
    #hash the time with the author and then take the last 10 digits for an ID
    _t = time.localtime()
    _id=hash(str(_t)+str(message.author))
    return str(_id)[-10:]

## Capture incoming messages and write them in json format to a text file
def add_to_queue(message: str):
    ensure_logger()
    logger.info("Message from " + str(message.author) + ":" + str(message.content))
    _id = create_hash(message)
    _ = {
        "id": _id,
        "author": str(message.author),
        "contents": str(message.content),
        "response": None,
        }
    jsonified_string = main.create_json(_)
    main.write_json_to_file(jsonified_string)
    openai_handler.check_for_pending_queue()

##TODO Writes text to a specified channel, with option to @ a user            
#async def bot_chat_to_channel(self, channel: discord.channel, content: str, tagged_user: discord.User):
#    await message.channel.send(vomit)

#Listens for incoming message and makes sure it wasn't the bot talking
@client.event
async def on_message(message):
    ensure_logger()
    if str(message.channel) == monitor_channel:
        if not message.author.bot:
            logger.debug(f"Discord bot received message: {message.content}")
            #await message.channel.send(f"Adding query to queue: {message.content}")
            add_to_queue(message)
    return        

##Announces once the discord client is active
@client.event
async def on_ready():
    ensure_logger()
    logger.info(f'Logged on as {discord_client.user}!')    
    check_for_responses()
    return                  

def remote_trigger():
    ensure_logger()
    try:#Called by openai script
        check_for_responses()
    except:
        logger.error("Error at remote trigger")

def initialize(api_key):
    ensure_logger()
   
    global discord_client
    discord_client = client
    discord_client.run(api_key)

    check_for_responses()
    return 0
