# By Somsak Lima 
import struct
import time, ubinascii, machine, ssd1306
from machine import UART, Pin, SoftI2C
from micropython import const
from micropyGPS import MicropyGPS

addrOled    = 60  #0x3c
hSize       = 64
wSize       = 128 
#oledIsConnected = False

stop = False
LED_GPIO = const(2)  # define a constant
led = machine.Pin(LED_GPIO, mode=machine.Pin.OUT)  # GPIO output
led = Pin(2, Pin.OUT)
relay1 = Pin(12, Pin.OUT)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000)  # ESP32 Dev Board /myown

uart1 = UART(1, 9600)
uart1.init(9600, bits=8, parity=None, stop=1, tx=12, rx=25)
uart2 = UART(2, 115200, timeout=300)
my_gps = MicropyGPS(+7)
rstr = ""

def sendATcommand(ATcommand):
    print("Command: {0}\r\n".format(ATcommand))
    print(ATcommand)
    uart2.write("{0}\r\n".format(ATcommand))
    rstr = uart2.read().decode("utf-8")
    print(rstr)
    return rstr

def Oledhello():
    oled.text("Hello", 0, 0)
    oled.text( "LoRaWAN Thailand",0, 17)
    oled.text("Start OTA Join", 0, 32)
    oled.text( "Waiting......",0, 49)
    oled.show()
    
oled = ssd1306.SSD1306_I2C(wSize, hSize, i2c, addrOled)
Oledhello()

sendATcommand("AT")
sendATcommand("AT+INFO")
sendATcommand("AT+APPEUI")
sendATcommand("AT+DEVEUI")
sendATcommand("AT+APPKEY")
sendATcommand("AT+NCONFIG")
sendATcommand("AT+CHSET")

###LOOP OTAA
sendATcommand("AT+NRB")
time.sleep(20.0)
rstr = sendATcommand("AT+CGATT")
tryno = 1
while rstr != "+CGATT:1":
    rstr = sendATcommand("AT+CGATT")
    print("Respond String")
    print(rstr)
    if rstr.startswith("+CGATT:1"):
        print("*******OTAA OK*******")
        break
    print("Retry OTAA Continue")
    b = str(tryno)
    print(b[-1:])
    if b[-1:] == "0":
        print("YES")
        sendATcommand("AT+NRB")
    else:
        print("NO")
    tryno = tryno + 1

    time.sleep(20.0)
print("Join Success")
###END LOOP OTAA

oled.fill(0)
oled.text( "Join Success",0, 24)
oled.show()
time.sleep(5.0)

cnt = 1
while True:
    print("\r\n\r\nPacket No #{}".format(cnt))
    
    my_sentence = uart1.readline()
    #my_sentence = (b"$GNGGA,215439.000,1348.3435,N,10030.7016,E,1,08,1.5,25.7,M,0.0,M,,*4B\r\n")
    #my_sentence = (b"$GNGGA,215439.000,1348.3435,N,10030.7016,E,5,15,1.1,470.50,M,45.65,M,,*75\r\n")
    print(my_sentence)
    for x in str(my_sentence):
        my_gps.update(x)

    print("---------------------------  ")
    lat1 = my_gps.latitude[0] + my_gps.latitude[1] / 60
    lon1 = my_gps.longitude[0] + my_gps.longitude[1] / 60
    speed=my_gps.speed[2]
    print('Date:',my_gps.date_string('s_dmy'))
    print("LATITUDE %2.6f" % float(lat1))
    print("LONGIITUDE %2.6f" % float(lon1))
    print("ALTITUDE %f" % float(my_gps.altitude))
    print ("Speed KM/H "+my_gps.speed_string('kph'))
    print (speed)
    print("---------------------------  ")

    oled.fill(0)
    oled.text("Packet No:"+str(cnt), 0, 0)
    oled.text("Date:"+my_gps.date_string('s_dmy'), 0, 10)
    oled.text("Time:"+str(my_gps.timestamp[0])+":"+str(int(my_gps.timestamp[1]))+":"+str(int(my_gps.timestamp[2])), 0, 20)
    oled.text("Sat:"+str(my_gps.satellites_in_use), 0, 30)
    oled.text("LAT:"+str(float(lat1)), 0, 40)
    oled.text("LON:"+str(float(lon1)), 0, 50)
    oled.show()

    cpu_temp=35
    bat=3
    speed = struct.pack('h', int(speed))
    bat_pack = struct.pack('h', int(bat))
    lat_pack = struct.pack('i', int(lat1 * 1000000))
    lon_pack = struct.pack('i', int(lon1 * 1000000))
    b = (bat_pack + speed + lat_pack + lon_pack)
    b = ubinascii.hexlify(b)
    
    
    print("************    Sending Data Status   **************")
    led.value(1)
    ATresp = sendATcommand(
        "AT+NMGS={0},{1}".format(int(len(b) / 2), b.decode("utf-8"))
    )
    print("********Finish Sending & Receiving Data Status******")
    led.value(0)
    cnt = cnt + 1
    time.sleep(5.0)
