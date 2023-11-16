#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import socket
import time
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'waveshare')
if os.path.exists(libdir):
    sys.path.append(libdir)

from datetime import timedelta
from enum import Enum
import logging
from nut2 import PyNUTClient
from waveshare import epd2in13_V3
import time
from PIL import Image,ImageDraw,ImageFont
import traceback
from uptime import uptime

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
    upsStatusCode = ups["ups.status"]

    # Drawing on the image
    font15 = ImageFont.truetype(os.path.join(libdir, 'GillSans.ttf'), 15)
    font18 = ImageFont.truetype(os.path.join(libdir, 'GillSans.ttf'), 18)
    font20 = ImageFont.truetype(os.path.join(libdir, 'GillSans.ttf'), 20)
    
    logging.info("1.Drawing on the image...")
    image = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame    
    draw = ImageDraw.Draw(image)
    
    # Battery icon

    line_thickness = 2

    radius = 5
    margin = 3
    spacing = 2
    height = 106
    width = 50

    top_inset = 10
    top_height = 10

    segment_height = 18

    segment_x = margin + line_thickness + spacing
    segment_y = margin + top_height + line_thickness
    segment_width = margin + width - line_thickness - spacing

    # Top contact
    draw.rounded_rectangle([(top_inset + margin, margin), (margin + width - top_inset, margin + top_height)], fill = 0, radius = 5, corners = (True, True, False, False))

    # Casing
    draw.rounded_rectangle([(margin, margin + top_height),(margin + width, margin + top_height + height)], radius = radius, width = line_thickness, outline = 0)

    segments = 5

    i = 0
    while i <= segments:
        rect_index = i + 1
        draw.rectangle([(segment_x, segment_y + (rect_index * spacing) + (segment_height * i)),(segment_width, segment_y + (rect_index * spacing) + (rect_index * segment_height))], fill = 0)
        i += 1

    text_margin = 10
    text_offset = (2 * margin) + width + text_margin
    text_spacing = 4
    font = 20

    # Info
    # draw.text((text_offset, margin), hostname, font = font20, fill = 0)
    # draw.text((text_offset, 35), upsBatteryCharge + "%", font = font18, fill = 0)
    # draw.text((text_offset, 55), upsBatteryRemaining + " minutes", font = font18, fill = 0)
    # draw.text((text_offset, 75), upsLoad + "W", font = font18, fill = 0)

    # Status
    draw.text((text_offset, 0), "Status: " + upsStatusCode, font = font20, fill = 0)
    draw.text((text_offset, font + text_spacing), upsBatteryCharge + "%", font = font20, fill = 0)
    draw.text((text_offset, (2 * font) + (2 * text_spacing)), "Remaining: " + upsBatteryRemaining + " mins", font = font20, fill = 0)
    draw.text((text_offset, (3 * font) + (3 * text_spacing)), "Load: " + upsLoad + "W", font = font20, fill = 0)
    draw.text((text_offset, (4 * font) + (4 * text_spacing)), "Up: " + str(timedelta(seconds=uptime())).split(".")[0], font = font20, fill = 0)

    # Fix rotation by 180deg
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

        time.sleep(1.0 - ((time.monotonic() - starttime) % 1.0))
    
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
