from django.shortcuts import render
from django.http import JsonResponse
from .models import Location
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import requests
import json
import psycopg2
from shapely.geometry import shape, mapping
import pyproj

def map_view(request):
    return render(request, 'myapp/map.html')

def get_locations(request):
    locations = Location.objects.all()
    features = [location.to_geojson() for location in locations]
    return JsonResponse({
        "type": "FeatureCollection",
        "features": features
    })

def list_geoserver_layers(request):
    geoserver_url = 'http://localhost:8080/geoserver/rest/layers'
    auth = ('admin', 'geoserver')  # Replace with your GeoServer username and password

    response = requests.get(geoserver_url, auth=auth, headers={'Accept': 'application/json'})
    if response.status_code == 200:
        layers = response.json()
        return JsonResponse(layers)
    else:
        return JsonResponse({'error': 'Unable to fetch layers from GeoServer'}, status=response.status_code)

def list_postgis_layers(request):
    conn = psycopg2.connect(
        dbname="geoserver",
        user="postgres",
        password="nabin",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cursor.fetchall()
    layers = [table[0] for table in tables]
    cursor.close()
    conn.close()
    return JsonResponse({"layers": layers})

def get_postgis_layer_properties(request):
    layer_name = request.GET.get('layer')
    conn = psycopg2.connect(
        dbname="geoserver",
        user="postgres",
        password="nabin",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{layer_name}'")
    columns = cursor.fetchall()
    properties = [column[0] for column in columns]
    cursor.close()
    conn.close()
    return JsonResponse({"properties": properties})

def get_geoserver_layer_properties(request):
    layer_name = request.GET.get('layer')
    geoserver_url = f'http://localhost:8080/geoserver/rest/layers/{layer_name}'
    auth = ('admin', 'geoserver')  # Replace with your GeoServer username and password

    response = requests.get(geoserver_url, auth=auth, headers={'Accept': 'application/json'})
    if response.status_code == 200:
        layer_info = response.json()
        properties = [attribute['name'] for attribute in layer_info['layer']['attributes']]
        return JsonResponse({"properties": properties})
    else:
        return JsonResponse({'error': 'Unable to fetch layer properties from GeoServer'}, status=response.status_code)

def get_postgis_layer(request):
    layer_name = request.GET.get('layer')
    conn = psycopg2.connect(
        dbname="geoserver",
        user="postgres",
        password="nabin",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT ST_AsGeoJSON(geom) FROM {layer_name}")
    features = cursor.fetchall()
    geojson_features = [{"type": "Feature", "geometry": json.loads(feature[0]), "properties": {}} for feature in features]
    cursor.close()
    conn.close()
    return JsonResponse({"type": "FeatureCollection", "features": geojson_features})


def spatial_query(request):
    layer_name = request.GET.get('layer')
    property_name = request.GET.get('property')
    value = request.GET.get('value')

    conn = psycopg2.connect(
        dbname="geoserver",
        user="postgres",
        password="nabin",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    try:
        query = f"""
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(feature)
        )
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'id', id,
                'geometry', ST_AsGeoJSON(geom)::jsonb,
                'properties', to_jsonb(row) - 'geom'
            ) AS feature
            FROM (
                SELECT *
                FROM {layer_name}
                WHERE {property_name} = %s
            ) row
        ) features;
        """
        
        cursor.execute(query, (value,))
        result = cursor.fetchone()[0]
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    finally:
        cursor.close()
        conn.close()

def geoserver_ccq(request):
    layer_name = request.GET.get('layer')
    property_name = request.GET.get('property')
    value = request.GET.get('value')

    cql_filter = f"{property_name}='{value}'"
    
    geoserver_url = (
        f"http://localhost:8080/geoserver/ows?"
        f"service=WFS&version=1.0.0&request=GetFeature&typeName={layer_name}"
        f"&outputFormat=application/json&CQL_FILTER={cql_filter}"
    )
    
    response = requests.get(geoserver_url)
    if response.status_code == 200:
        return JsonResponse(response.json())
    else:
        return JsonResponse({'error': 'Unable to fetch data from GeoServer'}, status=response.status_code)

def get_property_values(request):
    layer = request.GET.get('layer')
    property_name = request.GET.get('property')
    
    conn = psycopg2.connect(
        dbname="geoserver",
        user="postgres",
        password="nabin",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT {property_name} FROM {layer}")
    values = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    return JsonResponse({"values": values})


def get_occurrences_data(request):
    gbif_url = 'https://api.gbif.org/v1/occurrence/search?country=NP&year=2000,2020&taxon_key=212'
    response = requests.get(gbif_url)
    if response.status_code == 200:
        data = response.json()
        features = []
        for result in data['results']:
            if 'decimalLongitude' in result and 'decimalLatitude' in result:
                point = Point(result['decimalLongitude'], result['decimalLatitude'])

                # Add the original point feature
                point_feature = {
                    "type": "Feature",
                    "geometry": mapping(point),
                    "properties": result
                }
                features.append(point_feature)

        return JsonResponse({"type": "FeatureCollection", "features": features})
    else:
        return JsonResponse({'error': 'Unable to fetch occurrences data from GBIF'}, status=response.status_code)

def get_gbif_species_data(request):
    gbif_url = 'https://api.gbif.org/v1/species/search?datasetKey=0cfa2578-5c4e-49ba-9f4d-ec44f968f71e'
    response = requests.get(gbif_url)
    if response.status_code == 200:
        data = response.json()
        features = []
        for result in data['results']:
            if 'decimalLongitude' in result and 'decimalLatitude' in result:
                point = Point(result['decimalLongitude'], result['decimalLatitude'])

                # Add the original point feature
                point_feature = {
                    "type": "Feature",
                    "geometry": mapping(point),
                    "properties": result
                }
                features.append(point_feature)

        return JsonResponse({"type": "FeatureCollection", "features": features})
    else:
        return JsonResponse({'error': 'Unable to fetch species data from GBIF'}, status=response.status_code)