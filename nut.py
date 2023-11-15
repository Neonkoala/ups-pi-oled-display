#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import socket
import time
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'waveshare')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from nut2 import PyNUTClient
from waveshare import epd2in13_V3
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG)

starttime = time.monotonic()
epd = epd2in13_V3.EPD()

def update_display(full = False):
    # Init
    hostname = "localhost"

    upsBatteryCharge = "N/A"
    upsBatteryRemaining = "N/A"

    # Data gathering
    hostname = socket.gethostname()
    
    client = PyNUTClient()
    ups = client.list_vars("ups")

    upsBatteryCharge = ups["battery.charge"]
    upsBatteryRemainingSeconds = ups["battery.runtime"]
    upsBatteryRemaining = str(round(int(upsBatteryRemainingSeconds) / 60))
    upsLoad = ups["ups.load"]

    # Drawing on the image
    font15 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 15)
    font24 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 24)
    
    logging.info("1.Drawing on the image...")
    image = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame    
    draw = ImageDraw.Draw(image)
    
    # Battery icon
    draw.rectangle([(25,40),(45,50)], outline = 0)
    draw.rectangle([(15,50),(55,110)], outline = 0)
    draw.rectangle([(15,50),(55,110)], fill = 0)

    # Info
    draw.text((0, 0), hostname, font = font24, fill = 0)
    draw.text((70, 35), upsBatteryCharge + "%", font = font15, fill = 0)
    draw.text((70, 55), upsBatteryRemaining + " minutes", font = font15, fill = 0)
    draw.text((70, 75), upsLoad + "W", font = font15, fill = 0)

    image = image.rotate(180) # rotate
    if full:
        epd.display(epd.getbuffer(image))
    else:
        epd.displayPartial(epd.getbuffer(image))

    # epd.sleep()

try:
    logging.info("epd2in13_V3 Demo")

    # Display
    logging.info("init and Clear")
    epd.init()
    # epd.Clear(0xFF)

    update_display(True)

    while True:
        logging.info("Display update")
        update_display()

        time.sleep(5.0 - ((time.monotonic() - starttime) % 5.0))
    
    # # partial update
#    logging.info("4.show time...")
#    time_image = Image.new('1', (epd.height, epd.width), 255)
#    time_draw = ImageDraw.Draw(time_image)
#    
#    epd.displayPartBaseImage(epd.getbuffer(time_image))
#    num = 0
#    while (True):
#        time_draw.rectangle((120, 80, 220, 105), fill = 255)
#        time_draw.text((120, 80), time.strftime('%H:%M:%S'), font = font24, fill = 0)
#        epd.displayPartial(epd.getbuffer(time_image))
#        num = num + 1
#        if(num == 10):
#            break
    
    # logging.info("Clear...")
    # epd.init()
    # epd.Clear(0xFF)
    
        
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd2in13_V3.epdconfig.module_exit()
    exit()
