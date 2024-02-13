
import re
import configparser
import pyotp
from jugaad_trader import Zerodha
from telethon import TelegramClient, events, sync
import security
import asyncio
from vars import *

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

config = configparser.ConfigParser()
config.read('creds.ini')
user_id = config['DEFAULT']['user_id']
password = config['DEFAULT']['password']
totp_secret = config['DEFAULT']['totp_secret']

# Initialize TOTP with the secret key
otp_gen = pyotp.TOTP(totp_secret)

# Generate current OTP
current_otp = otp_gen.now()

# Initialize Zerodha class with credentials and OTP
kite = Zerodha(user_id=user_id, password=password, twofa=current_otp)

# Login to Zerodha
login_response = kite.login()
margins = kite.margins()
print(margins['equity']['net'])
print(margins)
ltp = kite.ltp("NSE:POLYCAB")
# print(ltp)
# print(login_response)
entity = bot.get_entity(1002140069507)
group_id = entity.id
message = login_response
if message:
    bot.send_message(group_id, "Kite connected")

# entity = bot.get_entity(1002140069507)
# group_id = entity.id

# bot.send_message(group_id, message)


tv_status = "CONNECTED"
if kite :
    zerodha_status = "CONNECTED"
    if bot :
        telegram_status = "CONNECTED"
    else :
        telegram_status = "DISCONNECTED"   
else :
    zerodha_status= "DISCONNECTED"         
entity = bot.get_entity(1002140069507)  # Replace 'your_channel_username' with your channel's username
print(entity.id)
group_id = entity.id
message = f"Tradingview status : {tv_status}\n Zerodha status : {zerodha_status} \n Telegram status :{telegram_status}"
# Now use the obtained group_id in the send_message call
bot.send_message(group_id, message)
async def regex_parser(text):
    print(text)
    pattern = re.compile(r'Alert - (Breakout Detected|Breakdown Detected|Stop Loss hit | Move stop loss)')

    # Search for the pattern in the text
    match = pattern.search(text)

    # Extract the matched action
    if match:
        action = match.group(1)
        await trade(action)
        print(action)
    else:
        print("No match found.")

async def trade(signal):
    print(f"{signal} is signal")

    # Read credentials from config file
    #kite.place_order(variety=kite.VARIETY_ICEBERG,exchange=kite.EXCHANGE_NFO,tradingsymbol=tradingsymbol,transaction_type=kite.TRANSACTION_TYPE_SELL,quantity=quantity,product=kite.MIS,iceberg_legs=4,order_type=)
    
    if signal == "Stop Loss hit":
        # Assuming cancel_orders and square_off_all_positions functions are defined in the security module
        await security.cancel_orders(kite)
        await security.square_off_all_positions(kite)
    elif signal == "Breakdown Detected":
        signal = -1
        # Assuming fire function is defined in the security module
        print(bot)
        await security.fire(signal, kite,bot,flag=1)
    elif signal == "Breakout Detected":
        signal = 1
        # Assuming fire function is defined in the security module
        print(bot)
        await security.fire(signal, kite,bot,flag=1)
    elif signal == "Move stop loss to entry point": 
        await security.cancel_orders(kite)
        await security.ctc(kite,bot)

@bot.on(events.NewMessage(chats=(1002140069507)))
async def handle_new_message(event):
    sender = await event.get_sender()
    content = event.message.text
    if content == '/EXT' :
        print("positions squaring off")
        await security.square_off_all_positions(kite,bot)
    elif content == '/CTC' :
        print("Cost to cost")
        await security.ctc(kite,bot)
    elif content == '/PRF-T' :
        print("Take profit level initiated")
        await security.prft(kite,bot)    
    # Call the regex_parser function with the message content
    await regex_parser(content)

    print(f'Username: {sender.username}, Message: {content}')

# def main():
#     bot.run_until_disconnected()

# if __name__ == '__main__':
#     main()
