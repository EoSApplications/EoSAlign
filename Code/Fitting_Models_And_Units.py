# Load libraries
    # Load local functions from local files
from Reference_Values_And_Units import Method_Units, Volume_Units
from EoS_Math.Fitting_Models import Get_Fitting_Models_For_Method





# The fittable models are built, not typed in here. EoS_Math.Fitting_Models makes one
# model for every equation in Function_Information (Reference_Values_And_Units) that has
# "Fitting_Information". Each model is a dict:
#   name            - display string (the Function_Information Display_Name)
#   function_key    - Function_Information key (used to look up the LaTeX equation)
#   fn              - the EoS_Math pressure function
#   variable_order  - the variables of fn after the measurement, in order
#   params          - list of {name, label, default, positive_only} dicts
#   has_P0 / needs_Z - True when the user enters the reference pressure / atomic number

# Unit -> measurement method. Built from Volume_Units and Method_Units so the units are
# exactly the ones EoSAlign uses
Unit_To_Method = {}
# Measurement method -> the models that can be fitted to it
Models_By_Method = {}



# Build the unit and model lookups the first time they are needed (the calibrations have to be loaded first)
def Load_Fitting_Models_And_Units():

    if Unit_To_Method:
        return
    for Method, Method_Unit in Method_Units.items():
        # XRD data can be entered in any of the volume units; every other method has one unit
        for Unit in (Volume_Units if Method == "XRD" else [Method_Unit]):
            Unit_To_Method[Unit] = Method
        Models_By_Method[Method] = Get_Fitting_Models_For_Method(Method)



# Get every unit the data can be entered in
def Get_Fitting_Units():

    Load_Fitting_Models_And_Units()
    return list(Unit_To_Method.keys())



# Get the measurement method for a unit, or None if no unit has been selected
def Get_Method_For_Unit(Unit):

    Load_Fitting_Models_And_Units()
    return Unit_To_Method.get(Unit)



# Get the models that can be fitted to a method
def Get_Models_For_Method(Method):

    Load_Fitting_Models_And_Units()
    return Models_By_Method.get(Method, [])



# Get the label for the measurement axis of a figure
def Get_Measurement_Axis_Label(Unit):

    return f"Volume ({Unit})" if Get_Method_For_Unit(Unit) == "XRD" else Unit
