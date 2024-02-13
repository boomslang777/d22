from imports import *
import configparser
api_id = '25042394'
api_hash = '8ee0191890aad20ce78034468178db27'
bot_token = '6785415766:AAGUoJpWVn-8aJIIpgRF_wovRRSL8XDufes'

metadata_file = 'metadata.pickle'
username = "logesh.newac@gmail.com"
password = "@gocharting"
tag = 'gUmyx8Qy8Y'

websocket_url = 'wss://ws.gocharting.com/blr1/ws'
websocket_headers = {'Pragma': 'no-cache',
                    'Origin': 'https://gocharting.com',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Upgrade': 'websocket',
                    'Cache-Control': 'no-cache',
                    'Connection': 'Upgrade',
                    'Sec-WebSocket-Version': '13',
                    'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
                }

tv_headers = {
    'Pragma': 'no-cache',
    'Origin': 'https://in.tradingview.com',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Upgrade': 'websocket',
    'Cache-Control': 'no-cache',
    'Connection': 'Upgrade',
    'Sec-WebSocket-Version': '13',
    'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
}

tv_url = 'wss://pushstream.tradingview.com/message-pipe-ws/private_NLHwCASVetj0Z-tTvsjcHe_97qw4mk7BMaZZ1xXHqUg'
go_connected = 'GoCharting Websocket connection established successfully.'


chat_id = '-1002140069507'
tele_url = 'http://api.telegram.org/bot6467985085:AAHT8IcC7uxWL7i-TShGvAqOHLOm3UiMk-o/sendMessage'
