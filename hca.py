# -*- coding: utf-8 -*-
"""
Created on Sat Oct  22 20:54:02 2022

@author: wwang2
"""

import pandas as pd
import random
import os
from pathlib import Path

import matplotlib.pyplot as plt

import numpy as np


import opendssdirect as dss
from opendssdirect.utils import run_command

## read partition regions of the feeder

PATH = Path(os.getcwd())



r0 = pd.read_csv(PATH/'partition'/'low_income_0.csv')
r1 = pd.read_csv(PATH/'partition'/'low_income_1.csv')
r2 = pd.read_csv(PATH/'partition'/'low_income_2.csv')


load_r0 = set(r0[r0['type']=='Load']['name'])
load_r1 = set(r1[r1['type']=='Load']['name'])
load_r2 = set(r2[r2['type']=='Load']['name'])

load_region = [load_r0, load_r1, load_r2]

fname = PATH/'p30uhs8_1247--p30udt9870'/'Master.dss'

run_command('compile '+fname)
dss.Vsources.PU(1.0)
run_command('solve')

if dss.Text.Result() == '':
    print('----- Success for the test run ----')
else:
    print('---- Opendss failed ------')
    print(dss.Text.Result())
summary = dss.run_command('summary')
print(summary)


v = dss.Circuit.AllBusMagPu()
vname = dss.Circuit.AllNodeNames()

df_v = pd.DataFrame.from_dict(dict(zip(vname,v)),orient='index')
df_v = df_v[df_v[0]>=0.1]
print('==== max voltage ====')
print(df_v.idxmax().item(), df_v.max())
print('==== min voltage ====')
print(df_v.idxmin().item(), df_v.min())

I = dss.PDElements.AllPctNorm()
Iname = dss.PDElements.AllNames()
df_I = pd.DataFrame.from_dict(dict(zip(Iname,I)),orient='index')


df_I['element'] = df_I.index.str.split('.',expand=True)
df_I_line = df_I[df_I['element'].str[0]=='Line']
df_I_line = df_I_line.drop(columns = ['element'])

print('==== max current percentage ====')
print(df_I_line.idxmax().item(), df_I_line.max())
print('==== min current percentage ====')
print(df_I_line.idxmin().item(), df_I_line.min())


df_I_line_sort = df_I_line[0].sort_values(ascending=False)

df_I_line_sort_ab100 = df_I_line_sort[df_I_line_sort>=100]
print('==== above 100% ====')

print(df_I_line_sort_ab100.index)

########## get load ###########
load_df = dss.utils.loads_to_dataframe()
load_df = load_df[load_df.index.str.contains("mv")==False]

load_name = load_df['Name']

region_zone = []
for ln in load_df.index:
    if ln.split('_')[0] + '_' + ln.split('_')[1] in list(load_r0):
        region_zone.append(0)
    elif ln.split('_')[0] + '_' + ln.split('_')[1] in list(load_r1):
        region_zone.append(1)
    else:
        region_zone.append(2)
load_df['zone'] = region_zone


total_list = True
snapshot_count = 0
snapshot_count_list = []
v_min_list = []
v_max_list = []
pen_level_list = []
mc_count = []
zone_list = []
zone = 0


