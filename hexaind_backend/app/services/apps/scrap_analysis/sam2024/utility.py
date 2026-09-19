import configparser


def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config


class Material:
    def __init__(self, name):
        self.name = name
        self.form = ""
        self.amount_available = 0
        self.min_amount = 0
        self.recovery = 1
        self.dict_chemistry = {}
        self.cost = 0


class Plant:
    def __init__(self, name):
        self.name = name
        self.list_alloys_demand = []
        self.list_material_supply = []
        self.dict_alloys_demand = {}
        self.dict_material_supply = {}
        self.dict_supply = {}
        self.dict_supply_minimum = {}
        self.dict_supply_maximum = {}
        self.dict_scrap_rate = {}
        self.list_form = []
        self.dict_form_capacity = {}
        self.prime = Material("Prime")


class Alloy:
    def __init__(self, name):
        self.name = name
        self.list_elements = []
        self.dict_chemistry = {}
