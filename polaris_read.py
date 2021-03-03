import time
import os
import smbus
import board
import busio
import adafruit_max9744 as MAX
from digilent_ctrl import Digilent
from output_monitor import Monitor
import serial
import sys
import datetime
import logging
import json
import math

class Polaris:

    global bx, by, bz, id, ser, line_buff
    global stop
    stop = 0
    bx = 0.0
    by = 0.0
    bz = 0.0


    line_buff = ""

    def parse(self, buffer):
        global bx, by, bz, id, ser, line_buff
        global stop
        #print(line_buff)

        if("DeviceID:" in line_buff):
            id = line_buff[-8:-1]
            line_buff = ""
            stop = 1
        if("RMS" in line_buff):
            return 0
        if("Bx" in line_buff and "E" not in line_buff):
            bx = line_buff[-10:-1]
        if("By" in line_buff and "E" not in line_buff):
            by = line_buff[-10:-1]
        if("Bz" in line_buff and "E" not in line_buff):
            bz = line_buff[-10:-1]
        if("Ez-Bx" in line_buff):
            line_buff = ""
            stop = 1
        else:
            line_buff = ""
        line_buff = ""
        return 0

    def init(self):
        global bx, by, bz, id, ser, line_buff
        global stop
        stop = 0

        port = '/dev/ttyACM0'
        speed = 9600 #default baud

        serial_connection_established = False

        try:
            ser = serial.Serial(port,speed)
            serial_connection_established = True
        except:
            print("serial connection failed, device may be in sleep. retrying in 2 seconds...")
            time.sleep(2)

        while (False == serial_connection_established):
            try:
                ser = serial.Serial(port,speed)
                serial_connection_established = True
            except:
                print("retrying in 2 seconds...")
                time.sleep(2)

        ser.setDTR()
        ser.flushInput()

        ser.write("\r\n".encode())
        ser.write("pass polaris\r\n".encode())

    def loop(self):
        global bx, by, bz, id, ser, line_buff
        global stop
        while stop == 0:
            try:
                x = ser.read()
                line_buff = line_buff + x.decode("utf-8")
                #print(line_buff)
                if "\r" in line_buff or "\n" in line_buff:
                    #print("here")
                    #print(line_buff)
                    res = self.parse(line_buff)
                    line_buff = ""
                    if(res == 1):
                        line_buff = ""
                        return
            except Exception as e:
                print("err")
                print(e)
                ser.close()
                time.sleep(1)
                print("[PYTHON: Serial connection lost, re-establishing]")
                self.init()

    def sample_single(self, freq, mag):
        global bx, by, bz, id, ser, line_buff
        global stop
        line_buff = ""

        ser.write("sample single\r\n".encode())

        stop = 0

        self.loop()

        magnitude = math.sqrt(math.pow(float(bx), 2) + math.pow(float(by), 2) + math.pow(float(bz), 2))

        return [freq, mag, bx, by, bz, magnitude]

    def get_id(self):
        global bx, by, bz, id, ser, line_buff
        global stop
        stop = 0
        ser.write("config\r\n".encode())
        ser.write("1\r\n".encode())

        self.loop()

        stop = 0

        ser.write("4\r\n".encode())
        ser.write("9\r\n".encode())

        line_buff = ""
        time.sleep(1)
        return id
