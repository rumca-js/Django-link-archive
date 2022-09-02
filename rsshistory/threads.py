import threading
import logging
import datetime
import traceback
import sys


class ThreadJobCommon(threading.Thread):

   def __init__(self, name = "ThreadJobCommon", seconds_wait = 1, itemless = False):
       threading.Thread.__init__(self)
       self._started_server_loop = False
       self._process_list = []
       self._process_item = None
       self._seconds_wait = seconds_wait
       self._close_event = threading.Event()
       self._itemless = itemless

       self._thread_name = name

   def set_config(self, config):
       self._config = config

   def get_config(self):
       return self._config

   def run(self):
       if self._started_server_loop == False:
           self.start_server_loop()

       while not self._close_event.is_set():
           if not self.handle_process_item():
               self._close_event.wait(self._seconds_wait)

       self.log_info("Leaving process")

   def handle_process_item(self):
       try:
           if self._itemless:
               self.process_item()
       except Exception as E:
           logging.critical(E, exc_info=True)
           traceback.print_exc(file=sys.stdout)

       if len(self._process_list) == 0:
           return False

       item = self._process_list.pop(0)

       try:
           self._process_item = item
           self.process_item(item)
           self._process_item = None
       except Exception as E:
           logging.critical(E, exc_info=True)
           traceback.print_exc(file=sys.stdout)

       try:
           self.finished_item(item)
       except Exception as E:
           logging.critical(E, exc_info=True)
           traceback.print_exc(file=sys.stdout)

       if len(self._process_list) == 0:
           try:
               self.finished_all()
           except Exception as E:
               logging.critical(E, exc_info=True)
               traceback.print_exc(file=sys.stdout)

       return True

   def get_thread_name(self):
       return self._thread_name

   def log_error(self, text):
       logging.error(self._thread_name + ":" + text)

   def log_info(self, text):
       logging.info(self._thread_name + ":" + text)

   def process_item(self, item = None):
       self._config.t_process_item(self._thread_name, item)

   def finished_item(self, item):
       pass

   def finished_all(self):
       self.log_info("All items were processed")

   def add_to_process_list(self, item):
       self._process_list.append(item)

   def get_processs_list(self):
       return self._process_list

   def get_process_item(self):
       item = self._process_item

       if item is None:
          if len(self._process_list) > 0:
              item = self._process_list[0]
       return item

   def get_queue_size(self):
       count = len(self._process_list)
       if self.get_process_item() is not None:
          count += 1
       return count

   def start_server_loop(self):
       self._started_server_loop = True
       self.log_info("Started thread loop")

   def close(self):
       self.log_info("Stopping thread loop")
       self._close_event.set()

   def get_safe_item_str(self, item):
       return basictypes.get_ascii_text(str(item))

