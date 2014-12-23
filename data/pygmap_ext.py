import math
###########################################################
##   This program is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation, either version 3 of the License, or
##   (at your option) any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###########################################################
###########################################################

###########################################################
## extension of pygmaps listed at http://code.google.com/p/pygmaps
##
## google maps javascript api v3 wrapper
##
##
############################################################

class maps:

    def __init__(self, centerLat, centerLng, zoom ):
        self.center = (float(centerLat),float(centerLng))
        self.zoom = int(zoom)
        self.grids = None
        self.paths = []
        self.points = []
        self.radpoints = []
        self.gridsetting = None
        self.coloricon = 'http://chart.apis.google.com/chart?cht=mm&chs=12x16&chco=FFFFFF,XXXXXX,000000&ext=.png'

        #my implementation
        self.options={}
        self.content=""
        self.maptypeid="ROADMAP"



    def setgrids(self,slat,elat,latin,slng,elng,lngin):
        self.gridsetting = [slat,elat,latin,slng,elng,lngin]

    def addpoint(self, lat, lng, title = "no implementation", color = '#FF0000',):
        self.points.append((lat,lng,color[1:],title))

    #def addpointcoord(self, coord):
    #   self.points.append((coord[0],coord[1]))

    def addradpoint(self, lat,lng,rad,color = '#0000FF'):
        self.radpoints.append((lat,lng,rad,color))

    def addpath(self,path,color = '#FF0000'):
        path.append(color)
        self.paths.append(path)

    #create the html file which inlcude one google map and all points and paths
    def draw(self, htmlfile):
        f = open(htmlfile,'w')
        f.write('<html>\n')
        f.write('<head>\n')
        f.write('<meta name="viewport" content="initial-scale=1.0, user-scalable=no" />\n')
        f.write('<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>\n')
        f.write('<title>Google Maps - pygmaps </title>\n')
        f.write('<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>\n')
        f.write('<script type="text/javascript">\n')
        f.write('\tfunction initialize() {\n')
        self.drawmap()
        self.drawgrids()
        self.drawpoints()
        self.drawradpoints()
        self.drawpaths(self.paths)
        f.write(self.content)
        f.write('\t}\n')
        f.write('</script>\n')
        f.write('</head>\n')
        f.write('<body style="margin:0px; padding:0px;" onload="initialize()">\n')
        f.write('\t<div id="map_canvas" style="width: 100%; height: 100%;"></div>\n')
        f.write('</body>\n')
        f.write('</html>\n')
        f.close()

    def drawgrids(self):
        if self.gridsetting == None:
            return
        slat = self.gridsetting[0]
        elat = self.gridsetting[1]
        latin = self.gridsetting[2]
        slng = self.gridsetting[3]
        elng = self.gridsetting[4]
        lngin = self.gridsetting[5]
        self.grids = []

        r = [slat+float(x)*latin for x in range(0, int((elat-slat)/latin))]
        for lat in r:
            self.grids.append([(lat+latin/2.0,slng+lngin/2.0),(lat+latin/2.0,elng+lngin/2.0)])

        r = [slng+float(x)*lngin for x in range(0, int((elng-slng)/lngin))]
        for lng in r:
            self.grids.append([(slat+latin/2.0,lng+lngin/2.0),(elat+latin/2.0,lng+lngin/2.0)])

        for line in self.grids:
            self.drawPolyline(line,strokeColor = "#000000")
    def drawpoints(self):
        for point in  self.points:
            self.drawpoint(point[0],point[1],point[2],point[3])

    def drawradpoints(self):
        for rpoint in self.radpoints:
            path = self.getcycle(rpoint[0:3])
            self.drawPolygon(path,strokeColor = rpoint[3])

    def getcycle(self,rpoint):
        cycle = []
        lat = rpoint[0]
        lng = rpoint[1]
        rad = rpoint[2] #unit: meter
        d = (rad/1000.0)/6378.8;
        lat1 = (math.pi/180.0)* lat
        lng1 = (math.pi/180.0)* lng

        r = [x*30 for x in range(12)]
        for a in r:
            tc = (math.pi/180.0)*a;
            y = math.asin(math.sin(lat1)*math.cos(d)+math.cos(lat1)*math.sin(d)*math.cos(tc))
            dlng = math.atan2(math.sin(tc)*math.sin(d)*math.cos(lat1),math.cos(d)-math.sin(lat1)*math.sin(y))
            x = ((lng1-dlng+math.pi) % (2.0*math.pi)) - math.pi
            cycle.append( ( float(y*(180.0/math.pi)),float(x*(180.0/math.pi)) ) )
        return cycle

    def drawpaths(self, paths):
        for path in paths:
            #print path
            self.drawPolyline(path[:-1], strokeColor = path[-1])

    #############################################
    # # # # # # Low level Map Drawing # # # # # #
    #############################################
    def drawmap(self):
        self.content +=('\t\tvar centerlatlng = new google.maps.LatLng(%f, %f);\n' % (self.center[0],self.center[1]))
        self.content +=('\t\tvar myOptions = {\n')
        self.content +=('\t\t\tzoom: %d,\n' % (self.zoom))
        #add my options
        if self.options:
            for  x in self.options:
                self.content +=('\t\t\t'+str(x)+': '+str(self.options[x])+',\n')

        #add my options
        self.content +=('\t\t\tcenter: centerlatlng,\n')
        self.content +=('\t\t\tmapTypeId: google.maps.MapTypeId.'+str(self.maptypeid)+'\n')
        self.content +=('\t\t};\n')
        self.content +=('\t\tvar map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);\n')
        self.content +=('\n')



    def drawpoint(self,lat,lon,color,title):
        self.content +=('\t\tvar latlng = new google.maps.LatLng(%f, %f);\n'%(lat,lon))
        self.content +=('\t\tvar img = new google.maps.MarkerImage(\'%s\');\n' % (self.coloricon.replace('XXXXXX',color)))
        self.content +=('\t\tvar marker = new google.maps.Marker({\n')
        self.content +=('\t\ttitle: "'+str(title)+'",\n')
        self.content +=('\t\ticon: img,\n')
        self.content +=('\t\tposition: latlng\n')
        self.content +=('\t\t});\n')
        self.content +=('\t\tmarker.setMap(map);\n')
        self.content +=('\n')

    def drawPolyline(self,path,\
            clickable = False, \
            geodesic = True,\
            strokeColor = "#FF0000",\
            strokeOpacity = 1.0,\
            strokeWeight = 2
            ):
        self.content +=('var PolylineCoordinates = [\n')
        for coordinate in path:
            self.content +=('new google.maps.LatLng(%f, %f),\n' % (coordinate[0],coordinate[1]))
            self.content +=('];\n')
            self.content +=('\n')

            self.content +=('var Path = new google.maps.Polyline({\n')
            self.content +=('clickable: %s,\n' % (str(clickable).lower()))
            self.content +=('geodesic: %s,\n' % (str(geodesic).lower()))
            self.content +=('path: PolylineCoordinates,\n')
            self.content +=('strokeColor: "%s",\n' %(strokeColor))
            self.content +=('strokeOpacity: %f,\n' % (strokeOpacity))
            self.content +=('strokeWeight: %d\n' % (strokeWeight))
            self.content +=('});\n')
            self.content +=('\n')
            self.content +=('Path.setMap(map);\n')
            self.content +=('\n\n')

    def drawPolygon(self,path,\
            clickable = False, \
            geodesic = True,\
            fillColor = "#000000",\
            fillOpacity = 0.0,\
            strokeColor = "#FF0000",\
            strokeOpacity = 1.0,\
            strokeWeight = 1
            ):
        self.content +=('var coords = [\n')
        for coordinate in path:
            self.content +=('new google.maps.LatLng(%f, %f),\n' % (coordinate[0],coordinate[1]))
        self.content +=('];\n')
        self.content +=('\n')

        self.content +=('var polygon = new google.maps.Polygon({\n')
        self.content +=('clickable: %s,\n' % (str(clickable).lower()))
        self.content +=('geodesic: %s,\n' % (str(geodesic).lower()))
        self.content +=('fillColor: "%s",\n' %(fillColor))
        self.content +=('fillOpacity: %f,\n' % (fillOpacity))
        self.content +=('paths: coords,\n')
        self.content +=('strokeColor: "%s",\n' %(strokeColor))
        self.content +=('strokeOpacity: %f,\n' % (strokeOpacity))
        self.content +=('strokeWeight: %d\n' % (strokeWeight))
        self.content +=('});\n')
        self.content +=('\n')
        self.content +=('polygon.setMap(map);\n')
        self.content +=('\n\n')

        #zee implementations
    def drawblock(self,style):
        data=''
        data +=('<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>\n')
        data +=('<script type="text/javascript">\n')
        data +=('\tfunction initialize() {\n')
        self.drawmap()
        self.drawgrids()
        self.drawpoints()
        self.drawradpoints()
        self.drawpaths(self.paths)
        data +=(self.content)
        data +=('\t}\n')
        data +=('</script>\n')
        data +=('<script type="text/javascript">\n')
        data +=('window.onload=function(){initialize();}\n')
        data +=('</script>\n')
        #f.write('<body style="margin:0px; padding:0px;" >\n')
        data +=('\t<div id="map_canvas" style="'+str(style)+'" ></div>\n')
        #f.write('</body>\n')
        return data



    #method to set basic options
    def setbasicoption(self,options):
            datatype=self.option_structure()
            result={}
            for x in options:
                if type(options[x]) is datatype[x]:
                    result[x]=options[x]

            self.options=self.bool_type_convertion(result)
    #method to set map type
    def setmaptypeid(self,type):
            self.maptypeid=type

    def bool_type_convertion(self,options):
                for x in options:
                    if type(options[x]) is bool:
                        if options[x]:
                            options[x] = "true"
                        else:
                            options[x] = "false"
                return options
    def option_structure(self):
        return {'backgroundColor' : str,
                'disableDefaultUI' : bool,
                'disableDoubleClickZoom' : bool,
                'draggable' : bool,
                'draggableCursor': str,
                'draggingCursor' : str,
                'heading' : int,
                'keyboardShortcuts' : bool,
                'mapMaker' : bool,
                'mapTypeControl' : bool,
                'maxZoom' : int,
                'minZoom' : int,
                'noClear' : bool,
                'overviewMapControl': bool,
                'panControl': bool,
                'rotateControl' : bool,
                'scaleControl' : bool,
                'scrollwheel': bool,
                'streetViewControl' : bool,
                'tilt' : int,
                'zoom': int,
                'zoomControl':bool
                }
