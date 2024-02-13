from vars import *
import telegram

def getClientId():
    headers = {
        "authority": "gocharting.com",
        "accept": "*/*",
        "accept-language": "en-GB,en;q=0.9",
        "referer": "https://gocharting.com/",
        "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://gocharting.com/dist/gocharting/20231227T072838-bae4acb83/app.9d6b43f9b85c409c4836.min.js",
        headers=headers,
    )
    if response.status_code == 200:
        response = response.text
        start = response.find("userPoolWebClientId")
        end = response[start:].find(",")
        client_id = (
            response[start : start + end]
            .replace("userPoolWebClientId:", "")
            .replace('"', "")
        )

        with open(metadata_file, "rb") as f:
            metadata = pickle.load(f)

        metadata["client_id"] = client_id

        with open(metadata_file, "wb") as f:
            pickle.dump(metadata, f)

        return client_id

    else:
        with open(metadata_file, "rb") as f:
            metadata = pickle.load(f)

        return metadata["client_id"]


def getAuthToken():
    headers = {
        "authority": "cognito-idp.ap-south-1.amazonaws.com",
        "accept": "*/*",
        "accept-language": "en-GB,en;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-amz-json-1.1",
        "origin": "https://gocharting.com",
        "referer": "https://gocharting.com/",
        "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "x-amz-target": "AWSCognitoIdentityProviderService.InitiateAuth",
        "x-amz-user-agent": "aws-amplify/5.0.4 js",
    }

    client_id = getClientId()

    auth_data = {
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": client_id,
        "AuthParameters": {"USERNAME": username, "PASSWORD": password},
        "ClientMetadata": {"myCustomKey": "myCustomValue"},
    }

    response = requests.post(
        "https://cognito-idp.ap-south-1.amazonaws.com/", headers=headers, json=auth_data
    )
    auth_token = response.json()["AuthenticationResult"]["IdToken"]
    return auth_token


async def sendTeleAlert(alert_text):
    params = {"chat_id": chat_id, "text": alert_text}
    response = requests.post(tele_url, params=params)
    await telegram.regex_parser(alert_text)
    if response.status_code != 200:
        print("Error sending alerts to telegram")


def getRequired(required_minutes, ohlcv, delta_data):
    bar_stats = pd.DataFrame(
        delta_data,
        columns=[
            "date",
            "max_delta",
            "min_delta",
            "close_delta",
            "cot_high",
            "cot_low",
        ],
    )

    df = pd.merge(ohlcv, bar_stats, on="date")[
        [
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "oi",
            "max_delta",
            "min_delta",
            "close_delta",
            "cot_high",
            "cot_low",
        ]
    ]
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%dT%H:%M:%S%z")
    df["date"] = df["date"].dt.tz_localize(None)
    df = df.sort_values("date", ascending=False)

    cols = ["max_delta", "min_delta", "close_delta", "cot_high", "cot_low"]
    df[cols] = df[cols].div(15).fillna(0).astype(int)

    df = df.sort_values("date", ascending=True).reset_index(drop=True)

    required_candles = {}
    for i in required_minutes:
        req = df[df["date"] == i]
        if not req.empty:
            required_candles[i] = req.squeeze().to_dict()
        if len(req) == 0:
            return None
    return required_candles


def formatText(date,
               volume,
               oi,
               max_delta,
               min_delta,
               close_delta,
               cot_high,
               cot_low,
               ratio1,
               ratio2,
               sellers,
               buyers):
    
    dominance = (
        "BUYERS and SELLERS currently balanced."
        if abs(sellers) == buyers
        else "SELLERS in action."
        if abs(sellers) > buyers
        else "BUYERS in action."
    )

    volume_str, oi_str = f"{volume}K", f"{oi}M"

    text = f"""
OFA DATA

{dominance}
DATE :: {date}

DELTA                {close_delta}
===================
MAX_DELTA       {max_delta}
MIN_DELTA       {min_delta}
==================={ratio1}%
COT_HIGH          {cot_high}
COT_LOW           {cot_low}
==================={ratio2}%
$VOLUME$         {volume_str}
OI                         {oi_str}
===================
    """
    return text


