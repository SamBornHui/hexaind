import pandas as pd
import numpy as np
import os
from .utility import *


def read_input(filepath):
    xl = pd.ExcelFile(filepath)
    plant_list = []
    plant_dict = {}
    transportation_dict = {}

    df = xl.parse("ScrapFlow")
    scrap_flow_dict = (
        df.groupby("Destination")
        .agg({"Source": lambda x: x.tolist()})
        .to_dict()["Source"]
    )

    df = xl.parse("Demand").set_index(["Plant", "Alloy"])
    df = df[df["Supply"] > 0]
    # Remove unused destinations from ScrapFlow
    to_remove = []
    for dest in scrap_flow_dict:
        if dest not in df.index.get_level_values("Plant").unique():
            to_remove.append(dest)
    for k in to_remove:
        del scrap_flow_dict[k]
    # continue parsing Demand
    elements = [elem for elem in df.columns if len(elem) <= 2]
    for idx in df.index:
        temp = df.loc[idx]
        if str(idx[0]) not in plant_list:
            plant = Plant(str(idx[0]))
            plant_list.append(plant.name)
            plant_dict.update({plant.name: plant})
        else:
            plant = plant_dict.get(str(idx[0]))
        alloy = Alloy(str(idx[1]))
        plant.list_alloys_demand.append(alloy.name)
        plant.dict_alloys_demand.update({alloy.name: alloy})
        plant.dict_supply.update({alloy.name: temp["Supply"]})
        if "Minimum" in temp:
            plant.dict_supply_minimum.update({alloy.name: temp["Minimum"]})
        if "Maximum" in temp:
            plant.dict_supply_maximum.update({alloy.name: temp["Maximum"]})
        plant.dict_scrap_rate.update({alloy.name: temp["RAS scrap rate"]})
        alloy.list_elements = elements
        alloy.dict_chemistry.update(temp[elements].to_dict())
        material = Material(str(idx[1]))
        material.dict_chemistry.update(temp[elements].to_dict())
        material.amount_available = (
            temp["Supply"] / (1 - temp["RAS scrap rate"]) * temp["RAS scrap rate"]
        )
        material.recovery = temp["Recovery"]
        plant.list_material_supply.append(material.name)
        plant.dict_material_supply.update({material.name: material})
        # if plant.name not in scrap_flow_dict[plant.name]:
        #     scrap_flow_dict[plant.name] += [plant.name]

    df = xl.parse("Scrap").set_index(["Plant", "Alloy"])
    # TODO: probably should make this more reliable
    # idea is to filter out any inputs with missing data, otherwise that can cause issues for optimizer
    if "Si" in df.columns:
        df = df[~df["Si"].isna()]
    elements = [elem for elem in df.columns if len(elem) <= 2]
    for idx in df.index:
        temp = df.loc[idx]
        plant = Plant(str(idx[0]))
        if plant.name not in plant_list:
            plant_list.append(plant.name)
            plant_dict.update({plant.name: plant})
        else:
            plant = plant_dict.get(str(idx[0]))
        material = Material(str(idx[1]))
        material.form = temp["Form"]
        material.min_amount = temp["Minimum Weight"]
        material.amount_available = temp["Available Weight"]
        material.recovery = temp["Recovery"]
        material.dict_chemistry.update(temp[elements].to_dict())
        if "Cost" in temp:
            material.cost = temp["Cost"]
        plant.list_material_supply.append(material.name)
        plant.dict_material_supply.update({material.name: material})

    df = xl.parse("Prime").set_index("Plant")
    elements = [elem for elem in df.columns if len(elem) <= 2]
    for idx in df.index:
        temp = df.loc[idx]
        if str(idx) not in plant_list:
            continue
        material = Material("Prime")
        material.recovery = temp["Recovery"]
        if "Cost" in temp:
            material.cost = temp["Cost"]
        material.dict_chemistry.update(temp[elements].to_dict())
        plant = plant_dict.get(str(idx))
        plant.prime = material

    df = xl.parse("Capacity").set_index("Destination")
    for idx in df.index:
        temp = df.loc[idx]
        if str(idx) not in plant_list:
            continue
        plant = plant_dict.get(str(idx))
        plant.list_form.append(temp["Form"])
        plant.dict_form_capacity.update(
            {temp["Form"]: [temp["Minimum"], temp["Capacity"]]}
        )

    df = xl.parse("Transportation").set_index(["Source", "Destination"])
    for idx in df.index:
        temp = df.loc[idx]
        if str(idx[0]) not in plant_list or str(idx[1]) not in plant_list:
            continue
        transportation_dict.update({f"{idx[0]}-{idx[1]}": temp["Cost"]})

    try:
        limits_df = xl.parse("Limits")
        limits_df = limits_df.fillna(1)
    except ValueError:
        limits_df = None

    return scrap_flow_dict, plant_dict, transportation_dict, limits_df
