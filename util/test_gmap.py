#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from pygmap_ext import maps
import webbrowser

mymap = maps(1.29425, 103.8991, 8)
mymap.addpoint(1.29425, 103.8991, color='#FF0000', title='test')
mymap.draw('mymap.draw.html')
url = 'mymap.draw.html'
webbrowser.open_new_tab(url)
