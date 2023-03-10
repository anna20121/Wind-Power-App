# Import libraries

from bokeh.io import output_notebook, show, curdoc
from bokeh.layouts import column, row, gridplot, layout
from bokeh.models import ColumnDataSource, Slider,CDSView, BoxAnnotation, Select, CustomJS, Label, CheckboxGroup, CustomJS, TeX, Span, CDSView, GroupFilter, LinearAxis, Range1d, Toggle, MultiSelect, MultiChoice, TableColumn, DataTable, Slope, DateRangeSlider, RangeSlider
from bokeh.plotting import figure
from bokeh.palettes import Category10, Category20, Turbo256, Spectral, Inferno256, Inferno, magma, turbo
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.transform import factor_cmap

from pywebio import start_server
from pywebio import *
from pywebio.pin import *
from pywebio.output import *
from pywebio.output import put_row, put_column
from pywebio.session import info as session_info
from pywebio_battery import put_logbox, logbox_append

import pandas as pd
import numpy as np
import os
import os.path
import csv
import io
from datetime import timedelta, datetime, date
import json
import time
from pathlib import Path
import sys
import requests
import xml.etree.ElementTree as et 

pd.options.mode.chained_assignment = None  # default='warn'
cwd = os.getcwd()
no_data='<!DOCTYPE html><html><head><title>error</title></head><body><img src="https://cdn-icons-png.flaticon.com/512/7486/7486759.png" style="width:200px;height:200px;float:right;margin-right:100px;"></body></html>'
error='<!DOCTYPE html><html><head><title>error</title></head><body><img src="https://cdn-icons-png.flaticon.com/512/463/463612.png" style="width:200px;height:200px;float:right;margin-right:100px;"></body></html>'
identifiers={"Wind power generation - hourly data": 75, 
"Wind power generation forecast - updated hourly":245, 
"Wind power production - real time data": 181,
"Electricity consumption in Finland - real time data": 193,
"Electricity production in Finland - real time data": 192,
"Surplus&deficit, cumulative - real time data": 186,
"Electricity consumption forecast - next 24 hours": 165,
"Electricity production prediction - updated hourly":241,
"Total production capacity used in the wind power forecast": 268,
"Wind power generation forecast - updated once a day": 246}

default_start_date= "2022-12-01"
default_end_date= "2022-12-10"
default_docType= "csv"
test = "https://web-api.tp.entsoe.eu/api?securityToken=123ed693-6b67-4a63-a3eb-1c5b58dffc27&documentType=A44&in_Domain=10YFI-1--------U&out_Domain=10YFI-1--------U&periodStart=201512312300&periodEnd=201612312300"

def entsoe_prices():
    try:
        period_end= datetime.now().strftime("%Y%m%d%H")
        period_start=(datetime.now() - timedelta(hours = 1)).strftime("%Y%m%d%H")
        url="https://web-api.tp.entsoe.eu/api?securityToken=123ed693-6b67-4a63-a3eb-1c5b58dffc27&documentType=A44&in_Domain=10YFI-1--------U&out_Domain=10YFI-1--------U&periodStart="+str(period_start)+"00"+"&periodEnd="+str(period_end)+"00"
        data=requests.get(url)
        print("requested from: ", url)
        root = et.fromstring(data.content)
        global price_array
        global timestamp_array
        global dates
        price_array =[]
        timestamp_array=[]
        dates = []
        print(root.tag)
        for child in root.iter("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}price.amount"):
            price_array.append(child.text)
        print(price_array)
        for child in root.iter("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}position"):
            timestamp_array.append(child.text)
        for child in root.iter("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}start"):
            dates.append(child.text)
        for child in root.iter("{urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0}end"):
            dates.append(child.text)
        print(timestamp_array, dates)

    except: put_html(error)

def joke():
    try:
        url = "https://v2.jokeapi.dev/joke/Programming?blacklistFlags=nsfw&type=single"
        data = requests.get(url)
        print("requested from: ", url)
        joke=json.loads(data.text)["joke"]
        print(joke)
        return joke
    except: put_html(error)

def open_weather():
    try:
        url = "https://api.openweathermap.org/data/2.5/weather?q=Valkeakoski&appid=a7fe093c9559910f8902ffe984c409ee"
        data = requests.get(url)
        print("requested from: ", url)
        weather_data=data.json()
        global speed
        speed=weather_data["wind"]["speed"]
        icon=weather_data["weather"][0]["icon"]
        global img_url
        img_url = "https://openweathermap.org/img/wn/"+icon+"@2x.png"
    except: put_html(error)

