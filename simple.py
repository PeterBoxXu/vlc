import serial
import time
import sys

class vlc():
  def __init__(self, port, this_addr, other_addr):
    self.addr = this_addr
    self.other_addr = other_addr
    self.s = serial.Serial(port,115200,timeout=1)
    self.setup()

  def setup(self):
    time.sleep(2) #give the device some time to startup (2 seconds)
    #write to the device’s serial port
    self.s.write(str.encode("a[" + self.addr + "]\n")) #set the device address
    time.sleep(0.1) #wait for settings to be applied
    self.s.write(str.encode("c[1,0,5]\n")) #set number of retransmissions to 5
    time.sleep(0.1) #wait for settings to be applied
    self.s.write(str.encode("c[0,1,30]\n")) #set FEC threshold to 30 (apply FEC to packets with payload >= 30)
    time.sleep(0.1) #wait for settings to be applied
    
  def send(self, message):
    self.s.write(str.encode("m[" + message + "\0," + self.other_addr + "]\n"))
    
  def receive(self):
    message = "" #reset message
    while True: #while not terminated
      # print("running inside " + self.addr)
      try:
        byte = self.s.read(1) #read one byte (blocks until data available or timeout reached)
        val = chr(byte[0]) 
        if val=='\n': #if termination character reached
          return message
        else:
          message = message + val #concatenate the message
      except serial.SerialException:
        break #on timeout try to read again
      except KeyboardInterrupt:
        sys.exit() #on ctrl-c terminate program 
      except IndexError:
        break
    return message
  
  def print_received_msg(self):
    msg = self.receive()
    if msg.startswith("m[R"):  # if message read from port is a received message, instead of the response of a sent message (m[P] messages)
      print("%s Received from %s: %s" %(self.addr, self.other_addr, msg))
      return
    return
  
  def close(self):
    self.s.close()

if __name__ == "__main__":
  # set up two VLC devices and send messages back and forth,
  # CHANGE THIS when running on your own computer!
  v1 = vlc("/dev/tty.usbmodem142101", "AB", "CD")
  v2 = vlc("/dev/tty.usbmodem142201", "CD", "AB")

  while True:
    v1_msg = "Hello from AB"
    v2_msg = "Hello from CD"
      
    try:  
      v1.send(v1_msg)
      v2.print_received_msg()
      v2.send(v2_msg)
      v1.print_received_msg()
    except KeyboardInterrupt:
      break
    except serial.SerialException:
      continue #on timeout try to read again
    except IndexError:
      continue #on timeout try to read again  

  v1.close()
  v2.close()