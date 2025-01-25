# للحصول على العملة الأفضل بناءً على تحليل SMC فقط، يمكننا تعديل الكود ليقوم بالتحليل لجميع العملات، ولكن بدلاً من إرسال رسالة لكل عملة تتحقق شروطها، نحتفظ بالعملة الأفضل (التي تحقق الشروط بأقوى طريقة). مثلاً: إذا كانت العملة لديها كسر هيكل صعودي (BOS Up) وهي الأقرب إلى الدعم، نعتبرها العملة الأفضل.



from binance import Client
import pandas as pd
import requests

api_key = '8kOTx7V96c8FDa2kxGI9OFuc7A6ofp8VIVUbdwrpxBYlvnwSbqXzThb5gRTgCNTa'
api_secret = 'Xj15wrPbcz9FJjM1qU4zeBhRCmrc1tD6JAmyg3IHyXS7Qv3U1veFt5okMpuq5hmc'

# تفاصيل بوت تيليجرام
bot_token = '6683435751:AAH2ONuZOvAGVtZUWMGvnLX6py2sCeSZ5Mw'  # Replace with your Telegram bot token
chat_id = '5242310376'  # Replace with your Telegram chat ID


# تهيئة عميل Binance
client = Client(api_key, api_secret)

# جلب بيانات الشموع التاريخية
def fetch_candlestick_data(symbol, interval='1h', limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'trades', 
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    data['high'] = data['high'].astype(float)
    data['low'] = data['low'].astype(float)
    data['close'] = data['close'].astype(float)
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    return data

# تحليل الشروط بناءً على SMC
def analyze_smc(data):
    data['high_prev'] = data['high'].shift(1)
    data['low_prev'] = data['low'].shift(1)
    data['close_prev'] = data['close'].shift(1)

    # كسر الهيكل (BOS)
    bos_up = (data['close'].iloc[-1] > data['high_prev'].iloc[-1])
    bos_down = (data['close'].iloc[-1] < data['low_prev'].iloc[-1])

    # مناطق السيولة (الدعم والمقاومة)
    support = data['low'].rolling(window=5).min().iloc[-1]
    resistance = data['high'].rolling(window=5).max().iloc[-1]
    current_price = data['close'].iloc[-1]

    # المسافة إلى الدعم والمقاومة
    distance_to_support = abs(current_price - support)
    distance_to_resistance = abs(resistance - current_price)

    return {
        "bos_up": bos_up,
        "bos_down": bos_down,
        "support": support,
        "resistance": resistance,
        "current_price": current_price,
        "distance_to_support": distance_to_support,
        "distance_to_resistance": distance_to_resistance
    }

# إرسال رسالة إلى تيليجرام
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=payload)
    return response

# تحليل جميع العملات واختيار الأفضل
exchange_info = client.get_exchange_info()
symbols = [symbol['symbol'] for symbol in exchange_info['symbols'] if symbol['status'] == 'TRADING']

best_symbol = None
best_score = float('inf')  # نستخدم هذا لتقييم أقرب عملة إلى الدعم
best_analysis = None

for symbol in symbols:
    try:
        # جلب بيانات الشموع
        data = fetch_candlestick_data(symbol, interval='1h', limit=50)

        # تحليل الشروط باستخدام SMC
        smc_results = analyze_smc(data)

        # تقييم بناءً على القرب من الدعم وكسر الهيكل الصعودي
        if smc_results["bos_up"] and smc_results["distance_to_support"] < best_score:
            best_symbol = symbol
            best_score = smc_results["distance_to_support"]
            best_analysis = smc_results

    except Exception as e:
        print(f"خطأ في العملة {symbol}: {e}")

# إرسال أفضل عملة إلى تيليجرام
if best_symbol and best_analysis:
    message = f"أفضل عملة بناءً على تحليل SMC:\n"
    message += f"الرمز: {best_symbol}\n"
    message += f"- السعر الحالي: ${best_analysis['current_price']:.2f}\n"
    message += f"- مستوى الدعم: ${best_analysis['support']:.2f}\n"
    message += f"- مستوى المقاومة: ${best_analysis['resistance']:.2f}\n"
    message += f"- كسر الهيكل: صعودي (Bullish)\n"
    send_to_telegram(message)

    print(f"تم إرسال أفضل عملة: {best_symbol}")
else:
    print("لم يتم العثور على عملة تحقق الشروط.")
