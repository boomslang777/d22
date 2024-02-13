from datetime import datetime, timedelta
import pandas as pd
from telethon.sync import TelegramClient
from telethon import TelegramClient, events, sync
import time
import re
from settings import *
import telethon
# quantity = 15
import asyncio


def get_exp(contract_name):

    if contract_name != "BANKNIFTY":
        return None  


    current_date = datetime.now()

    day_of_week = current_date.weekday()


    if day_of_week in [1, 2]:
        nearest_wednesday_date = current_date + timedelta(days=7)
    else:
        days_until_nearest_wednesday = (2 - day_of_week + 7) % 7
        nearest_wednesday_date = current_date + timedelta(days=days_until_nearest_wednesday)
    week_number = (nearest_wednesday_date.day - 1) // 7 + 1
    print(week_number)
    if week_number == 4:
        return nearest_wednesday_date.strftime("%y%b").upper()
    else:
        month = nearest_wednesday_date.strftime("%m").lstrip("0")
        return nearest_wednesday_date.strftime("%y{0}%d").format(month) + nearest_wednesday_date.strftime("%y%m%d")[6:]

async def place_order(instrument, qty,kite,bot):
    print(instrument)
    mark = await get_ltp(kite,instrument)
    if qty >0 and qty < 900 :
        try :
            order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange="NFO",
                            tradingsymbol=instrument,
                            transaction_type="BUY",
                            quantity=qty,
                            order_type="MARKET",
                            product="MIS",
                            validity="DAY",
                            price=0,
                            trigger_price=0)
            print("Position entered successfully")
            
            current_time = datetime.now()
            status = await get_order_status(kite,order_id)
            message = f'Message: status: "{status}"\n {instrument}\nfilled_quantity": {qty}\naverage_price": {mark}\n\n\nexchange_order_id": "{order_id}\nexchange_timestamp": "{current_time}"'
            entity = await bot.get_entity(1002140069507) 
            print(entity.id)
            group_id = entity.id
            await bot.send_message(group_id, message)
        except  Exception as e:
            message = f"{e}"
            entity = await bot.get_entity(1002140069507)  
            group_id = entity.id
            await bot.send_message(group_id, message)


    else :
        legs = qty//900
        if qty%900 != 0 :
            legs += 1
        try :
            order_id = kite.place_order(variety=kite.VARIETY_ICEBERG,exchange = "NFO"
                            ,tradingsymbol=instrument,transaction_type = 'BUY',quantity=qty,
                            order_type="MARKET",product="MIS",validity="DAY",
                            iceberg_legs = legs,price =0,trigger_price =0,iceberg_quantity=900)
            print("Position entered successfully")
            message = f"Position entered successfully {instrument} with order id {order_id}"
            entity = await bot.get_entity(1002140069507)  
            print(entity.id)
            group_id = entity.id
            await bot.send_message(group_id, message)
        except  Exception as e:
            message = f"{e}"
            entity = await bot.get_entity(1002140069507)  
            group_id = entity.id
            await bot.send_message(group_id, message)    

async def get_order_status(kite, order_id):
    order_history = kite.order_history(order_id)

    for order in order_history:
        print(f"Order ID: {order['order_id']}, Status: {order['status']}")
        return order['status']

async def place_iceberg_limit_order(kite, tradingsymbol, quantity, price,bot):
    """
    Place an iceberg order.

    Parameters:
    kite (KiteConnect): The KiteConnect instance.
    tradingsymbol (str): The trading symbol.
    quantity (int): The total quantity.
    order_type (str): The order type ('MARKET' or 'LIMIT').
    price (float, optional): The price for limit orders.
    """
    mark = await get_ltp(kite,tradingsymbol)
    if quantity >0 and quantity < 900 :
        try :
            order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange="NFO",
                            tradingsymbol=tradingsymbol,
                            transaction_type="BUY",
                            quantity=quantity,
                            order_type="LIMIT",
                            product="MIS",
                            validity="DAY",
                            price=price)
            print("Position entered successfully")
            current_time = datetime.now()
            await asyncio.sleep(2)
            status = await get_order_status(kite,order_id)
            message = f'Message: status": "{status}"\nexchange_order_id": "{order_id}\nexchange_timestamp": "{current_time}\n \n{tradingsymbol}\nfilled_quantity": {quantity}\naverage_price": {mark}\n'

            entity = await bot.get_entity(1002140069507) 
            print(entity.id)
            group_id = entity.id
            await bot.send_message(group_id, message)
        except  Exception as e:
            message = f"{e}"
            entity = await bot.get_entity(1002140069507)  
            group_id = entity.id
            await bot.send_message(group_id, message)    
    else : 
        legs = quantity // 900
        if quantity % 900 != 0:
            legs += 1
        iceberg_qty = quantity//legs
        try:
            order_id = kite.place_order(
                tradingsymbol=tradingsymbol,
                quantity=quantity,
                order_type='LIMIT',
                price=price,
                product=kite.PRODUCT_MIS,
                exchange=kite.EXCHANGE_NSE,
                transaction_type=kite.TRANSACTION_TYPE_BUY,
                validity=kite.VALIDITY_DAY,
                disclosed_quantity=iceberg_qty,
                tag="Iceberg",
                variety=kite.VARIETY_ICEBERG,
                iceberg_legs = legs,iceberg_quantity = iceberg_qty
            )
            print(f"Order placed successfully. Order ID: {order_id}.")
        except  Exception as e:
            message = f"{e}"
            entity = await bot.get_entity(1002140069507)  
            group_id = entity.id
            await bot.send_message(group_id, message)


