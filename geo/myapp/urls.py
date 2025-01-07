
from django.urls import path
from . import views  # Correct import statement

urlpatterns = [
    path('map_view/', views.map_view, name='map_view'),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('conservation_effort/', views.conservation_effort, name='conservation_effort'),
    path('documentation/', views.documentation, name='documentation'),
    path('species/', views.species, name='species'),
    path('newsletter/', views.newsletter, name='newsletter'),
    path('get_occurrences_data/', views.get_occurrences_data, name='get_occurrences_data'),
    path('get_gbif_species_data/', views.get_gbif_species_data, name='get_gbif_species_data'),
    path('get_locations/', views.get_locations, name='get_locations'),
    path('list_geoserver_layers/', views.list_geoserver_layers, name='list_geoserver_layers'),
    path('list_postgis_layers/', views.list_postgis_layers, name='list_postgis_layers'),
    path('get_postgis_layer/', views.get_postgis_layer, name='get_postgis_layer'),
    path('get_postgis_layer_properties/', views.get_postgis_layer_properties, name='get_postgis_layer_properties'),
    path('get_geoserver_layer_properties/', views.get_geoserver_layer_properties, name='get_geoserver_layer_properties'),
    path('spatial_query/', views.spatial_query, name='spatial_query'),
    path('geoserver_ccq/', views.geoserver_ccq, name='geoserver_ccq'),
    path('get_property_values/', views.get_property_values, name='get_property_values'),
]