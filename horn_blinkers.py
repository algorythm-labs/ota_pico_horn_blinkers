import network
import socket
import utime
import machine
import _thread
from CONFIG import SSID, PASSWORD, PORT, URL, FILE
from ota import OTAUpdater

LED = machine.Pin("LED",machine.Pin.OUT)
Right = machine.Pin(7,machine.Pin.OUT) 
Left = machine.Pin(8,machine.Pin.OUT)

#Setup a PWM Output
Buzzer = machine.PWM(machine.Pin(15)) 
Buzzer.duty_u16(0) #Start with the buzzer off

ota_updater = OTAUpdater(URL, FILE)

def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        utime.sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def open_socket(ip):
    # Open a socket
    address = (ip, PORT)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    print(connection)
    return connection
    
def webpage(state, status):
    #Template HTML
    html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <title>Blinkers & horns</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
            <form action="./lighton">
            <input type="submit" value="Light on" />
            </form>
            <form action="./lightoff">
            <input type="submit" value="Light off" />
            </form>
            <form action="./left">
            <input type="submit" value="Left" />
            </form>
            <form action="./right">
            <input type="submit" value="Right" />
            </form>
            <form action="./horn" method="get">
            <div>
            <label for="Freq">Horn Frequency</label>
            <input id="Freq" type="number" name="Freq" min="1" max="20000" />
            </div>
            <div>
            <input type="submit" value="Horn" />
            </div>
            </form>
            <form action="./allon">
            <input type="submit" value="All on" />
            </form>
            <form action="./alloff">
            <input type="submit" value="All off" />
            </form>
            <br>
            <br>
            <form action="./restart">
            <input type="submit" value="Restart Pico" />
            </form>
            <form action="./check">
            <input type="submit" value="Check for updates" />
            </form>
            <form action="./update">
            <input type="submit" value="Fetch and prepare for upgrade" />
            </form>
            <form action="./list">
            <input type="submit" value="List upgrade" />
            </form>
            <p>LED is {state}</p>
            <p>Status is {status}</p>
            <p>Version: {ota_updater.current_version}</p>           
            </body>
            </html>
            """
    return str(html)

def serve(connection):
    #Start a web server 
    state = "OFF"
    status = ""
    LED.value(1) 
    while True:
        client, addr = connection.accept()
        print("Connection from", addr)
        request = client.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass
        if request == "/lighton?":
            LED.value(1)
            state = "ON"
            status = "Turn on light"
        elif request =="/lightoff?":
            LED.value(0)
            state = "OFF"
            status = "Turn off light"
        elif request =="/left?" or request =="/left":
            #_thread.start_new_thread(left,())
            _thread.start_new_thread(right,())
            state = "OFF"
        elif request =="/right?" or request =="/right":
            #_thread.start_new_thread(right,())
            _thread.start_new_thread(left,())
            state = "OFF"
        elif "/horn" in request:
            Frequency = [1000]
            Frequency[0] = int(request.split("=")[1])
            _thread.start_new_thread(horn,(Frequency))
        elif request =="/alloff?":
            status = "Turning of all"
            LED.value(0)
            Left.value(0)
            Right.value(0)
            Buzzer.duty_u16(0)
            state = "OFF"
        elif request =="/allon?":
            status = "Turning on all"
            LED.value(1)
            Left.value(1)
            Right.value(1)
            state = "ON"
        elif request =="/check?" or request =="/check":            
            status = "Checking for new software"
            newSoftware = ota_updater.check_for_updates()
            print(f'Newer version available: {newSoftware}')            
            print(f'Current version: {ota_updater.current_version}')
            print(f'Latest version: {ota_updater.latest_version}')
            status += "<br>Newer version available: " + str(newSoftware)
            status += "<br>Current version: " + str(ota_updater.current_version)
            status += "<br>Latest version: " + str(ota_updater.latest_version)
        elif request =="/update?" or request =="/update":
            status = "Updating software"
            newSoftware = ota_updater.check_for_updates()
            status += "<br>Newer version available: " + str(newSoftware)
            status += "<br>Current version: " + str(ota_updater.current_version)
            status += "<br>Latest version: " + str(ota_updater.latest_version)
            ota_updater.fetch_latest_code()
            ota_updater.update_no_reset()
        elif request =="/list?" or request == "/list":
            status = "List if update exists"
            status += str(ota_updater.list_software())
            state = "OFF"
        elif request =="/deletetemp?" or request =="/deletetemp":
            status = "Deleting temporary downloads"
            ota_updater.delete_temp()
            ota_updater.current_version = "0"
            state = "OFF"
        elif request =="/restart?" or request =="/restart":
            status = "Restart Pico"
            client.send(status)
            client.close()
            ota_updater.restart()
            
        print(status)

        html = webpage(state, status)
        client.send("HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n")
        client.send(html)
        client.close()

def horn(Frequency=[1000]):
    status = "Horn"
    print("freq: ", Frequency)
    Buzzer.freq(Frequency)
    Buzzer.duty_u16(32767)
    utime.sleep_ms(500)
    Buzzer.duty_u16(0)
    #utime.sleep_ms(900)
    return status
    
def left():
    status = "Left"
    Right.value(0)
    for i in range(4):
        Left.value(1)
        utime.sleep_ms(500)
        Left.value(0)
        utime.sleep_ms(500)
    return status

def right():
    status = "Right"
    Left.value(0)
    for i in range(4):
        Right.value(1)
        utime.sleep_ms(500)
        Right.value(0)
        utime.sleep_ms(500)
    return status

try:
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    machine.reset()