async def ctc(kite, bot):
    positions = kite.positions()['net']
    for position in positions:
        if position['quantity'] != 0:
            average_price = position['average_price']
            print(f"The average price is {average_price}")
            break
        else:
            print("No open position found.")
            return
    try:
        order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange="NFO",
                                    tradingsymbol=position['tradingsymbol'],
                                    transaction_type="SELL",
                                    quantity=position['quantity'],
                                    order_type="SL",
                                    product="MIS",
                                    validity="DAY",
                                    price=average_price,
                                    trigger_price=average_price)
        print(f"Stop loss set at entry price for order id: {order_id}")  
        message = f"SL moved to Cost {average_price}, with order ID {order_id}"
        entity = await bot.get_entity(1002140069507)  
        print(entity.id)
        group_id = entity.id
        from datetime import datetime
        current_time = datetime.now()
        ltp = await get_ltp(kite,position['tradingsymbol'])
        pnl = ltp - average_price
        await bot.send_message(group_id,f"Time : {current_time}\nOrder ID : {order_id}\n {position['tradingsymbol']} BOT at : {average_price}\n {position['tradingsymbol']} LTP : {ltp}\n\n [Unrealised PnL : {pnl}₹]\n\n Press /EXT to exit as Market Order \n\n Press /PRF-T to Trail Profit\nNote: TRADE TAG /CTC - SL is currently set at the entry point.")
    except Exception as e:
        print(f"An error occurred while modifying order : {e}")


    
async def get_stk(condition,kite):
    ins = "BANKNIFTY"
    instrument = ins + await get_current_year_month()
    banknifty_ltp = kite.ltp(f"NFO:{instrument}")[f"NFO:{instrument}"]["last_price"]
    strike_price = round(banknifty_ltp / 100) * 100
    print(f"{strike_price} is strike price")
    if condition == "BUY":
        return strike_price + 900
    elif condition == "SELL":
        return strike_price - 900
    else:
        return strike_price

async def cancel_orders(kite):
    orders = kite.orders()
    print(orders)
    for order in orders:
        if order["status"] == "OPEN" or order["status"] == "TRIGGER PENDING" and order["pending_quantity"] > 0:
            order_id = order["order_id"]
            print(order_id)
            kite.cancel_order(kite.VARIETY_REGULAR, order_id)
            print(f"Order {order_id} cancelled")


async def square_off_all_positions(kite,bot):
    await cancel_orders(kite)
    positions =  kite.positions()
    for position_type in ['net']:
        for position in positions.get(position_type, []):
            tradingsymbol = position['tradingsymbol']
            quantity = position['quantity']
            if quantity > 0 and quantity < 900:
                try :
                    order_id =  kite.place_order(variety=kite.VARIETY_REGULAR,
                                                exchange=kite.EXCHANGE_NFO,
                                                tradingsymbol=tradingsymbol,
                                                transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                quantity=quantity,
                                                product=kite.PRODUCT_MIS,
                                                order_type=kite.ORDER_TYPE_MARKET,
                                                tag="SquareOff")

                    from datetime import datetime
                    current_time = datetime.now()
                    response = kite.margins()
                    equity_available_margin = response['equity']['available']['cash']
                    message = f"Time : {current_time} \n All positions squared off and pending orders cancelled \n\n Trading symbol {tradingsymbol}\nOrder ID : {order_id}\n MARGIN : {equity_available_margin}"
                    entity = await bot.get_entity(1002140069507)  
                    print(entity.id)
                    group_id = entity.id
                    await bot.send_message(group_id, message)
                    break
                except  Exception as e:
                    message = f"{e}"
                    entity = await bot.get_entity(1002140069507)  
                    group_id = entity.id
                    await bot.send_message(group_id, message)

