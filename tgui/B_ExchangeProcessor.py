import time
import os, sys
import traceback
import signal

import Config
from TGui import TGui
from B_UniformOrderbooks import B_UniformOrderbooks
from loggers import genLoggers


class B_ExchangeProcessor:
	def __init__(self, ExCls):
		self.ExCls = ExCls
		tg = TGui(readOnly=False)
		self.exchange = ExCls(tg)

		fn = self.exchange.name + ".log"
		(self.log, self.loge, self.logw) = genLoggers(fn)
		self.exchange.cbLog = self.log

		self.pid = os.getpid()


	def _setSignalHandlers(self):
		def sigHandler(sig, frame):
			nonlocal self
			if sig == signal.SIGTERM:
				self.log("normal shutdown")
				sys.exit(0)
		signal.signal(signal.SIGTERM, sigHandler)
		signal.signal(signal.SIGINT, sigHandler)
	

	def uniformOrderbooks(self, ex):
		buo = B_UniformOrderbooks(ex)
		buo.cycle()
		if buo.errorMessage:
			self.log(buo.errorMessage)


	def runForever(self):
		ex = self.exchange
		self._setSignalHandlers()
		self.log("started (pid={pid})".format(pid=self.pid))

		while True:
			self.log(" *** Cycle for {exn}".format(exn=ex.name))
			msg = ""
			try:
				self.log("\tconnecting/reconnecting...")
				msg = ex.connectReconnect()
				if msg: self.log(msg)

				self.log("\tdownloading instruments...")
				ex.downloadInstruments()

				self.log("\tretrieving orderbooks")
				ex.pullOrderbooks()

				self.log("\tcreating uniform orderbooks...")
				self.uniformOrderbooks(ex)

				self.log("\tcleaning up old orderbooks...")
				ex.cleanupOldOrderbooks()

				self.log("\ttrying to update volume data...")
				ex.pullVolume()

				self.log("\tupdating funding data...")
				ex.pullFunding()
			except KeyboardInterrupt:
				pass
			except Exception as e:
				msg = "exception in runForever(): " + str(e)
				msg += "\n" + "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
				self.loge(msg)
			self.log(" *** End of cycle ({exn})".format(exn=ex.name))

			time.sleep(Config.BACKEND_LOOP_INTERVAL)
