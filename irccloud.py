import requests, json, websocket, urllib

LOGIN_EMAIL = ''
LOGIN_PASS  = ''

# The websocket library incorrectly presumes the origin to be
# from plain HTTP site. This monkey patch assumes HTTPS.
original_handshake = websocket.WebSocket._handshake
def https_origin_handshake(self, host, port, resource, **options):
    if not 'origin' in options:
        if port == 80:
            hostport = host
        else:
            hostport = "%s:%d" % (host, port)
        options['origin'] = 'https://%s' % hostport
    original_handshake(self, host, port, resource, **options)
websocket.WebSocket._handshake = https_origin_handshake

session=None

def on_open(ws):
    print ' open'

def on_message(ws, message):
    print '  msg: %s' % message

    msg = json.loads(message)
    if msg['type'] == 'stat_user':
        last_buffer = msg['last_selected_bid']
        hb_msg = dict(
            selected_buffer = last_buffer,
            _reqid = "1",
            _method = "heartbeat"
        )
        print 'sending %s' % json.dumps(hb_msg)
        ws.send(json.dumps(hb_msg))

    if msg['type'] == 'oob_include':
        url = msg['url']
        resp = requests.get(
            'https://www.irccloud.com%s' % url,
            cookies=dict(session = session)
        )
        resp.text

def on_error(ws, error):
    print 'error: %s' % error

def on_close(ws):
    print 'close'

def start():
    global session
    resp = requests.post('https://www.irccloud.com/chat/auth-formtoken', '_reqid=1')
    authdata = json.loads(resp.text)
    token = authdata['token']

    logindata = dict(
        email = LOGIN_EMAIL,
        password = LOGIN_PASS,
        token = token,
        org_invite='',
        _reqid = '2'
    )

    postdata = urllib.urlencode(logindata)
    resp = requests.post('https://www.irccloud.com/chat/login', postdata,
        headers={'x-auth-formtoken': token}
    )
    logindata = json.loads(resp.text)
    if not logindata['success']:
        print 'Could not login'
        exit()

    session = logindata['session']

    ws = websocket.WebSocketApp(
        'wss://www.irccloud.com/',
        on_message = on_message,
        on_error = on_error,
        on_close = on_close,
        on_open = on_open,
        cookie='session=%s' % session,
    )
    ws.run_forever()

if __name__ == '__main__':
    start()
