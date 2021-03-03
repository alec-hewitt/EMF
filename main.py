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
from polaris_read import Polaris

digilent = Digilent()
while(digilent.open()):
    print("Cannot connect to digilent")

polaris = Polaris()
polaris.init()

global first_run
first_run = 1

#bus = busio.I2C(board.SCL, board.SDA)
#amp = MAX.MAX9744(bus)
#amp.volume = 60

def save(id, data):
    global first_run
    print(data)
    print("\n")
    file = 'results/' + id + '.txt'

    if(os.path.exists(file)):
        if(first_run == 1):
            f = open(file, "w")
        else:
            f = open(file, "a")
    else:
        f = open(file, "w")

    f.write(str(data) + "\n")

    f.close()
    first_run = 0

time.sleep(8)

print("Retrieving Device ID")
id = polaris.get_id()
print("Connected to Polaris " + id)

print("Generating none for ambient reading")
digilent.sine_out(0, 0) #0mG
save(id, polaris.sample_single(0, 0))

print("Generating 5 mGauss Field @ 60 Hertz")
digilent.sine_out(60, 0.039) #60Hz 5mG
save(id, polaris.sample_single(60, 5))

print("Generating 10 mGauss Field @ 60 Hertz")

digilent.sine_out(60, 0.078) #60Hz 10mG
save(id, polaris.sample_single(60, 10))
print("Generating 15 mGauss Field @ 60 Hertz")

digilent.sine_out(60, 0.116) #60Hz 15mG
save(id, polaris.sample_single(60, 15))

print("Generating 5mGauss Field @ 120 Hertz")
digilent.sine_out(120, 0.039) #120Hz 5mG
save(id, polaris.sample_single(120, 5))

print("Generating 5mGauss Field @ 180 Hertz")
digilent.sine_out(180, 0.039) #180Hz 5mG
save(id, polaris.sample_single(180, 5))

digilent.sine_out(0, 0)

time.sleep(1)
#amp.volume = 0
digilent.disable_analog()
digilent.close()