if total_list == True:
    for i in range(0,10):
            print(f"=== Working on scenario {i} ===")
            
            run_command('compile '+fname)
            #run_command('Edit Vsource.vsource pu=1.0')
            dss.Vsources.PU(1.0)
            run_command('solve')
            

            load_list = list(load_df.index)

            # drop mv load
            #load_list = [x for x in load_list_orig if "mv" not in x]

            add_pv_total = []
            pen_level = 0
            for pen_level_target in range(5,105,5):
                print(f" ==== working on pen_level_target={pen_level_target}% ==== " )
                txt = ''
                while pen_level < pen_level_target and len(load_list)!=0 :
                    # choose load from region
                    #print(load_list[:3])
                    
                    load_select = random.choice(load_list) # load select location for PV generator
                    # now define new PV
                    kv = run_command(f"? load.{load_select}.kV")
                    bus1 = run_command(f"? load.{load_select}.bus1")
                    conn = run_command(f"? load.{load_select}.conn")
                    kw = float(run_command(f"? load.{load_select}.kw"))
                    txt = txt + f"new generator.pv_{load_select} conn={conn} bus1={bus1} kv={kv} kw={kw} model=1 Phases=1 \n"
                    run_command(f"new generator.pv_{load_select} conn={conn} bus1={bus1} kv={kv} kw={kw} model=1 Phases=1 kvar=0")
                    load_list.remove(load_select)
                    add_pv_total.append(kw)
                    pen_level = 100*sum(add_pv_total)/load_df['kW'].sum()
                run_command("solve")
                snapshot_count +=1
                
                v = dss.Circuit.AllBusMagPu()
                vname = dss.Circuit.AllNodeNames()

                df_v = pd.DataFrame.from_dict(dict(zip(vname,v)),orient='index')
                df_v = df_v[df_v[0]>=0.1]

                v_min_list.append(float(df_v.min()))
                v_max_list.append(float(df_v.max()))
                if float(df_v.max()) <=1.05:
                    print(float(df_v.max()))
                else:
                    pass
                pen_level_list.append(pen_level_target)
                mc_count.append(i)
                #zone_list.append(zone)
                snapshot_count_list.append(snapshot_count)              


else:

    for zone in range(0,3):
        print(f"=== Working on zone {zone} ===")
        for i in range(0,10):
            print(f"=== Working on scenario {i} ===")
            
            run_command('compile '+fname)
            #run_command('Edit Vsource.vsource pu=1.0')
            dss.Vsources.PU(1.0)
            run_command('solve')
            
            load_list = list(load_df[load_df['zone']==zone].index)
            if total_list == True:
                load_list = list(load_df.index)

            # drop mv load
            #load_list = [x for x in load_list_orig if "mv" not in x]

            add_pv_total = []
            pen_level = 0
            for pen_level_target in range(5,105,5):
                print(f" ==== working on pen_level_target={pen_level_target}% ==== " )
                txt = ''
                while pen_level < pen_level_target and len(load_list)!=0 :
                    # choose load from region
                    #print(load_list[:3])
                    
                    load_select = random.choice(load_list) # load select location for PV generator
                    # now define new PV
                    kv = run_command(f"? load.{load_select}.kV")
                    bus1 = run_command(f"? load.{load_select}.bus1")
                    conn = run_command(f"? load.{load_select}.conn")
                    kw = float(run_command(f"? load.{load_select}.kw"))
                    txt = txt + f"new generator.pv_{load_select} conn={conn} bus1={bus1} kv={kv} kw={kw} model=1 Phases=1 \n"
                    run_command(f"new generator.pv_{load_select} conn={conn} bus1={bus1} kv={kv} kw={kw} model=1 Phases=1 kvar=0")
                    load_list.remove(load_select)
                    add_pv_total.append(kw)
                    pen_level = 100*sum(add_pv_total)/load_df[load_df['zone']==zone]['kW'].sum()
                run_command("solve")
                snapshot_count +=1
                
                v = dss.Circuit.AllBusMagPu()
                vname = dss.Circuit.AllNodeNames()

                df_v = pd.DataFrame.from_dict(dict(zip(vname,v)),orient='index')
                df_v = df_v[df_v[0]>=0.1]
        
                v_min_list.append(float(df_v.min()))
                v_max_list.append(float(df_v.max()))
                if float(df_v.max()) <=1.05:
                    print(float(df_v.max()))
                else:
                    pass
                pen_level_list.append(pen_level_target)
                mc_count.append(i)
                zone_list.append(zone)
                snapshot_count_list.append(snapshot_count)  

########## now save dataframe to results ##########

results_df = pd.DataFrame()

results_df['snapshot_count'] = snapshot_count_list
results_df['v_min'] = v_min_list
results_df['v_max'] = v_max_list
results_df['pen_level'] = pen_level_list
results_df['scenario'] = mc_count
if total_list != True:
    results_df['zone'] = zone_list



print(f" ---- Simulation is done! high five! save to results_df {PATH}")
results_df.to_csv(PATH/'results_df.csv')

###################################################





