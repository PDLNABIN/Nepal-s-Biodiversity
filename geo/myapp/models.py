from django.db import models
from shapely.geometry import Point, Polygon
import json

class Location(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def to_point(self):
        return Point(self.longitude, self.latitude)

    def to_geojson(self):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "name": self.name,
                "description": self.description
            }
        }
    

