from definitions.templates import insertion


def insert_cylinder(d: float):
    insertable = "cylinder_" + str(d)
    insert_into = "hole_" + str(d)
    approach = "hole_" + str(d) + "_above"
    pd = insertion(insertable, insert_into, approach)
    pd.cost_function.geometry_factor = d / 1000
    return pd


def insert_key(key_type: str):
    insertable = "key_" + key_type
    insert_into = "lock_" + key_type
    approach = "lock_" + key_type + "_above"
    pd = insertion(insertable, insert_into, approach)
    pd.cost_function.geometry_factor = 0.005
    pd.domain.limits["offset_x"] = (-0.002, 0.002)
    pd.domain.limits["offset_y"] = (-0.002, 0.002)
    pd.domain.limits["wiggle_a_psi"] = (-0.01, 0.01)
    pd.domain.limits["wiggle_f_psi"] = (-0.01, 0.01)
    return pd
