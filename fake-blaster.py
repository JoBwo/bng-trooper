## This will spawn a message every second and exit gracefully when receiving sigint
import time
import signal
import sys

def signal_handler(sig, frame):
	print("\nThe program has executed.")
	print("Finishing gracefully.")
	sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

for i in range(10):
	print("I am doing stuff", flush=True)
	time.sleep(1)