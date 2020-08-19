import time
import os, sys
import traceback
from multiprocessing import Process
import signal

from Observer import Observer
import Config
from B_ExchangeProcessor import B_ExchangeProcessor
from Date import Date
from TGui import TGui
from loggers import genLoggers


class Backend:
	def __init__(self):
		tg = TGui(readOnly=False)

		pid = os.getpid()
		tg.setPar("tguiBackend_pid", pid)

		self.tg = tg
		self.ps = []
		self.pid = os.getpid()

		(self.log, self.loge, self.logw) = genLoggers(Config.FILE_BACKEND_LOG)


	def _sigHandler(self, sig, frame):
		if sig == signal.SIGTERM:
			for p in self.ps:
				p.terminate()
				p.join()

			tg = TGui(readOnly=False)
			tg.setPar("tguiBackend_pid", "")
			self.log("normal shutdown")
			sys.exit(0)


	def _setSignalHandlers(self):
		def sigHandler(sig, frame):
			nonlocal self
			self._sigHandler(sig, frame)

		signal.signal(signal.SIGTERM, sigHandler)
		signal.signal(signal.SIGINT, sigHandler)


	def runForever(self):
		self._setSignalHandlers()
		self.log("started (pid={pid})".format(pid=self.pid))

		def exProcessor(ExCls):
			ep = B_ExchangeProcessor(ExCls)
			ep.runForever()

		ps = self.ps
		for ExCls in TGui.exchangeClasses:
			p = Process(target=exProcessor, args=(ExCls,))
			p.start()
			ps += [p]

		# add the observer process
		def observerTarget():
			observer = Observer()
			observer.runForever()
		p = Process(target=observerTarget)
		p.start()
		ps += [p]

		for p in ps: p.join()


	def __enter__(self):
		return self


	def __exit__(self, a, b, c):
		if a is SystemExit  or  a is InterruptedError: return
		if a is KeyboardInterrupt: return
		msg = "the backend caught an exception class={ec}:{b}".format(b=b, ec=a.__name__ if a else "?")
		msg += "\n" + "".join(traceback.format_exception(a, b, c))
		self.loge(msg)
		self._sigHandler(signal.SIGTERM, None)
