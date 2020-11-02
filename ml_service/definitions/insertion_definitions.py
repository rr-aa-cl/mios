from definitions.templates import insertion


def insert_cylinder(d: float):
    insertable = "cylinder_" + str(d)
    insert_into = "hole_" + str(d)
    approach = "hole_" + str(d) + "_above"
    pd = insertion(insertable, insert_into, approach)
    pd.cost_function.geometry_factor = d / 1000
    return pd
