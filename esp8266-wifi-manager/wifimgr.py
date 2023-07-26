import network
import socket
import ure
import time

ap_ssid = "GrayrockLabs_BreezyConnect"
ap_password = "looknorth"
ap_authmode = 3  # WPA2

NETWORK_PROFILES = 'wifi2.dat'
print(network.AP_IF)
print(network.STA_IF)
wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

server_socket = None


def force_disconnection():
    """deconnect from an existing wlan_sta to forget existing network"""
    print("DEBUG", "Disconnecting STA...")
    time.sleep(2)
    wlan_sta.disconnect()


def get_connection():
    """return a working WLAN(STA_IF) instance or None"""

    # First check if there already is any connection:
    if wlan_sta.isconnected():
        print("DEBUG", "Found existing STA connection. STA:", wlan_sta)
        return wlan_sta

    connected = False
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if wlan_sta.isconnected():
            return wlan_sta

        # Read known network profiles from file
        profiles = read_profiles()

        # Search WiFis in range
        wlan_sta.active(True)
        networks = wlan_sta.scan()

        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            encrypted = authmode > 0
            print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = do_connect(ssid, password)
                else:
                    print("skipping unknown encrypted network")
            else:  # open
                connected = do_connect(ssid, None)
            if connected:
                break

    except OSError as e:
        print("exception", str(e))

    # start web server for connection manager:
    if not connected:
        connected = start()

    return wlan_sta if connected else None


