import subprocess

class Pipe:

	def __init__(self, cmd, stdin=""):
		"""Run command cmd given in the list form piping stdin to it

		stdin is a string

		A Pipe object has the following attributes:
			stdout    string, contains the command's stdout
			stderr    string, contains the command's stderr
			status    int, the command's exit status

		USAGE EXAMPLE:

			cmd = ["cat"]
			s = Pipe(cmd, "Hello, World!").stdout
			print(s)
		"""

		p = subprocess.Popen(
			cmd,
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
		)

		(stdout, stderr) = p.communicate(stdin.encode())
		status = p.returncode

		if stdout:
			stdout = stdout.decode(errors='ignore')
		else:
			stdout = ""

		if stderr:
			stderr = stderr.decode(errors='ignore')
		else:
			stderr = ""

		self.status = status
		self.stdout = stdout
		self.stderr = stderr
