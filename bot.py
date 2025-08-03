import logging
import requests
import time
from telegram import Bot
from threading import Thread

# === CONFIGURATION ===
TOKEN = "8260575825:AAFbElNrnGhTT7mtRRaC4uETTtE6KgCc7Lg"  # Bot token
CHANNEL_CHAT_ID = -1002884056595  # Channel ID (IMPORTANT: keep the -100 prefix)

bot = Bot(token=TOKEN)

# === INTERNAL STATE ===
last_period = None
history = []

# === PREDICTION LOGIC ===
def logic_DigitBandBias():
    recent = history[-10:]
    big = sum(1 for x in recent if x.get("actualResult") == "BIG")
    small = sum(1 for x in recent if x.get("actualResult") == "SMALL")
    if big >= 7:
        return "SMALL"
    if small >= 7:
        return "BIG"
    return "BIG" if time.time() % 2 > 1 else "SMALL"

# === FETCH GAME RESULT (used only for internal tracking, not sending) ===
def fetchGameResult():
    url = "https://api.bdg88zf.com/api/webapi/GetNoaverageEmerdList"
    headers = {"Content-Type": "application/json"}
    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 1,
        "language": 0,
        "random": "4a0522c6ecd8410496260e686be2a57c",
        "signature": "334B5E70A0C9B8918B0B15E517E2069C",
        "timestamp": int(time.time())
    }

    try:
        res = requests.post(url, json=payload, headers=headers)
        data = res.json()
        return data['data']['list'][0]
    except Exception as e:
        print("API Error:", e)
        return None

# === MAIN LOOP ===
def prediction_loop():
    global last_period
    while True:
        now = time.localtime()
        total_minutes = now.tm_hour * 60 + now.tm_min
        period = f"{now.tm_year}{now.tm_mon:02d}{now.tm_mday:02d}1000{10001 + total_minutes - 330}"

        if period != last_period:
            prediction = logic_DigitBandBias()
            history.append({
                "period": period,
                "prediction": prediction,
                "status": "PENDING"
            })
            last_period = period

            # Stylish Message Design
            message = (
                "🧊  𝐀𝐀𝐑𝐔𝐒𝐇𝐈 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍  🧊\n\n"
                "╭───────────────╮\n"
                f"│ Period : {period}\n"
                f"│  Predict : {prediction}\n"
                "╰───────────────╯\n\n"
            )

            # Send only to channel
            bot.send_message(chat_id=CHANNEL_CHAT_ID, text=message)

        # Keep checking results (used only for bias logic)
        result = fetchGameResult()
        if result:
            try:
                number = int(result['number'])
                actual_result = "BIG" if number >= 5 else "SMALL"
                for item in history:
                    if item["period"] == result["issueNumber"] and item["status"] == "PENDING":
                        item["actualResult"] = actual_result
                        item["status"] = "WIN" if item["prediction"] == actual_result else "LOSS"
            except Exception as e:
                print("Result Parse Error:", e)

        time.sleep(5)

# === START BOT ===
Thread(target=prediction_loop).start()