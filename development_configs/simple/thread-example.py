import threading
import time
from pydispatch import dispatcher

# Define signal name
SIGNAL = 'test_signal'


def sender():
  """Thread function to send signals every 5 seconds."""
  while True:
    print('Sending signal...')
    dispatcher.send(signal=SIGNAL, sender='sender_thread', message='Hello from sender')
    time.sleep(5)


def receiver(sender, message):
  """Receiver function to handle signals."""
  print(f'Received signal from {sender}: {message}')


def receiver_thread():
  """Thread function to connect the receiver to the signal."""
  dispatcher.connect(receiver, signal=SIGNAL, sender=dispatcher.Any)
  # Keep the thread alive to listen for signals
  while True:
    time.sleep(1)


def main():
  # Create and start the sender thread
  sender_thread = threading.Thread(target=sender)
  sender_thread.daemon = True
  sender_thread.start()

  # Create and start the receiver thread
  receiver_thread_instance = threading.Thread(target=receiver_thread)
  receiver_thread_instance.daemon = True
  receiver_thread_instance.start()

  # Keep the main thread alive
  while True:
    time.sleep(1)


if __name__ == '__main__':
  main()
