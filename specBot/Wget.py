import Config
import subprocess

class Wget:
	def __init__(self, baseCmd=[]):
		if not baseCmd:
			baseCmd = [
				"wget",
				"--timeout=%d" % Config.WGET_TIMEOUT,
			]

		self.baseCmd = baseCmd


	def run(self, cmd):
		cmd = [
			"timeout",
			"--kill-after=%d" % (Config.WGET_TIMEOUT + 3),
			"%d" % Config.WGET_TIMEOUT,
		] + self.baseCmd + cmd

		print("wget command:", cmd)

		st = subprocess.call(cmd)

		return st


class WgetDummy: pass
