import socket
import requests
from datetime import datetime
from time import sleep
import os
import wiringpi
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

# string from webserver
url = 'http://planetarium.chrisdemoor.nl/positions.txt'

# if test_modus is TRUE the webserver string is not used 
# TEST_website_string.py which runs on a seperate RPI provides the string
# this is for testing
test_modus = False
planeet_motor = True
if test_modus:
   url = 'http://192.168.178.52/positions.txt'

# which planet are we?
planeet = socket.gethostname()

if (planeet == "DMO-Saturnus"):
   totaal_stappen = 6683 # number of steps to make one full circle, 1% deviation
   magneet_positie = 2  # position in degrees where the magnet of the planet is
   beginpos_string = 15  # de beginpositie in de string bij de Curl van deze planeet
   eindpos_string  = 18  # de eindpositie in de string bij de Curl van deze planeet
   richting = stepper.BACKWARD
   stijl = stepper.DOUBLE
if (planeet == "DMO-Jupiter"):
   totaal_stappen = 4326 # number of steps to make one full circle, 1% deviation
   magneet_positie = 5  # position in degrees where the magnet of the planet is
   beginpos_string = 12  # de beginpositie in de string bij de Curl van deze planeet
   eindpos_string  = 15  # de eindpositie in de string bij de Curl van deze planeet
   richting = stepper.BACKWARD
   stijl = stepper.DOUBLE
if (planeet == "DMO-Mars"):
   totaal_stappen = 2045 # number of steps to make one full circle, 1% deviation
   magneet_positie = 88  # position in degrees where the magnet of the planet is
   beginpos_string = 9  # beginposition in the string 
   eindpos_string  = 12  # endposition in the string 
   richting = stepper.FORWARD
   stijl = stepper.DOUBLE
if (planeet == "DMO-Aarde"):
   totaal_stappen = 1107 # number of steps to make one full circle, 1% deviation
   magneet_positie = 106   # 6 september, position in degrees where the magnet of the planet is
   beginpos_string = 6  # beginposition in the string 
   eindpos_string  = 9  # endposition in the string 
   richting = stepper.BACKWARD
   stijl = stepper.DOUBLE
if (planeet == "DMO-Venus"):
   totaal_stappen = 1019 # aantal stappen om een rondje te maken, 1% afwijking per keer
   magneet_positie = 281  # position in degrees where the magnet of the planet is
   beginpos_string = 3  # beginposition in the string 
   eindpos_string  = 6  # endposition in the string 
   richting = stepper.BACKWARD
   stijl = stepper.DOUBLE
if (planeet == "DMO-Mercurius"):
   totaal_stappen = 202 # aantal stappen om een rondje te maken, 1% afwijking per keer
   magneet_positie = 83   # position in degrees where the magnet of the planet is
   beginpos_string = 0  # beginposition in the string 
   eindpos_string  = 3  # endposition in the string 
   richting = stepper.BACKWARD
   stijl = stepper.DOUBLE
    
# reedswitch
os.system('gpio export 19 in')
sleep(0.5)
io = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_GPIO_SYS)
io.pinMode(19,io.INPUT)

# Adafruit
kit = MotorKit()

schakelaar = "open"
teller = 1
positiestring     = ""
positiestring_oud = "001001001001001001001001001"
totaalteller = 1
offline_teller = 1

# first time startup wait 30 seconds for all background processes of RPI to startup, prevents bumpy ride in the beginning
sleep (30)

while True:

  #timestamp  DMO.log
  now = datetime.now()
  dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
  print ('-------------------------------')
  print (totaalteller , ' ' + dt_string + ' ' + planeet)
  
  try:
       r = requests.get(url, timeout=4)
       positiestring = r.text
       print ('ONLINE')
       offline_teller = 1
  except requests.exceptions.ConnectionError:
       positiestring = positiestring_oud
       print ('OFFLINE ', offline_teller)
       offline_teller +=1
       if offline_teller > 10:
          print ('RESTART ' + dt_string)
          os.system('sudo cp /home/pi/DMO/DMO.log /home/pi/DMO/DMOlog.old')
          os.system('sudo cp /home/pi/DMO/DMO.error /home/pi/DMO/DMOerror.old') 
          os.system('sudo shutdown -r now')
         
  print ('Mer ',positiestring[0:3],' Ven ',positiestring[3:6],' Aar ',positiestring[6:9],' Mar ',positiestring[9:12],' Jup ',positiestring[12:15],' Sat ',positiestring[15:18])

  # if there is a new position and we have got internet
  if str(positiestring) != str(positiestring_oud):   
      
    # first drive to magnet
    while (schakelaar == "open") and (not test_modus):
      kit.stepper1.onestep(direction=richting, style= stijl)
      if (io.digitalRead(19)):  
        schakelaar = "open"
      else:
        if teller > 200:
          schakelaar = "dicht"
      teller +=1
    sleep(1)  
   
    # calculation number of steps
    try:
       nieuwe_positie_planeet = int(positiestring[beginpos_string:eindpos_string])
    except:
       print ('FOUT in conversie van: ',  positiestring[beginpos_string:eindpos_string])
       nieuwe_positie_planeet = 1
    stappen_per_graad = totaal_stappen/360
    if (nieuwe_positie_planeet < magneet_positie) and (nieuwe_positie_planeet > 0):
       aantal_stappen_te_lopen = (magneet_positie - nieuwe_positie_planeet) * stappen_per_graad
    else:
       aantal_stappen_te_lopen =  ((360- nieuwe_positie_planeet)+ magneet_positie) * stappen_per_graad 
    
    print ('nieuwe_positie_planeet ' , nieuwe_positie_planeet)
    print ('stappen_per_graad ' , stappen_per_graad)
    print ('magneet_positie ' , magneet_positie)
    print ('aantal_stappen_te_lopen ' , aantal_stappen_te_lopen)      
   
    # drive to position
    teller = 1
    while (teller < aantal_stappen_te_lopen):
       if planeet_motor:
          kit.stepper1.onestep(direction=richting, style= stijl) 
       teller +=1    
    sleep (1)
   
  # wait 10 seconds to prevent overload of webserver
  sleep (10)
  totaalteller +=1
  if planeet_motor:
     kit.stepper1.release() 
      
  positiestring_oud = positiestring
  schakelaar = "open"
  teller = 1