def processAlerts(message):
    alert = json.loads(message)
    content = alert["text"]["content"]
    if isinstance(content, dict):
        if content["m"] == "alert_fired":
            symbol = content["p"]["symbol"]
            message = content["p"]["message"]
            time_ = content["p"]["fire_time"]
            time_ = dt.datetime.strptime(time_, "%Y-%m-%dT%H:%M:%SZ") + dt.timedelta(
                hours=5.5
            )

            go_chart_info = None
            if "go_chart" in message:
                message, go_chart_info = message.split(' "go_chart" : ')

            if go_chart_info != None:
                go_chart_info = json.loads(go_chart_info)
                symbol = go_chart_info["symbol"]
                close = go_chart_info["close"]
                context = go_chart_info["context"]
                tf = (
                    go_chart_info["tf"] + "m"
                    if "h" not in go_chart_info["tf"]
                    else go_chart_info["tf"]
                )
                htf = (
                    go_chart_info["htf"] + "m"
                    if "h" not in go_chart_info["htf"]
                    else go_chart_info["htf"]
                )
                goCharting_TF = (
                    go_chart_info["goCharting_TF"] + "m"
                    if "h" not in go_chart_info["goCharting_TF"]
                    else go_chart_info["goCharting_TF"]
                )

                cnd = (int(go_chart_info["candle_time"]) / 1000)
                candle_time = dt.datetime.fromtimestamp(cnd).strftime(
                    "%Y-%m-%d %H:%M:00"
                )
                candle_date = dt.datetime.fromtimestamp(cnd).strftime("%Y-%m-%d")
                return message, symbol, time_, tf, htf, goCharting_TF, candle_time, candle_date, close, context
            
            return message, symbol, time_
    return