async def calculate_and_send_pnl(kite, group_id, bot):
    from datetime import datetime
    while True:
        try:
            positions = kite.positions()['net']
            has_open_position_flag = False

            for position in positions:
                trading_symbol = position['tradingsymbol']
                quantity = position['quantity']
                current_time = datetime.now()
                has_open_position = quantity != 0

                if has_open_position :
                    has_open_position_flag = True
                    pnl = position['m2m']
                    avg = position['average_price']
                    ltp = await get_ltp(kite,trading_symbol)
                    pnl = round((ltp - avg) * quantity, 2)
                    print(f"PnL for {trading_symbol}: ", pnl)
                    await bot.send_message(group_id, f"Entry for {trading_symbol}: {avg}₹ \nLTP for {trading_symbol} : {ltp}   \n PNL :{pnl} ₹")
                    
            if has_open_position_flag == False :
                status = "COMPLETE"
                positions = kite.positions()['net']
                latest_position = positions[0]
                current_time = datetime.now()
                pnl =  latest_position['sell_m2m'] - latest_position['buy_m2m']
                print(f"Final PnL for {trading_symbol}: ", pnl)
                qty = latest_position['sell_quantity']
                pts = latest_position['sell_price'] -  latest_position['buy_price']
                await bot.send_message(group_id, f"--------------\nTime : {current_time}\nTrade status is {status}\nInstrument : {latest_position['tradingsymbol']}\n\nQTY : {qty}\nBOT : {latest_position['buy_price']}\nSOLD : {latest_position['sell_price']}\n\n Realized PNL : {pnl}₹\nPoints Captured : {round(pts,2)}  ")
                print("No open positions")
                break


            await asyncio.sleep(30) 

        except Exception as e:
            print(f"An error occurred while calculating P&L: {e}")

