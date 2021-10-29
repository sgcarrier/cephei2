from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib
from platforms.CHARTIER.CHARTIER import CHARTIER
from functions.helper_functions import *
import json
import threading

import logging

_logger = logging.getLogger(__name__)

class CHARTIERHandler(BaseHTTPRequestHandler):

    board = None

    def do_POST(self):
        if self.board:
            parsed_path = urllib.parse.urlsplit(self.path)
            query = urllib.parse.parse_qs(parsed_path.query)
            print(query)

            paths = (self.path).split('?')[0]
            paths = paths.split('/')

            if paths[1] == "CHARTIER":
                cmd = self.board.b
            else:
                cmd = self.board
            paths = filter(None, paths[2:])
            for path in paths:
                cmd = getattr(cmd, path)

            args = query['args']
            for i in range(len(args)):
                args[i] = self.autoconvert(args[i])

            r = cmd(*args)

            if (r == -1):
                self.send_response(400)
            else:
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                json_str = json.dumps({'returnValue': str(r)})
                self.wfile.write(json_str.encode(encoding='utf_8'))

    def do_GET(self):
        if self.board:
            parsed_path = urllib.parse.urlsplit(self.path)
            query = urllib.parse.parse_qs(parsed_path.query)
            print(query)

            paths = (self.path).split('?')[0]
            paths = paths.split('/')
            if paths[1] == "CHARTIER":
                cmd = self.board.b
            else:
                cmd = self.board
            paths = filter(None, paths[2:])
            for path in paths:
                cmd = getattr(cmd, path)

            args = query['args']
            for i in range(len(args)):
                args[i] = self.autoconvert(args[i])

            r = cmd(*args)

            if (r == -1):
                self.send_response(400)
            else:
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                json_str = json.dumps({'returnValue': str(r)})
                self.wfile.write(json_str.encode(encoding='utf_8'))

    def boolify(self, s):
        if s == 'True':
            return True
        if s == 'False':
            return False
        raise ValueError("Not a bool")

    def autoconvert(self, s):
        for fn in (self.boolify, int, float, str):
            try:
                return fn(s)
            except ValueError:
                pass
        return s


if __name__ == '__main__':
    from http.server import HTTPServer
    handler = CHARTIERHandler
    handler.board = Board()
    server = HTTPServer(('192.168.0.200', 5000), handler)
    print('Starting server at http://192.168.0.200:5000')

    handler.board.trigger_oscillator.set_frequency(20)  # div by 2 later
    handler.board.trigger_divider.set_divider(510, Divider.MUX_NOT_CORR)                  
    handler.board.mux_trigger_laser.select_input(MUX.DIVIDER_INPUT)                                               
    handler.board.mux_trigger_external.select_input(MUX.PCB_INPUT)      
    handler.board.trigger_delay_head_0.set_delay_code(0)                
    handler.board.b.ICYSHSR1.gpio_set(0,"REINIT", False)                                                
    time.sleep(1)                
    handler.board.b.ICYSHSR1.gpio_set(0,"REINIT",True)                                              	  
    time.sleep(1) 

    handler.board.asic_head_0.set_trigger_type(1)
    handler.board.b.ICYSHSR1.TRIGGER_EVENT_DRIVEN_COLUMN_THRESHOLD(0, 1, 0)


    '''Set RECHARCHE current '''
    CE_T_RCH = 2 #uA
    '''Set HOLDOFF current'''
    CE_T_HOLDOFF = 2 #uA
    '''Set comparator threshold'''
    CE_V_COMP = 3 #V
    #handler.board.recharge_current.set_current(CE_T_RCH)
    #handler.board.holdoff_current.set_current(CE_T_HOLDOFF)
    #handler.board.comparator_threshold.set_voltage((CE_V_COMP/3.3) * 5)

    #handler.board.b.DMA.set_meta_data("test", "test", 0, 0)
    head_0 = threading.Thread(target=handler.board.b.DMA.start_data_acquisition, args=(0,0,-1,-1,-1))

    try:
        head_0.start()
        server.serve_forever()
    except KeyboardInterrupt:
        handler.board.b.DMA.stop_data_acquisition()
        _logger.info("Stopping live feed")
        exit()



