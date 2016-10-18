import math
import geojson


class GeoJSON():
    def __init__(self, v):
        self.data = v.data
        self.refX, self.refY = self.getMapReference()
        self.startX, self.startY = self.getStartReference()
        self.refLat, self.refLng = self.getRefLat()
        self.geojson = self.createGeoJSON()

    def getMapReference(self):
        """ Retrieve reference map coordinates from Vissim parameters
            Input: None
            Output: x, y coordinates
        """
        x = float(self.data.xpath('./netPara/refPointMap')[0].attrib['x'])
        y = float(self.data.xpath('./netPara/refPointMap')[0].attrib['y'])
        return x, y

    def getStartReference(self):
        """ Retrieve reference start coordinates from Vissim parameters
            Input: None
            Output: x, y coordinates
        """
        x = float(self.data.xpath('./netPara/refPointNet')[0].attrib['x'])
        y = float(self.data.xpath('./netPara/refPointNet')[0].attrib['y'])
        return x, y

    def metersToLatLng(self, x, y):
        """ Convert xy points to latlng.
            Input: x, y
            Output: WGS84 lat/lng
        """
        extent = 20015085  # height/width in meters of the VISSIM map
        lng = x * 180 / float(extent)
        y = y * 180 / float(extent)
        lat = math.atan(math.exp(y*(math.pi/180.0))) * (360 / math.pi) - 90
        return lat, lng

    def getRefLat(self):
        refLat, refLng = self.metersToLatLng(self.refX, self.refY)
        return refLat, refLng

    def scaledMetersToNode(self, xy):
        """ Remove Mercator scaling factor and reference point.
            Input: scaled xy
            Output: latlng node
        """
        scaleX, scaleY = xy
        scaleX, scaleY = float(scaleX), float(scaleY)
        scale = 1 / math.cos(math.radians(self.refLat))
        x = (scaleX * scale) + self.refX - self.startX
        y = (scaleY * scale) + self.refY - self.startY
        lat, lng = self.metersToLatLng(x, y)
        return lat, lng

    def createGeoJSON(self):
        """ Get list of link geometries and properties to be converted.
            Input: Vissim object
            Output: list of links
        """
        features = []
        for link in self.data.xpath('./links/link'):
            geos = []
            linkNum = link.attrib['no']
            for geo in link.xpath('./geometry/points3D/point3D'):
                x, y = geo.attrib['x'], geo.attrib['y']
                latLng = self.scaledMetersToNode((x, y))
                geos.append(latLng)
            laneNum = str(len(link.xpath('./lanes/lane')))
            multiLine = geojson.MultiLineString(coordinates=geos)
            features.append(geojson.Feature(id=linkNum, geometry=multiLine,
                                            properties={'lane': laneNum}))
        return geojson.FeatureCollection(features)

    def export(self, filename):
        """ Export GeoJSON object to file
            Input: filename
            Output: written file
        """
        f = open(filename, 'w')
        f.writelines(geojson.dumps(self.geojson))
        f.close()