async def fire(condition, kite, bot,flag=0):
    print(f"{condition} {kite} {bot}")
    try:
        if condition == 1 or condition == -1:
            direction = "BUY" if condition == 1 else "SELL"
            option_type = "CE" if condition == 1 else "PE"
            exp =  get_exp(instrument).upper()
            print(f"{exp} is expiry")
            stk = await get_stk(direction, kite)
            contract_name = instrument
            order_info = f"{contract_name}{exp}{stk}{option_type}"
            ltp = await get_ltp(kite, order_info)
            margins = kite.margins()
            mgin = margins['equity']['net']
            av_mgin = (mgin*margin_allowed_pct)/100
            lot_size = int(av_mgin//(lots*ltp))
            print(f"{lot_size} is lot size")
            quantity = lots 
            margin = quantity * ltp
            current_time = datetime.now()
            message = f"Timestamp : {current_time} \n\nDirection: {direction}\nOrder Info: {order_info}\nQuantity: {quantity}\nLTP : {ltp}\n\nDo you want to proceed? (Type /yes to confirm),\n{margin} ₹ is margin\n\n MKT/QTY/STRIKE \n LMT/PRICE/QTY/STRIKE"
            print("Stop here")
            try:
                entity = await bot.get_entity(1002140069507)
            except Exception as e:
                print(f"An error occurred: {e}")
            print("enter here")
            print(entity.id)
            group_id = entity.id
            print(f"{order_info} is order info")
            await bot.send_message(group_id, message)
            @bot.on(events.NewMessage(chats=group_id))
            async def handle_new_message(event, order_info=order_info, quantity=quantity):
                nonlocal flag
                sender = await event.get_sender()
                print(f'Username: {sender.username}, Message: {event.message.text}')

                market_order_regex = re.compile(r'/MKT/(\d+)/([+-]?\d+)')
                limit_order_regex = re.compile(r'/LMT/([+-]?\d+(\.\d+)?)/(\d+)/([+-]?\d+)')

                match_market_order = market_order_regex.match(event.message.text)
                match_limit_order = limit_order_regex.match(event.message.text)

                if match_market_order and flag ==1:
                    quantity = int(match_market_order.group(1))
                    strike = int(match_market_order.group(2))
                    banknifty_ltp = kite.ltp("NSE:NIFTY BANK")["NSE:NIFTY BANK"]["last_price"]
                    stkm = int(round(banknifty_ltp + strike, -2))
                    order_info = f"{contract_name}{exp}{stkm}{option_type}"
                    print(f"Market Order - Quantity: {quantity}, Strike: {stkm}")
                    print("Placing trades")
                    await place_order(order_info, quantity, kite,bot)
                    print("Order placed")
                    print("SL placed")
                    await calculate_and_send_pnl(kite, group_id, bot)
                    flag =0
                    bot.remove_event_handler(handle_new_message)

                elif match_limit_order and flag ==1:
                    price = float(match_limit_order.group(1))
                    quantity = int(match_limit_order.group(3))
                    strike = int(match_limit_order.group(4))
                    banknifty_ltp = kite.ltp("NSE:NIFTY BANK")["NSE:NIFTY BANK"]["last_price"]
                    stkl = int(round(banknifty_ltp + strike, -2))
                    order_info = f"{contract_name}{exp}{stkl}{option_type}"
                    print(f"Limit Order - Price: {price}, Quantity: {quantity}, Strike: {strike}")
                    order_id = await place_iceberg_limit_order(kite, order_info, quantity, price,bot)
                    flag =0
                    while True:
                        orders = kite.orders()
                        open_orders = [order for order in orders if order['status'] == 'OPEN']
                        if not open_orders:
                            print("No open orders found.")
                            print("Placing SL")
                            await calculate_and_send_pnl(kite, group_id, bot)
                            break
                        else:
                            await asyncio.sleep(1) 
                            continue
                    bot.remove_event_handler(handle_new_message)       

                elif event.message.text == '/yes' and flag ==1:
                    print("Placing trades")
                    await place_order(order_info, quantity, kite,bot)
                    print("Order placed")
                    print("SL placed")
                    await calculate_and_send_pnl(kite, group_id, bot)
                    flag =0
                    bot.remove_event_handler(handle_new_message)

    except Exception as e:
        print(f"An error occurred: {e}")

async def check_latest_position(kite):
    positions = kite.positions()['net']
    if not positions:
        return "No positions found."
    latest_position = positions[-1]
    if latest_position['quantity'] > 0:
        return "BUY"
    elif latest_position['quantity'] < 0:
        return "SELL"
    else:
        return None

async def prft(kite,bot) :
    latest_pos = await check_latest_position(kite)
    ins = "BANKNIFTY"
    instrument = ins + await get_current_year_month()
    pt = kite.ltp(f"NFO:{instrument}")[f"NFO:{instrument}"]["last_price"]
    entity = await bot.get_entity(1002140069507)  
    print(entity.id)
    group_id = entity.id
    from datetime import datetime
    current_time = datetime.now()
    positions = kite.positions()['net']
    for position in positions:
        trading_symbol = position['tradingsymbol']
        ltp = await get_ltp(kite,trading_symbol)
        quantity = position['quantity']
        current_time = datetime.now()
        has_open_position = quantity != 0
        average_price = position['average_price']
        pnl = (ltp - average_price)*quantity
        if has_open_position :
            await bot.send_message(group_id,f"Time : {current_time}\n {position['tradingsymbol']} BOT at : {average_price}\n {trading_symbol} LTP : {ltp}\n\n [Unrealised PnL : {pnl}₹]\n\n Press /EXT to exit as Market Order \nPress CTC to move your SL to entry point\n Press /PRF-T to Trail Profit\nNote: TRADE TAG /PRF-T - SL is currently set at the PRF-T Future Price")
            break
    if latest_pos == "BUY":
        print(f"{pt} is profit target")
        print(f"{latest_pos} is buy")
        while True:
            ltp = kite.ltp(f"NFO:{instrument}")[f"NFO:{instrument}"]["last_price"]
            print(f"{ltp} is ltp")
            if ltp <= pt :
                await square_off_all_positions(kite,bot)
                break
    elif latest_pos == "SELL":
        print(f"{latest_pos} is sell")
        print(f"{pt} is profit target")
        while True:
            ltp = kite.ltp(f"NFO:{instrument}")[f"NFO:{instrument}"]["last_price"]
            print(f"{ltp} is ltp")
            if ltp >= pt :
                await square_off_all_positions(kite,bot)
                break       

async def get_current_year_month():
    import datetime
    now = datetime.datetime.now()
    last_week = (now + datetime.timedelta(days=7)).month != now.month

    if last_week:
        next_month = now.replace(month=(now.month % 12) + 1, day=1)
        return next_month.strftime("%y%b").upper() + 'FUT'
    else:
        return now.strftime("%y%b").upper() + 'FUT'
async def get_ltp(kite,instrument):
    ltp = kite.ltp(f"NFO:{instrument}")[f"NFO:{instrument}"]["last_price"]
    return ltp