def read_profiles():
    with open(NETWORK_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")
        profiles[ssid] = password
    return profiles


def write_profiles(profiles):
    lines = []
    for ssid, password in profiles.items():
        lines.append("%s;%s\n" % (ssid, password))
    with open(NETWORK_PROFILES, "w") as f:
        f.write(''.join(lines))


def do_connect(ssid, password):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        return None
    print('Trying to connect to %s...' % ssid)
    wlan_sta.connect(ssid, password)
    for retry in range(200):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print('\nConnected. Network config: ', wlan_sta.ifconfig())
        
    else:
        print('\nFailed. Not Connected to: ' + ssid)
    return connected


def send_header(client, status_code=200, content_length=None ):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
      client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()


html_top = """\
<html>
  <head>
    <link rel="stylesheet" href="./connect.css" />
    <style>
      html {
        font-family: Arial, sans-serif;
        background-color: #222222;
      }
      body {
        color: rgb(230, 230, 230);
      }
      .ssid-list {
        width: 70%;
        margin-left: auto;
        margin-right: auto;
      }
      .ssid-list div {
        background-color: #303030;
      }
      .ssid-div {
        width: 30%;
        min-width: 300px;
        margin-left: auto;
        margin-right: auto;
      }
      .w3-tooltip,.w3-display-container{position:relative}.w3-tooltip .w3-text{display:none}.w3-tooltip:hover .w3-text{display:inline-block}
      .w3-container:after,.w3-container:before,.w3-panel:after,.w3-panel:before,.w3-row:after,.w3-row:before,.w3-row-padding:after,.w3-row-padding:before,
      .w3-display-container:hover .w3-display-hover{display:block}.w3-display-container:hover span.w3-display-hover{display:inline-block}.w3-display-hover{display:none}
      .w3-container,.w3-panel{padding:0.01em 16px}.w3-panel{margin-top:16px;margin-bottom:16px}
      .w3-blue,.w3-hover-blue:hover{color:#fff!important;background-color:#2196F3!important}
      h1{font-size:36px}h2{font-size:30px}h3{font-size:24px}h4{font-size:20px}h5{font-size:18px}h6{font-size:16px}
      h1,h2,h3,h4,h5,h6{font-family:"Segoe UI",Arial,sans-serif;font-weight:400;margin:10px 0}.w3-wide{letter-spacing:4px}
      html{box-sizing:border-box}*,*:before,*:after{box-sizing:inherit}
      button,input,select,textarea,optgroup{font:inherit;margin:0}optgroup{font-weight:bold}
      button,input{overflow:visible}button,select{text-transform:none}
      button,[type=button],[type=reset],[type=submit]{-webkit-appearance:button}
      .w3-card-4,.w3-hover-shadow:hover{box-shadow:0 4px 10px 0 rgba(0,0,0,0.2),0 4px 20px 0 rgba(0,0,0,0.19)}
      [type=checkbox],[type=radio]{padding:0}
      .w3-check,.w3-radio{width:24px;height:24px;position:relative;top:6px}

    </style>
  </head>
  <body>
    <div class="w3-container w3-blue">
      <h1>Breezy Wi-Fi Setup</h1>
    </div>
    <form action="configure" method="post">
      <div class="ssid-div">
        <br />
        <h2>
          <span style="color: #fff"> Choose your network </span>
        </h2>
        <ul class="w3-ul w3-card-4">
"""

html_list_item = """\
          <li>
            <input type="radio" name="ssid" value="{0}" id="option-{0}" class="w3-radio" />
            <label for="option-{0}">{0}</label>
          </li>
"""

html_bottom = """\
        </ul>
        <br />
        <div>
          <label>Password</label>
          <input class="w3-input" name="password" type="password" />
        </div>
        <p style="text-align: center">
          <input type="submit" value="Submit" class="w3-button w3-round w3-blue w3-block" />
        </p>
      </div>
    </form>
  </body>
</html>
"""

def handle_root(client):
    wlan_sta.active(True)
    ssids = sorted(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan())
    print("GOT SSIDs", ssids)
    send_header(client)
    
    # send HTML
    client.sendall(html_top)
    while len(ssids):
        ssid = ssids.pop(0)
        client.sendall(html_list_item.format(ssid))
    client.sendall(html_bottom)
    
    client.close()


def handle_configure(client, request):
    print("TRACE", "Handle configure. CLIENT:", client, "REQUEST:", request)
    match = ure.search("ssid=([^&]*)&password=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")

    if len(ssid) == 0:
        send_response(client, "SSID must be provided", status_code=400)
        return False

    if do_connect(ssid, password):
        response = """\
            <html>
                <center>
                    <br><br>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP successfully connected to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        time.sleep(1)
        wlan_ap.active(False)
        try:
            profiles = read_profiles()
        except OSError:
            profiles = {}
        profiles[ssid] = password
        write_profiles(profiles)

        time.sleep(5)

        return True
    else:
        response = """\
            <html>
                <center>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP could not connect to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                    <form>
                        <input type="button" value="Go back!" onclick="history.back()"></input>
                    </form>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        return False


def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


def stop():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None


def start(port=80):
    global server_socket

    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

    stop()

    wlan_sta.active(True)
    wlan_ap.active(True)

    wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)

    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)

    print('Connect to WiFi ssid ' + ap_ssid + ', default password: ' + ap_password)
    print('and access the ESP via your favorite web browser at 192.168.4.1.')
    print('Listening on:', addr)

    while True:
        if wlan_sta.isconnected():
            wlan_ap.active(False)
            print("DEBUG", "Active STA connection detected")
            return True

        client, addr = server_socket.accept()
        print('client connected from', addr)
        try:
            client.settimeout(5.0)

            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)
            except OSError:
                pass

            # Handle form data from Safari on macOS and iOS; it sends \r\n\r\nssid=<ssid>&password=<password>
            try:
                request += client.recv(1024)
                print("Received form data after \\r\\n\\r\\n(i.e. from Safari on macOS or iOS)")
            except OSError:
                pass

            print("Request is: {}".format(request))
            if "HTTP" not in request:  # skip invalid requests
                continue

            # version 1.9 compatibility
            try:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).decode("utf-8").rstrip("/")
            except Exception:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
            print("URL is {}".format(url))

            if url == "":
                handle_root(client)
            elif url == "configure":
                handle_configure(client, request)
            else:
                handle_not_found(client, url)

        finally:
            client.close()
