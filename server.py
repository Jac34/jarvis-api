#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import argparse # manage program arguments
import json # read input json
import os # build path
import socket # port in use exception
import sys # exit (1)
import signal # catch kill
import urlparse # parse url parameters
from subprocess import check_output # run sell commands

class Jarvis():
    def __init__(self):
        #self.path = os.path.dirname(os.path.realpath(__file__))
        self.program = [os.path.join (".", "jarvis.sh"), "-j"]
        self.mute_mode = False
        self.verbose = False
    
    def _exec (self, args):
        flags = []
        if self.mute_mode:
            flags.append ("-m")
        if self.verbose:
            flags.append ("-v")
        return check_output(self.program + flags + args)
    
    def get_config (self):
        config={}
        for config_filename in os.listdir  ('config'):
            with open (os.path.join ('config', config_filename)) as config_file:
                config[config_filename]=config_file.read ().rstrip ()
        return config
    
    def set_config (self, config):
        for config_filename in os.listdir  ('config'):
            with open (os.path.join ('config', config_filename), 'w') as config_file:
                value=config[config_filename]
                if isinstance (value, bool):
                    value="true" if value else "false" # to string would give "True"
                config_file.write (value.encode('utf-8')+'\n')
    
    def say (self, phrase):
        return json.loads(self._exec (["-s", phrase]))
    
    def handle_order (self, order):
        return json.loads(self._exec (["-x", order]))
    
    def get_commands (self):
        with open('jarvis-commands') as the_file:
            return { 'commands' : the_file.read() }
    
    def set_commands (sef, commands):
        commands=commands.rstrip()+'\n' # add new line end of file if missing
        with open ('jarvis-commands', 'w') as the_file:
            the_file.write (commands.encode('utf-8'))

def proper_exit (signum, frame):
    print 'Stopping HTTP server'
    http_server.server_close()
    sys.exit(0)

def handle_request (self, data):
    jarvis.mute_mode = ("mute" in data) and (data ["mute"])
    jarvis.verbose = ("verbose" in data) and (data ["verbose"])
    if "action" in data:
        action = data ["action"]
        if action == "get_commands":
            response=jarvis.get_commands ()
        elif action == "set_commands":
            if "commands" in data:
                jarvis.set_commands (data ["commands"])
            else:
                raise ValueError ("Missing commands parameter")
        elif action == "get_config":
            response=jarvis.get_config ()
        elif action == "set_config":
            jarvis.set_config (data ["config"])
        else:
            raise ValueError ("Unsupported action")
    elif "order" in data:
        response=jarvis.handle_order (data ["order"])
    elif "say" in data:
        response=jarvis.say (data ["say"])
    else:
        raise ValueError ("Don't know what to do")
    self.send_response(200)
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Content-type", "application/json")
    self.end_headers()
    self.wfile.write(json.dumps (response))

class RESTRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse.urlparse(self.path)
        data = dict(urlparse.parse_qsl(url.query))
        try:
            handle_request (self, data)
        except Exception as e:
            self.send_response(400)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "application/json")
            self.end_headers()
            print "ERROR:", e
            self.wfile.write(json.dumps ({"error":str(e)}))
            pass
        
    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        response={"error":False}
        try:
            data = json.loads(post_data)
            handle_request (self, data)
        except Exception as e:
            self.send_response(400)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "application/json")
            self.end_headers()
            print "ERROR:", e
            self.wfile.write(json.dumps ({"error":str(e)}))
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Jarvis HTTP RestAPI Server')
    parser.add_argument('-p', '--port', help='Listening port (default: 8080)', type=int, default=8080)
    args = parser.parse_args()
    
    jarvis = Jarvis ()
    server_address = ('', args.port)
    try:
        http_server = HTTPServer(server_address, RESTRequestHandler)
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, proper_exit)
        http_server.serve_forever()
    except socket.error, msg:
        print 'ERROR: ', msg
        sys.exit(1)
    except KeyboardInterrupt:
        print # new line
        pass