class OFAbot:

    def __init__(self) -> None:
        pass

    def initiate_ws(self):
        token = getAuthToken()
        self.websocket_url = websocket_url + "?token=" + token + "&tag=" + tag
        self.ws = websocket.create_connection(
            self.websocket_url, header=websocket_headers, timeout=600
        )

    def send(self, function, arguments):
        message = json.dumps(
            {"command": function, "payload": arguments}, separators=(",", ":")
        )
        self.ws.send(message)

    def ping(self):
        self.ws.send("PING")
        self.last_ping = dt.datetime.now()

    def subscribe(self):
        message = json.dumps(
            {
                "command": "SUBSCRIBE",
                "channel": "trade",
                "payload": [f"{self.exchange}:{self.symbol}"],
            },
            separators=(",", ":"),
        )
        self.ws.send(message)

    def unsubscribe(self):
        message = json.dumps(
            {
                "command": "UNSUBSCRIBE",
                "payload": [f"{self.exchange}:{self.segment}:{self.symbol}"],
            },
            separators=(",", ":"),
        )
        self.ws.send(message)
        message = json.dumps(
            {
                "command": "UNSUBSCRIBE",
                "channel": "OHLCV",
                "payload": {"exchange":self.exchange,"segment":self.segment,"symbol":self.symbol,"interval":self.interval},
            },
            separators=(",", ":"),
        )
        self.ws.send(message)

    def parse(self):
        if self.message.startswith("{") and self.message.endswith("}"):
            self.message = json.loads(self.message)

    def getOhlcv(self):
        params = {
            "exchange": self.exchange,
            "segment": self.segment,
            "symbol": self.symbol,
            "interval": self.interval,
            "rows": self.rows,
            "max": False,
            "idxs": [0],
        }

        self.send("OHLCV", params)

    def getFootprint(self):
        params = {
            "exchange": self.exchange,
            "segment": self.segment,
            "symbol": self.symbol,
            "interval": self.interval,
            "dates": [self.date],
        }
        self.send("FOOTPRINT", params)

    def recv(self):
        self.message = self.ws.recv()
        if "Welcome-" in self.message:
            print(go_connected)

        elif "OHLCV" in self.message:
            if self.message.startswith("{") and self.message.endswith("}"):
                self.ohlcv = json.loads(self.message)
                command = self.ohlcv.get("command")
                if command == "OHLCV":                        
                        self.ohlcv = pd.DataFrame(self.ohlcv["out"]["data"])
        else:
            return self.message
        
    def start_ws(self):
        self.last_ping = dt.datetime.now()
        self.ohlcv = None
        self.initiate_ws()
        self.recv()

    def getData(
        self,
        symbol: str = "BANKNIFTY-I",
        exchange: str = "NSE",
        interval: str = "1m",
        rows: int = 200,
        segment: str = "FUTURE",
        date: dt.datetime.date = dt.datetime.now().date().strftime("%Y-%m-%d"),
        required_minutes: list = [],
        ) -> None:

        self.symbol = symbol
        self.exchange = exchange
        self.interval = interval
        self.rows = rows
        self.segment = segment
        self.date = date
        self.required_minutes = required_minutes
           
        if self.ws.status=='closed':
            self.start_ws()
        
        self.getOhlcv()
        self.ping()
        self.recv()
        self.subscribe()
        self.recv()

        self.getFootprint()
        self.delta_data = []

        while True:
            self.message = self.recv()
            if not self.message:
                continue
            if self.message.startswith("{") and self.message.endswith("}"):
                self.message = json.loads(self.message)
                command = self.message.get("command")

                if command:
                    if command == "HOLLOW_FOOTPRINT":
                        out = self.message.get("out", {})
                        ref = out.get("ref")
                        if ref:
                            self.send("FOOTPRINT_CANDLE", {"ref": ref})

                    elif command == "FOOTPRINT_CANDLE":
                        data = self.message.get("out", {})
                        for date, summary in data.items():
                            req = summary.get("ending_summary", {})
                            req["date"] = date
                            self.delta_data.append(req)
                        required_data = getRequired(self.required_minutes, self.ohlcv, self.delta_data)
                        if required_data:
                            lst = []
                            for i in required_data:

                                bar_stats = required_data[i]
                                date = bar_stats["date"]
                                volume = round(bar_stats["volume"] / 1000, 1)
                                oi = round(bar_stats["oi"] / 1000000, 1)
                                max_delta = bar_stats["max_delta"]
                                min_delta = bar_stats["min_delta"]
                                close_delta = bar_stats["close_delta"]
                                cot_high = abs(bar_stats["cot_high"])
                                cot_low = abs(bar_stats["cot_low"])

                                ratio2 = min(cot_high, cot_low) / max(cot_high, cot_low) or 1
                                ratio1, ratio2 = round(1 / ratio2, 2), round(ratio2, 2)

                                sellers = -(abs(min_delta) + (max_delta - close_delta))
                                buyers = abs(min_delta) + max_delta
                                l = [date, volume, oi, max_delta, min_delta, close_delta, cot_high, cot_low, ratio1, ratio2, sellers, buyers]
                                lst.append(l)
                            
                            return lst

    async def ping_task(self):
        while True:
            await asyncio.sleep(30)
            self.ping()

    def start_ping_task(self):
        asyncio.ensure_future(self.ping_task())

    async def scriptAlerts(self):
        self.start_ws()
        self.start_ping_task()

        while True:
            try:
                async with websockets.connect(
                    tv_url,
                    extra_headers=tv_headers,
                    ping_interval=10**100,
                    ping_timeout=100000,                    
                ) as websocket:
                    
                    while True:
                        alert = await websocket.recv()
                        alert_text = processAlerts(alert)
                        
                        if isinstance(alert_text, tuple):
                            if len(alert_text)==3:
                                message, symbol, time_ = alert_text
                                tele_text = f"""Symbol : {symbol}\nTime : {time_} \n\n{message}\n\n -Powered by BOT Office Assistant - Kate"""
                            
                            else:
                                message, symbol, time_, tf, htf, goCharting_TF, candle_time, candle_date, close, context = alert_text
                                print(goCharting_TF, candle_time, candle_date)
                                print(self.ohlcv)
                                data = self.getData(interval=goCharting_TF, required_minutes=[candle_time], date=candle_date)[0]
                                print(self.ohlcv)
                                date, volume, oi, max_delta, min_delta, close_delta, cot_high, cot_low, ratio1, ratio2, sellers, buyers = data
                                ofa_text = formatText(date, volume, oi, max_delta, min_delta, close_delta, cot_high, cot_low, ratio1, ratio2, sellers, buyers)
                                tele_text = f"""Symbol : {symbol}\nTime : {time_} \n\n{message}\n\n {ofa_text}\n\n -Powered by BOT Office Assistant - Kate"""
                            await sendTeleAlert(tele_text)

                        diff = dt.datetime.now() - self.last_ping

                        if diff.total_seconds() > 29:
                            self.ping()                        

            except websockets.exceptions.ConnectionClosedError:
                print("WebSocket connection closed. Reconnecting...")
                await self.scriptAlerts()
                pass
            
            except KeyboardInterrupt:
                break
# text = f'''Symbol: NSE:BANKNIFTY1!
# Time: 2024-01-11 14:15:01\n\n
# Alert - Breakdown Detected
# NSE:BANKNIFTY1! price has closed below the marked low level of 47603.05\n\n
# PCA-L $193.05 / PTM-HL $276.5 / BCS $308\n\n
# OFA DATA\n\n
# BUYERS in action.\n
# DATE: 2024-01-11 14:00:00\n\n
# DELTA: 161
# ===================
# MAX_DELTA: 182
# MIN_DELTA: -46
# ===================4.0%
# COT_HIGH: 12
# COT_LOW: 3
# ===================0.25%
# $VOLUME$: 11.6K
# OI: 2.4M
# ===================\n\n
# -Powered by BOT Office Assistant - Kate
# '''


async def run():
    while True:
        try:
            # await sendTeleAlert(text)
            await OFAbot().scriptAlerts()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(e)
            print('Reconnecting..')
            pass

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

