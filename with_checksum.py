# In simple.py, we wasted too much time on string operations, during which the VLC devices are flickering and the messages are not sent properly.
# In this snippet, we use a checksum to verify the integrity of the message.
# The checksum is calculated using the MD5 algorithm, which is a cryptographic hash function.
# The checksum is appended to the message, separated by a pipe character.
# The receiver calculates the checksum of the message and compares it with the checksum received.
# If the checksums are the same, the message is printed.
# If the checksums are different, a NACK signal is sent to the sender.
# The sender, upon receiving a NACK signal, resends the last message.
# This way, we can guarantee that the final printed message is always correct.
# 
# Note: the checksum is calculated at application level, not at the VLC level.

import serial
import time
import sys
import hashlib

class vlc():
  def __init__(self, port, this_addr, other_addr):
    self.addr = this_addr
    self.other_addr = other_addr
    self.s = serial.Serial(port,115200,timeout=1)
    self.last_msg = ""
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

  def checksum(self, message):
    return hashlib.md5(message.encode()).hexdigest()
    
  def send(self, message):
    self.last_msg = message  # save last message sent, in case it needs to be resent upon receiving a NACK signal
    # TODO: append checksum to last_message to save computation time
    checksum = self.checksum(message)
    data = message + "|" + checksum  # checksum is appended to the message, separated by a pipe character
    self.s.write(str.encode("m[" + data + "\0," + self.other_addr + "]\n"))
    
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
  
  
  def do_receive(self):
    # receives a data message. If the checksum is correct, do nothing.
    # If the checksum is incorrect, send a NACK signal to the sender.
    # Note all of this is explicitly performed at application level, not at the VLC level.
    payload = self.receive()
    if not payload.startswith("m[R"):  # if message read from port is only a response of a sent message (m[P] messages), ignore it
      return
    
    # if message read from port is a received message...
    data = payload.split(",")[-1][:-1]
    if data.startswith("NACK"):  # if data read from port is a NACK signal, resend last message
      print("%s Received a NACK signal, resending last message" %self.addr)
      self.send(self.last_msg)
      return
    
    if data == "A": # if data read from port is an ACK signal, ignore it
      print("%s Received an ACK signal, doing nothing" %self.addr)
      return
    
    # then, message read from port must be a genuine message...
    msg = data.split("|")[0]
    received_checksum = data.split("|")[-1]
    calculated_checksum = self.checksum(msg)
    if received_checksum != calculated_checksum:  # if checksum is incorrect, send a NACK signal to the sender
      print("%s Received a data message with incorrect checksum" %self.addr)
      print("Received checksum: %s" %received_checksum)
      print("Calculated checksum: %s" %calculated_checksum)
      print("Sending NACK signal to %s" %self.other_addr)
      self.s.write(str.encode("m[NACK\0," + self.other_addr + "]\n"))
      return
    
    # if checksum is correct, print the message
    print("%s Received from %s: %s" %(self.addr, self.other_addr, data))
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
      v2.do_receive()
      v2.send(v2_msg)
      v1.do_receive()

      time.sleep(0.1)  # wait for 0.1 second to avoid sending messages too fast
    except KeyboardInterrupt:
      break
    except serial.SerialException:
      continue #on timeout try to read again
    except IndexError:
      continue #on timeout try to read again  

  v1.close()
  v2.close()