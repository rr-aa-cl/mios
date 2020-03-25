#!/usr/bin/python3 -u
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from jsonrpc import JSONRPCResponseManager, dispatcher

import argparse
import random
import sys
import time
import webcolors
import numpy as np
import pdb

import config
import setup
from aurora import Aurora

from threading import Thread
import sys
import requests
import json
import time


class LEDServer:
    def __init__(self):
        try:
            self.aurora = config.aurora()
            self.panels = self.aurora.rotated_panel_positions
            self.s = self.aurora.effect_stream()
            self.panels_sorted = None
        except (TypeError):
            exit(-1)

    def init(self,port):
        run_simple('0.0.0.0', port, self.start_server)

    @Request.application
    def start_server(self,request):
        response = JSONRPCResponseManager.handle(request.data, dispatcher)
        return Response(response.json, mimetype='application/json')

    def streaming_color(self, led):
        for l in led:
            print(l)
            r=l['colors'][0]
            g = l['colors'][1]
            b = l['colors'][2]
            print(b)
            if r>255:
                r=255
            if r<1:
                r=1
            if g > 255:
                g = 255
            if g < 1:
                g = 1
            if b > 255:
                b = 255
            if b < 1:
                b = 1
            #print('Set '+str(l['id'])+' to ('+str(r)+','+str(g)+','+str(b)+')')
            self.s.panel_prepare(l['id'],r,g,b,transition_time=l['tt'])
        self.s.panel_strobe()

    @dispatcher.add_method
    def set_led(led_config):
        print(led_config)
        L.streaming_color(led_config)

    @dispatcher.add_method
    def get_panel_id(**kwargs):
        L.panels_sorted=[0]*5
        if len(L.panels) != 5:
            return {'id': [], 'valid': False}

        for p in L.panels:
            dist=np.sqrt(pow(p['x'],2)+pow(p['y'],2))
            if p['x']==-74 and p['y']==43:
                L.panels_sorted[4]=(p['panelId'],dist)
            if p['x']==-74 and p['y']==129:
                L.panels_sorted[0]=(p['panelId'],dist)
            if p['x']==0 and p['y']==173:
                L.panels_sorted[1]=(p['panelId'],dist)
            if p['x']==74 and p['y']==129:
                L.panels_sorted[2]=(p['panelId'],dist)
            if p['x']==74 and p['y']==43:
                L.panels_sorted[3]=(p['panelId'],dist)

        return {'id':L.panels_sorted,'valid':True}

    @dispatcher.add_method
    def panel_test(**kwargs):
        panels = [0]*5
        for p in L.panels:
            dist = np.sqrt(pow(p['x'], 2) + pow(p['y'], 2))
            if p['x'] == -74 and p['y'] == 43:
                panels[4] = (p['panelId'], dist)
            if p['x'] == -74 and p['y'] == 129:
                panels[0] = (p['panelId'], dist)
            if p['x'] == 0 and p['y'] == 173:
                panels[1] = (p['panelId'], dist)
            if p['x'] == 74 and p['y'] == 129:
                panels[2] = (p['panelId'], dist)
            if p['x'] == 74 and p['y'] == 43:
                panels[3] = (p['panelId'], dist)

        for i in range(len(panels)):
            for p in panels:
                L.s.panel_prepare(p[0],0,0,0,transition_time=1)
            L.s.panel_prepare(panels[i][0],0,0,255,transition_time=1)
            L.s.panel_strobe()
            time.sleep(1)

        for p in panels:
            L.s.panel_prepare(p[0], 0, 0, 0, transition_time=1)
        L.s.panel_strobe()

    @dispatcher.add_method
    def set_all_led(red, green, blue):
        for p in L.panels:
            L.s.panel_prepare(p['panelId'], red, green, blue, transition_time=1)
            L.s.panel_strobe()


if __name__ == '__main__':
    L = LEDServer()
    L.init(int(sys.argv[1]))