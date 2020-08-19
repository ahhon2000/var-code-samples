import os, sys
import re

dirTGui = "./site_root"

sslKeysDir = '../gui/keys'

DB_NAME = "userdb"
DB_USER = "user"
DB_PASSWORD = ""
PORT = 8115
#LISTEN_ADDR = '127.0.0.1'
LISTEN_ADDR = '0.0.0.0'

DEFAULT_EXCHANGE = "OKEx" # TODO should be OKEx
#DEFAULT_EXCHANGE = "BitMEX"

DEFAULT_PRICE_DEPTH = 0.2  # percent (i. e., 1 means 1%)
DEFAULT_AVG_INTERVAL1 = 5  # minutes
DEFAULT_AVG_INTERVAL2 = 60  # minutes

DEFAULT_COINS = [
	"BTC", "ETH", "LTC", "EOS", "ETC", "XRP", "BCH", "BSV", "TRX",
	"ADA",
]
COINS = {
	"OKEx": list(DEFAULT_COINS),
	"BitMEX": list(DEFAULT_COINS),
	"Bitfinex": ["BTC", "ETH", "EOS", "LTC", "XRP", "ETC", "TRX", "BAB"],
	"Binance": ["BTC", "ETH", "EOS", "LTC", "XRP", "ETC", "TRX", "BCHABC",
		"ADA",
	],
}
COINS['BitMEX'][COINS['BitMEX'].index('BTC')] = 'XBT'

FUNDING_SYMBOLS = ["BTCUSD", "ETHUSD", "EOSUSD", "XRPUSD", "BCHUSD",
	"LTCUSD", "ETCUSD", "BSVUSD", "TRXUSD",
]

BITMEX_CONFIG = {
	'CONTRACTS_TO_IGNORE': ["XBT7D_D95", "XBT7D_U105"],
	'MAX_N_ORDERBOOK_RECORDS': 200,
	'MAX_RECONNECTS_PER_HOUR': 15,
}

BACKEND_LOOP_INTERVAL = 2  # seconds
ORDERBOOK_EXPIRY_INTERVAL = 1  # hours
U_ORDERBOOK_EXPIRY_INTERVAL = 10  # hours
INVALID_POINTS_ALLOWANCE_FOR_AVERAGES = 0.35  # fraction, e. g.: 0.1 means 10%

UNIFORM_ORDERBOOK_DEPTH_STEP = 0.02 #  percent points
UNIFORM_ORDERBOOK_MAX_DEPTH = 20  # percent points
UNIFORM_ORDERBOOK_INTERVAL = 1  # minutes between each uniform record

#POINTS_PER_MINUTE_FOR_AVERAGES = 6  # at least this many points for a unif. o/b
POINTS_PER_MINUTE_FOR_AVERAGES = 4  # at least this many points for a unif. o/b
UNIFORM_POINTS_PER_HOUR = 60

DEFAULT_GRAPH_TIME_RANGE = 60  # minutes

VOLUME24H_UPDATE_PERIOD = 5  # minutes, affects the backend only
# NOTE FUNDING_UPDATE_PERIOD should be 15 minutes or less
FUNDING_UPDATE_PERIOD = 10  # minutes, affects the backend only

FILE_BACKEND_LOG = "tguiBackend.log"
MAX_LOG_SZ = 50 * 10**6  # maximum log file size in bytes
N_DAYS_TO_KEEP_LOGS = 14

BACKEND_DIRS = [
	"/home/ahhon/projects/klakteuh/tgui/",
	"/home/ahhon/projects/tgui/",
]

OBSERVER_FREQ = 900  # seconds
FILE_OBSERVER_LOG = "observer.log"
#
#SENDER_EMAIL = "sickworld2000@yandex.ru"
SENDER_EMAIL = "johnprankster2000@gmail.com"
RECIPIENT_EMAIL = "ahhon2000@yandex.ru"
#SMTP_SERVER = "smtp.yandex.ru"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
PASSWORD_FILE_SMTP = "mail_pw"

BACKEND_RESTART_MAX_FREQ = 60  # min seconds between manual backend restarts
