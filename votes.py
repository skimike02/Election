# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 10:32:32 2020

@author: Micha
"""

import pandas as pd
import jinja2
import json
from bokeh.plotting import figure, save, output_file
from bokeh.models import GeoJSONDataSource
import geopandas as gpd
import os
import config

fileloc=config.fileloc

shapefile='Precincts/Consolidated_Precincts_2020_11_GENERAL.shp'
gdf = gpd.read_file(shapefile)[['VPrecinct','geometry','SHAPE_Area']]
dir_path = os.path.dirname(os.path.abspath(__file__))

df=pd.read_excel('PRES_Results_Precinct.xlsx')
df.drop(df[df.Precinct=='TOTALS'].index,inplace=True)
df.Precinct=df.Precinct.astype('int64')
candidates=df.columns.to_list()
candidates.remove('Precinct')
df['votes_cast']=df.apply(lambda x: x[candidates].sum(), axis=1)
df['pctBiden']=df['JOSEPH R. BIDEN']/df['votes_cast']
df['pctTrump']=df['DONALD J. TRUMP']/df['votes_cast']
df['pctOther']=(df['votes_cast']-df['JOSEPH R. BIDEN']-df['DONALD J. TRUMP'])/df['votes_cast']
df.fillna(0,inplace=True)
df['color']=df.apply(lambda x: '#%02x%02x%02x' % ((x['pctTrump']*255).astype('int'), 0, (x['pctBiden']*255).astype('int')),axis=1)

merged = gdf.merge(df, left_on = 'VPrecinct', right_on = 'Precinct', how = 'inner')
merged['voter_density']=merged['votes_cast']/merged['SHAPE_Area']
merged['votershade']=(merged['voter_density']/merged['voter_density'].max())*.95+.05

def get_geodatasource(gdf):    
    json_data = json.dumps(json.loads(gdf.to_json()))
    return GeoJSONDataSource(geojson = json_data)

def plot_map():
    source=get_geodatasource(merged)
    tools = 'wheel_zoom,pan,reset'
    p = figure(
        title='Sacramento County Presidential Votes - Color by party, shading by voter density', tools=tools, plot_width=800,plot_height=800,
        x_axis_location=None, y_axis_location=None,
        tooltips=[("Precinct", "@Precinct"),
                  ("Percent Trump", "@pctTrump{0.0%}"),
                  ("Percent Biden","@pctBiden{0.0%}"),
                  ("Percent Other","@pctOther{0.0%}"),
                  ("Votes Cast","@votes_cast{0,}")                 
                  ],
        sizing_mode='scale_height',
        )
    
    p.grid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"
    p.patches(xs='xs', ys='ys', source=source,
              fill_color='color',
              fill_alpha='votershade',
              line_color="grey", line_width=0.1)
    return(p)

p=plot_map()

output_file(fileloc+'Election.html')
templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = os.path.join(dir_path,"home.html")
with open(TEMPLATE_FILE) as file_:
    template=jinja2.Template(file_.read())
save(p,title='Election',template=template)

#results from https://results.saccounty.net/resultsSW.aspx?type=PRES&map=MPRC&shape=Nov2020
#Precincts from https://data.saccounty.net/datasets/255dd4348bd045cea5c7c4ea949a5b4a_0

#https://opendata.arcgis.com/datasets/255dd4348bd045cea5c7c4ea949a5b4a_0.zip?outSR=%7B%22latestWkid%22%3A2226%2C%22wkid%22%3A102642%7D