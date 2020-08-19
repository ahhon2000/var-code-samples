DB_FILE = "specBot.db"
DB_NAME = "specbot"

CURRENCY1 = "USD"
CURRENCY2 = "WMX"
PURSE1 = "Z143819301566"
#PURSE2 = "R632098701410"
#PURSE2 = "H397728883106"
PURSE2 = "X700322743845"
WMID = "121371724997"

WM_CERTIFICATE_FILE = "/home/ahhon/wmcert/wm_20170913_0130_pw.pem"
WM_KEY_FILE = "/home/ahhon/wmcert/wm_20170913_0130_pw.key"

# Maximum amount to trade (CURRENCY1). 0 means no limit
MAXIMUM_AMOUNT1 = 0

# Initial amount to trade. Is used for the 1st transaction only.
#	0 means `use MAXIMUM_AMOUNT1'
INITIAL_AMOUNT1 = 520

#MAX_PLACE_FOR_WEIGHING = 20
#MAX_PLACE_FOR_WEIGHING = 15
#MAX_PLACE_FOR_WEIGHING = 10
MAX_PLACE_FOR_WEIGHING = 5

# minimum relative profit per one roundtrip transaction (a fraction of 1)
#MIN_REL_PROFIT = 0.0010
#MIN_REL_PROFIT = 0.0030  # since 2017-09-30 00:00
#MIN_REL_PROFIT = 0.0010  # since 2017-10-03 00:43
MIN_REL_PROFIT = 0.01

# After this time since the moment a reverse transaction was opened
# minProfitRate() will return tar2. Set to 0 to disable this behaviour
#HOURS_MIN_REL_PROFIT_REVERSE = 24*4
#HOURS_MIN_REL_PROFIT_REVERSE = 18
HOURS_MIN_REL_PROFIT_REVERSE = 0

# Time interval over which to average MarketState's average rates
#RATE_AVG_HOURS = 1
RATE_AVG_HOURS = 0.166667

# maximum allowed deviation of rate1 or rate2 from MarketState averages
MAX_RATE_DEVIATION = 0.4

#
# Rate setting modes
#
RSM = [
	"RSM_SPREAD_AND_MIN_PROFIT",
	"RSM_MIN_PROFIT",
	"RSM_SMART_MIN_PROFIT",
	"RSM_1TAR_2MIN_PROFIT",
]
for i in range(len(RSM)): exec("%s = %d" % (RSM[i], i))

#RATE_SETTING_MODE = RSM_SPREAD_AND_MIN_PROFIT
#RATE_SETTING_MODE = RSM_SMART_MIN_PROFIT
#RATE_SETTING_MODE = RSM_MIN_PROFIT
RATE_SETTING_MODE = RSM_1TAR_2MIN_PROFIT

#
# Database Format
#

DBF = [
	"DBF_SQLITE3",
	"DBF_MARIADB",
]
for i in range(len(DBF)): exec("%s = %d" % (DBF[i], i))

#DB_FORMAT = DBF_SQLITE3
DB_FORMAT = DBF_MARIADB

DB_USER = "spbu"
DB_PASSWORD = "trident1"
DB_USER_RO = "spbu_ro"
DB_PASSWORD_RO = "trident2"

_TMP_DIR = "/tmp"
LOG_FILE = "specBot.log"

# maximum log file size in bytes
MAX_LOG_SZ = 10 * 10**6

SENDER_EMAIL = "sickworld2000@yandex.ru"
RECIPIENT_EMAIL = "ahhon@mail.ru"
SMTP_SERVER = "smtp.yandex.ru"
PASSWORD_FILE_SMTP = "mail_pw"

MIN_MINUTES_BTW_REQUESTS = 3

WM_COMMISSION = 0.008
COMMISSION_MAXIMA = {
	"USD": 50,
	"RUB": 1500,
	"WMX": 5,
	"WMH": 30,
}

MIN_RATE_CHANGE_TO_UPLOAD = 0.0001

WGET_TIMEOUT = 60

# the number of hours after which to send next notification about the
#	unavailability of market states
NO_MS_NOTIF_INTERVAL = 2

#
# MarketState source
#
MSSRC = [
	"MSSRC_HTML",
	"MSSRC_XML",
]
for i in range(len(MSSRC)): exec("%s = %d" % (MSSRC[i], i))
#MARKETSTATE_SOURCE = MSSRC_HTML
MARKETSTATE_SOURCE = MSSRC_XML

WM_CURRENCY_SYNONYMS = {
	"USD": "WMZ",
	"RUB": "WMR",
	"WMX": "WMX",
	"WMH": "WMH",
}
