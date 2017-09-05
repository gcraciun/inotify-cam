#!/usr/bin/env python

import logging
import inotify.adapters
import re
import subprocess
import shlex
import os
import errno

# Create our logger for this application
app_logger = logging.getLogger(__name__)

def log_setup():
  """ Sets all other parameters related to logging """
  # Set the logger level to INFO
  app_logger.setLevel(logging.INFO)
  # Create a formater (log format)
  app_log_fmt = logging.Formatter('%(asctime)s - %(name)s - %(filename)s - %(levelname)s - %(message)s')
  # Create the Console Handler (ch) / It should log only ERRORs or above
  ch = logging.StreamHandler()
  ch.setLevel(logging.ERROR)
  # Create the File Handler (fh) / It should log only INFO or above
  fh = logging.FileHandler('myapp.log')
  fh.setLevel(logging.INFO)
  # Apply the log format (formatter) to the Two handlers crested above
  ch.setFormatter(app_log_fmt)
  fh.setFormatter(app_log_fmt)
  # Add the Two handlers to our app logger
  app_logger.addHandler(ch)
  app_logger.addHandler(fh)
                                  
def match_vids(file_name):
  my_reg = re.compile(r"^vid\d{1,2}\.h264$")
  my_match = my_reg.match(file_name.decode('utf-8'))
  if my_match:
   return True
  else:
   return False

def create_mp4(h264path, h264file):
  (file, ext) = h264file.split('.')
  mp4file = ".".join((file, 'mp4'))
  cmd_line = "/usr/bin/MP4Box -fps 15 -add "+h264path+"/"+h264file+" "+h264path+"/"+mp4file

  cmd_line_fmt = shlex.split(cmd_line)

  try:
   os.remove(h264path+'/'+mp4file)
  except OSError as e:
    if e.errno == errno.ENOENT:
      app_logger.error('trying to remove non-existent file '+h264path+'/'+mp4file)
    if e.errno == errno.EPERM:
      app_logger.error('not enough permissions to remove file '+h264path+'/'+mp4file)
  except Exception:
    app_logger.error('another major error')
  app_logger.info('Starting mp4box with cmd_line = '+cmd_line)
#  subprocess.call([ '/usr/bin/MP4Box', '-fps', '15', '-add', h264path+'/'+h264file, h264path+'/'+mp4file ],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
  subprocess.call(cmd_line_fmt, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

def main():
  i = inotify.adapters.Inotify()
  i.add_watch(b'/mnt/sdc1/fridge3')

  try:
    for event in i.event_gen():
      if event is not None:
        (header, type_names, watch_path, filename) = event
        if (header.mask == 8):
          app_logger.info('New writtern file detected '+filename.decode('utf-8'))
          if match_vids(filename):
            app_logger.info('File matched our regular expression')
            app_logger.debug("WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s "
                             "WATCH-PATH=[%s] FILENAME=[%s]",
                             header.wd, header.mask, header.cookie, header.len, type_names,
                             watch_path.decode('utf-8'), filename.decode('utf-8'))
            create_mp4(watch_path.decode('utf-8'), filename.decode('utf-8'))
          else:
            app_logger.info('File did not match our regular expression')
  finally:
   i.remove_watch(b'/mnt/sdc1/fridge3')

if __name__ == '__main__':
  log_setup()
  main()
