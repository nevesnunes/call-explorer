import os
import sys

def eventTrace(frame, event, arg, indent=[0]):
      if event == "call":
          indent[0] += 2
          print "-" * indent[0] + "> call function", frame.f_code.co_name
      elif event == "return":
          print "<" + "-" * indent[0], "exit function", frame.f_code.co_name
          indent[0] -= 2
      return eventTrace

class Logger:
    def __init__(self, activated):
        #sys.settrace(eventTrace)

        self.activated = activated
        self.logs = {}
        for logname in [ "error", "trace"]:
            try:
                os.remove("./" + logname + ".txt")
            except OSError:
                pass
            self.logs[logname] = open("./" + logname + ".txt", "a")

    def log(self, filename, message):
        if self.activated:
            self.logs[filename].write(message + "\n")

    def __exit__(self, exc_type, exc_value, traceback):
        for log in self.logs:
            log.close()
