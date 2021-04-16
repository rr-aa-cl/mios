from definitions.templates import insertion
from definitions.templates import insertion_light
from definitions.templates import insertion_demo
from definitions.templates import tax_insertion


def insert_cylinder(d: float, geometry_factor: float):
    insertable = "cylinder_" + str(d)
    insert_into = "hole_" + str(d)
    approach = "hole_" + str(d) + "_above"
    pd = insertion(insertable, insert_into, approach)
    pd.cost_function.geometry_factor = geometry_factor
    return pd


def insert_cylinder_light(d: float, geometry_factor: float):
    insertable = "cylinder_" + str(d)
    insert_into = "hole_" + str(d)
    approach = "hole_" + str(d) + "_above"
    pd = insertion_light(insertable, insert_into, approach)
    pd.cost_function.geometry_factor = geometry_factor
    return pd


def insert_key(key_type: str, geometry_factor: float):
    insertable = "key_" + key_type
    insert_into = "lock_" + key_type
    approach = "lock_" + key_type + "_above"
    pd = tax_insertion(insertable, insert_into, approach)
    pd.cost_function.geometry_factor = geometry_factor
    pd.domain.limits["offset_x"] = (-0.002, 0.002)
    pd.domain.limits["offset_y"] = (-0.002, 0.002)
    return pd


def insert_key_light(key_type: str, geometry_factor: float):
    insertable = "key_" + key_type
    insert_into = "lock_" + key_type
    approach = "lock_" + key_type + "_above"
    pd = insertion_light(insertable, insert_into, approach)
    pd.cost_function.geometry_factor = geometry_factor
    pd.domain.limits["offset_x"] = (-0.002, 0.002)
    pd.domain.limits["offset_y"] = (-0.002, 0.002)
    return pd


def insert_key_demo(key_type: str, geometry_factor: float):
    insertable = "key_" + key_type
    insert_into = "lock_" + key_type
    approach = "lock_" + key_type + "_above"
    pd = insertion_demo(insertable, insert_into, approach)
    pd.cost_function.geometry_factor = geometry_factor
    pd.domain.limits["offset_x"] = (-0.002, 0.002)
    pd.domain.limits["offset_y"] = (-0.002, 0.002)
    return pd


def insert_generic():
    insertable = "generic_insertable"
    insert_into = "generic_container"
    approach = "generic_container_approach"
    pd = tax_insertion(insertable, insert_into, approach)
    pd.domain.limits["offset_x"] = (-0.002, 0.002)
    pd.domain.limits["offset_y"] = (-0.002, 0.002)
    return pd