def dataset_request(start_date, end_date, type, identifier):
    try:
        id=identifiers[identifier]
        #print(identifier)
        start_time= start_date + str("T00%3A00%3A00Z")
        end_time= end_date + str("T00%3A00%3A00Z")
        url=f"https://api.fingrid.fi/v1/variable/{id}/events/{type}?start_time={start_time}&end_time={end_time}"
        data = requests.get(url)
        print("requested from: ", url)
        if type == "csv":
            my_data = pd.DataFrame([x.split(',') for x in data.text.split('\n')[1:]], columns=[x for x in data.text.split('\n')[0].split(',')])
            return(my_data)
        elif type=="json":
            return data.json()
    except: put_html(error)

def get_data():
    try:
        file = dataset_request(pin.start_date3, pin.end_date3, pin.docType, pin.identifier3)
        if pin.docType =="csv":
            exs_loc = Path(f'{cwd}/{pin.identifier3}_{pin.start_date3}_{pin.end_date3}.csv')
            file.to_csv(exs_loc, encoding="utf-8")
            log_box_data=file
        elif pin.docType == "json":
            with open(f'{cwd}/{pin.identifier3}_{pin.start_date3}_{pin.end_date3}.json', 'w') as json_file:
                json.dump({"data":file}, json_file)
            log_box_data="loaded json"
        with use_scope('log_box', clear=True):
            with put_loading():
                time.sleep(2)
                put_logbox("log")
                logbox_append("log", log_box_data)
                time.sleep(2)
    except: put_html(error)


def real_graph(start_date, end_date, docType, identifier):
    try:
        df = dataset_request(start_date, end_date, docType, identifier)
        df["timestamp"]=pd.to_datetime(df["start_time"])
        #print(df)
        p = figure(title = "Title", plot_height=500, plot_width=1100, x_axis_type="datetime")
        p.line(df['timestamp'], df["value"], line_width = 3)
        show(p)
    except: put_html(no_data)

def forecast_graph(start_date, end_date, docType, identifier):
    try:
        df = dataset_request(start_date, end_date, docType, identifier)
        df["timestamp"]=pd.to_datetime(df["start_time"])
        #print(df)
        p = figure(title = "Title", plot_height=500, plot_width=1100, x_axis_type="datetime")
        p.line(df['timestamp'], df["value"], line_width = 3)
        show(p)
    except: put_html(no_data)

def prices():
    try:
        p = figure(title = f"Electricity prices from {dates[0]} to {dates[-1]}", plot_height=500, plot_width=1100)
        p.line(timestamp_array, price_array, line_width = 3)
        show(p)
    except: put_html(no_data)

def analysis_graph(option, timerange):
    try:
        print(option, timerange)
        if timerange == "last day":
            end_date=date.today()
            start_date=end_date- timedelta(days = 1)
        elif timerange== "last week":
            end_date=date.today()
            start_date=end_date- timedelta(days = 7)
        elif timerange== "last month":
            end_date=date.today()
            start_date=end_date- timedelta(days = 30)
        else:
            end_date=date.today()
            start_date=end_date- timedelta(days = 1)

        if option == "Wind power generation":
            forecast_df=dataset_request(str(start_date), str(end_date), "csv", "Wind power generation forecast - updated hourly")
            forecast_df["timestamp"]=pd.to_datetime(forecast_df["start_time"])
            real_df=dataset_request(str(start_date), str(end_date), "csv", "Wind power generation - hourly data")
            real_df["timestamp"]=pd.to_datetime(real_df["start_time"])
        elif option == "Electricity production":
            forecast_df=dataset_request(str(start_date), str(end_date), "csv", "Electricity production prediction - updated hourly")
            forecast_df["timestamp"]=pd.to_datetime(forecast_df["start_time"])
            real_df=dataset_request(str(start_date), str(end_date), "csv", "Electricity production in Finland - real time data")
            real_df["timestamp"]=pd.to_datetime(real_df["start_time"])
        elif option == "Electricity consumption":
            forecast_df=dataset_request(str(start_date), str(end_date), "csv", "Electricity consumption forecast - next 24 hours")
            forecast_df["timestamp"]=pd.to_datetime(forecast_df["start_time"])
            real_df=dataset_request(str(start_date), str(end_date), "csv", "Electricity consumption in Finland - real time data")
            real_df["timestamp"]=pd.to_datetime(real_df["start_time"])

        p = figure(title = "Real and predicted "+option, plot_height=500, plot_width=1100, x_axis_type="datetime")
        p.line(forecast_df['timestamp'], forecast_df["value"], line_width = 3, color="orange", legend_label="predicted")
        p.line(real_df['timestamp'], real_df["value"], line_width = 3,legend_label="real")
        show(p)
    except: put_html(no_data)


    
