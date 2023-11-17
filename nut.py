#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import os
import time
import sys
from datetime import timedelta
from enum import Enum
from nut2 import PyNUTClient
from PIL import Image, ImageDraw, ImageFont
from uptime import uptime

libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'waveshare')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare import epd2in13_V3

logging.basicConfig(level=logging.DEBUG)

start_time = time.monotonic()
epd = epd2in13_V3.EPD()


class UPSStatus(Enum):
    online = "OL"
    online_low_battery = "OL LB"
    online_low_voltage = "OL BOOST"
    online_charge = "OL CHRG"
    online_charge_low_battery = "OL CHRG LB"
    online_discharge = "OL DISCHRG"
    online_discharge_low_battery = "OL DISCHRG LB"
    battery_discharge = "OB DISCHRG"
    battery_discharge_low_battery = "OB DISCHRG LB"
    battery_low_battery = "OB LB"
    replace_battery = "RB"
    bypass = "BYPASS"


class UPSOnlineStatus(Enum):
    online = 1
    offline = 2
    unknown = 3


class UPSChargeStatus(Enum):
    charging = 1
    discharging = 2
    none = 3


class UPSOtherStatus(Enum):
    low_battery = 1
    low_voltage = 2
    none = 3


def ups_online_status(status: UPSStatus):
    if status in [UPSStatus.online, UPSStatus.online_low_battery, UPSStatus.online_low_voltage, UPSStatus.online_charge,
                  UPSStatus.online_charge_low_battery, UPSStatus.online_discharge,
                  UPSStatus.online_discharge_low_battery]:
        return UPSOnlineStatus.online
    elif status in [UPSStatus.battery_discharge, UPSStatus.battery_discharge_low_battery,
                    UPSStatus.battery_low_battery]:
        return UPSOnlineStatus.offline
    else:
        return UPSOnlineStatus.unknown


def ups_charge_status(status: UPSStatus):
    if status in [UPSStatus.online_charge, UPSStatus.online_charge_low_battery]:
        return UPSChargeStatus.charging
    elif status in [UPSStatus.battery_discharge, UPSStatus.battery_discharge_low_battery, UPSStatus.online_discharge,
                    UPSStatus.online_discharge_low_battery]:
        return UPSChargeStatus.discharging
    else:
        return UPSChargeStatus.none


def ups_other_status(status: UPSStatus):
    if status == UPSStatus.online_low_voltage:
        return UPSOtherStatus.low_voltage
    elif status in [UPSStatus.online_low_battery, UPSStatus.online_charge_low_battery,
                    UPSStatus.online_discharge_low_battery, UPSStatus.battery_discharge_low_battery,
                    UPSStatus.battery_low_battery]:
        return UPSOtherStatus.low_battery
    else:
        return UPSOtherStatus.none


def update_display(full=False):
    # Init
    ups_battery_charge = "N/A"
    ups_battery_remaining = "N/A"

    # Data gathering
    client = PyNUTClient()
    ups = client.list_vars("ups")

    ups_battery_charge = ups["battery.charge"]
    ups_battery_remaining_seconds = ups["battery.runtime"]
    ups_battery_remaining = str(round(int(ups_battery_remaining_seconds) / 60))
    ups_load = ups["ups.load"]
    ups_status_code = ups["ups.status"]

    # Drawing on the image
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

    segment_count = 5
    segment_height = 18

    segment_x = margin + line_thickness + spacing
    segment_y = margin + top_height + line_thickness
    segment_width = margin + width - line_thickness - spacing
    segment_max = segment_y + (segment_height * segment_count) + (spacing * segment_count)

    # Top contact
    draw.rounded_rectangle(((top_inset + margin, margin), (margin + width - top_inset, margin + top_height)),
                           radius=5, fill=0, corners=(True, True, False, False))

    # Casing
    draw.rounded_rectangle(((margin, margin + top_height), (margin + width, margin + top_height + height)),
                           radius=radius, width=line_thickness, outline=0)

    # Calculate & draw battery segments
    draw_segments = (float(ups_battery_charge) / 100) * segment_count

    i = 0
    while i < draw_segments - 1:
        rect_index = i + 1
        draw.rectangle(((segment_x, segment_max - (i * spacing) - (rect_index * segment_height)),
                        (segment_width, segment_max - (i * spacing) - (i * segment_height))), fill=0)
        i += 1

    text_margin = 10
    text_offset = (2 * margin) + width + text_margin
    text_spacing = 4
    font = 20

    # Status
    status = UPSStatus(ups_status_code)
    online_status = ups_online_status(status)
    charge_status = ups_charge_status(status)
    other_status = ups_other_status(status)

    status_text = "Unknown"
    if online_status == UPSOnlineStatus.online:
        status_text = "Online"
    elif online_status == UPSOnlineStatus.offline:
        status_text = "Offline"

    if other_status == UPSOtherStatus.low_voltage:
        status_text += " (Low Voltage)"
    elif other_status == UPSOtherStatus.low_battery:
        status_text += " (Low Battery)"

    battery_status_text = "%"
    if charge_status == UPSChargeStatus.charging:
        battery_status_text = "% Charging"
    elif charge_status == UPSChargeStatus.discharging:
        battery_status_text = "% Discharging"

    # Draw text
    draw.text((text_offset, 0), status_text, font=font20, fill=0)
    draw.text((text_offset, font + text_spacing), ups_battery_charge + battery_status_text, font=font20, fill=0)
    draw.text((text_offset, (2 * font) + (2 * text_spacing)), "Remaining: " + ups_battery_remaining + " mins",
              font=font20, fill=0)
    draw.text((text_offset, (3 * font) + (3 * text_spacing)), "Load: " + ups_load + "W", font=font20, fill=0)
    draw.text((text_offset, (4 * font) + (4 * text_spacing)), "Up: " + str(timedelta(seconds=uptime())).split(".")[0],
              font=font20, fill=0)

    # Fix rotation by 180deg
    image = image.rotate(180)  # rotate
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

        time.sleep(1.0 - ((time.monotonic() - start_time) % 1.0))

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
