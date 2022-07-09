# -*- coding: utf-8 -*-
"""
Created on Sat May 28 19:52:17 2022

@author: Gabriel Lobo
"""
import time
import sys
import os
from netCDF4 import Dataset
from wrf import (getvar, interplevel, ALL_TIMES, ll_to_xy)
import pandas as pd
#%%
def val_at_coord(dataset,_lat,_lon,precision = 0.03):

    return dataset.where(
        (dataset['XLAT'] > (_lat - precision)) & 
        (dataset['XLAT'] < (_lat + precision)) & 
        (dataset['XLONG'] > (_lon - precision)) & 
        (dataset['XLONG'] < (_lon + precision)), drop=True)
def closest(lst, K):
    return min(range(len(lst)), key=lambda i: abs(lst[i]-K))

def get_real_hpa(_date,_df):
    return _df.loc[_date]['Baro;air_pressure;Avg [hPa]']
def clear_last():
    sys.stdout.write("\033[F")

#%%
lat = -12.221720
lon = -42.377980
heights = [80,100,120]

height_dict = {
    80: "Ane4;wind_speed;Avg [m/s]",
    100: "Ane3;wind_speed;Avg [m/s]",
    118: "Ane2;wind_speed;Avg [m/s]",
    120: "Ane1;wind_speed;Avg [m/s]"
}

num_files = 0

df_final = pd.DataFrame({"Real": [], "WRF": []})

#%%
df = pd.read_csv("raw.csv", delimiter="\t", decimal=",")
df.drop(df.columns[len(df.columns)-1], axis=1, inplace=True)


format = '%Y-%m-%d %H:%M:%S'
df['Datetime'] = pd.to_datetime(df['Datetime'], format=format)
df = df.set_index(pd.DatetimeIndex(df['Datetime'])).drop(['Datetime'], axis=1)
df = df.resample('H').mean()
header = list(df)
# df = df[start_date:end_date]

#%%
start = time.time()
print("Getting all files...")
# wrfout_dir = '//wsl.localhost/ubuntu/home/lobo/wrf/RUNS/2021-12-20_2'
wrfout_dir = 'E:/RUNS/20210801_20210807/wrfout'
files = os.listdir(wrfout_dir)
files = list(filter(lambda x: x.startswith("wrfout_d02"), files))
files.sort()

if num_files > 0:
    files = files[:num_files]
    
end = time.time()
clear_last()
print("Getting all files... Done in {:.3f}s".format(end - start))
    
#%%
start = time.time()
print("Building Datasets...")

datasets = [Dataset(os.path.join(wrfout_dir,file)) for file in files]

end = time.time()
clear_last()
print("Building Datasets... Done in {:.3f}s".format(end - start))

start = time.time()
print("Getting windspeed...")

wspd_cat = getvar(datasets, "wspd_wdir", timeidx=ALL_TIMES)[0]

end = time.time()
clear_last()
print("Getting windspeed... Done in {:.3f}s".format(end - start))

start = time.time()
print("Getting height AGL...")

hgt_agl_cat = getvar(datasets, 'height_agl', timeidx=ALL_TIMES)

end = time.time()
clear_last()
print("Getting height AGL... Done in {:.3f}s".format(end - start))


#%% smart loc
x_y = ll_to_xy(datasets[140], lat,lon, as_int=True)
start = time.time()
print("Building DataFrame...")
for wspd in wspd_cat:
    date = pd.to_datetime(wspd.coords['Time'].data).replace(minute=0, second=0, microsecond=0)
    hgt_agl = hgt_agl_cat.loc[date]
    wspd_int = interplevel(wspd, hgt_agl, heights)[0]
    wspd_loc = wspd_int[x_y[1], x_y[0]]
    wspd_data = wspd_loc.item(0)
    
    new_row_data = {'WRF': wspd_data, 'Real': df.loc[date, height_dict[80]]}
    new_row = pd.DataFrame(new_row_data, index=[date])
    
    df_final = pd.concat([df_final, new_row])
end = time.time()
clear_last()
print("Building DataFrame.... Done in {:.3f}s".format(end - start))
#%%

df_final['bias'] = df_final['Real'] - df_final['WRF']
bias = df_final['bias'].mean()
df_final['WRF no BIAS'] = df_final['WRF'] + bias

#%%

ax = df_final[['Real','WRF']].plot(title=f"Wind speed at {heights[0]}m AGL")
ax.set_ylabel("Wind speed [m/s]")


#%%
ax = df_final[['Real','WRF']].rolling(window=3).mean().plot(title=f"Wind speed at {heights[0]}m AGL")
ax.set_ylabel("Wind speed [m/s]")

ax2 = df_final[['Real','WRF no BIAS']].rolling(window=3).mean().plot(title=f"Wind speed at {heights[0]}m AGL")
ax2.set_ylabel("Wind speed [m/s]")

#%%
print('STD: ', df_final[['Real','WRF']].std(ddof=0)[1])
print('RMSE: ', ((df_final['Real'] - df_final['WRF']) ** 2).mean() ** .5 )

print('STD (no bias): ', df_final[['Real','WRF no BIAS']].std(ddof=0)[1])
print('RMSE (no bias): ', ((df_final['Real'] - df_final['WRF no BIAS']) ** 2).mean() ** .5 )
#%%
df_final.to_csv(r'./output/20210801.csv')