def upd0():
    with use_scope('real_graph', clear=True):
        with put_loading():
            time.sleep(2)
            real_graph(pin.start_date, pin.end_date, "csv", pin.identifier)
def upd1():
    with use_scope('forecast_graph', clear=True):
        with put_loading():
            time.sleep(2)
            forecast_graph(pin.start_date2, pin.end_date2, "csv", pin.identifier2)

def upd2():
    with use_scope('analysis_graph', clear=True):
        with put_loading():
            time.sleep(2)
            analysis_graph(pin.analysis_option, pin.timerange)

def main():
    session.set_env(title='Windy App',output_max_width='90%')
    output_notebook(verbose=False, notebook_type='pywebio')
    open_weather()
    entsoe_prices()
    put_grid([
        [span(put_markdown('# Windy'), col=10),span(put_markdown("### Electricity price: "+str(price_array[-1])+" MWH")),span(put_markdown("### Wind speed: "+str(speed)+" m/s"), col=1), span(put_image(img_url), col=1)]
    ])
    put_tabs([
        {'title': 'Current data', 'content': put_grid([
            [span(put_markdown('Select settings: '), col=1), None, span(put_select(name='identifier', options=["Wind power generation - hourly data", "Wind power production - real time data", "Electricity consumption in Finland - real time data", "Electricity production in Finland - real time data", "Surplus&deficit, cumulative - real time data"]),col=1),None,span(put_input('start_date', type='date', value=0), col=1),None,span(put_input('end_date', type='date', value=0), col=1),None, span(put_buttons([dict(label='Submit',value='submit',color='dark')], onclick=lambda _:upd0()), col=1)],
            [span(put_scope('real_graph'),col=12)]
        ])},
        {"title": "Forecast", "content": put_grid([
            [span(put_markdown('Select settings: '), col=1), None, span(put_select(name='identifier2', options=["Wind power generation forecast - updated hourly", "Wind power generation forecast - updated once a day","Electricity consumption forecast - next 24 hours","Electricity production prediction - updated hourly","Total production capacity used in the wind power forecast"]),col=1),None,span(put_input('start_date2', type='date', value=0), col=1),None,span(put_input('end_date2', type='date', value=0), col=1),None, span(put_buttons([dict(label='Submit',value='submit',color='dark')], onclick=lambda _:upd1()), col=1)],
            [span(put_scope('forecast_graph'),col=12)]
        ])},
        {"title": "Analysis", "content": put_grid([
            [span(put_select(name="analysis_option", options=["Wind power generation", "Electricity production", "Electricity consumption"]), col=1), None, span(put_select(name="timerange", options=["last day", "last week", "last month"]), col=2),None, span(put_buttons([dict(label='Submit',value='submit',color='dark')], onclick=lambda _:upd2()), col=1)],
            [span(put_scope("analysis_graph"), col=12)],
            [span(put_markdown("### Following graph allows to compare forecasted/predicted data with real data for three valiables in three timerange options"))]
        ])},
        {"title": "Electricity price", "content": put_grid([
            [span(put_scope("prices"), col=12)],
            [span(put_markdown("### Graph displays electricity day ahead prices (24 hours). Data was taking from entsoe API"))]
        ])},
        {"title": "Get Data", "content": put_grid([
            [span(put_markdown('Select settings: '), col=1), None,span(put_select(name="docType", options=["csv", "json"])), None, span(put_select(name='identifier3', options=["Wind power generation - hourly data", "Wind power generation forecast - updated hourly", "Wind power production - real time data", "Electricity consumption in Finland - real time data", "Electricity production in Finland - real time data", "Surplus&deficit, cumulative - real time data"]),col=1),None,span(put_input('start_date3', type='date', value=0), col=1),None,span(put_input('end_date3', type='date', value=0), col=1),None, span(put_buttons([dict(label='Get Data',value='Get Data',color='dark')], lambda _:get_data()), col=1)],
            [span(put_scope("log_box"), col=12)]
        ])},
        {"title": "Daily Joke", "content": put_grid([
            [span(put_markdown(joke()))]
        ])}
    ])



    with use_scope('make_request'):
        with use_scope('real_graph', clear=True):
            real_graph(default_start_date,default_end_date, default_docType, "Wind power generation - hourly data")
        with use_scope("forecast_graph", clear=True):
            forecast_graph(default_start_date,default_end_date, default_docType, "Wind power generation forecast - updated hourly")
        with use_scope("prices", clear=True):
            prices()
        with use_scope("analysis_graph", clear=True):
            analysis_graph("Wind power generation", "last day")
            



if __name__ == '__main__':
    start_server(main, port=8080, debug=True)