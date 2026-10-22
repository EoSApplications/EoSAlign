# Load libraries
    # Load standard libraries
import numpy as np
    # Load local functions from local files
from EoS_Math.Fitting_Functions import Fit_Fitting_Model, Make_Measurement_Grid, Convert_Pressure_Between_Calibrations





# Fit every checked model to the data
    # Read_Parameters(Model_Name, Model) -> (guesses, fixed parameter names, fixed uncertainties)
    # Read_Composition_Inputs(Model) -> (effective Z, atoms per volume unit), both None if the model does not need them
def Run_Fits(Checked_Models, Read_Parameters, Read_Composition_Inputs, Measurement, Sigma_Measurement, Pressure, Sigma_Pressure, Reference_Pressure, Random_Generator):

    Fit_Results = {}
    Reports = []
    Measurement_Dense = Make_Measurement_Grid(Measurement)

    for Model in Checked_Models:
        Model_Name = Model["name"]
        try:
            Effective_Z, Atoms_Per_Unit = Read_Composition_Inputs(Model)
            Guesses, Fixed, Fixed_Uncertainties = Read_Parameters(Model_Name, Model)
            Fit = Fit_Fitting_Model(Model, Guesses, Fixed, Fixed_Uncertainties, Measurement, Pressure, Sigma_Measurement, Sigma_Pressure, Measurement_Dense, Random_Generator, Reference_Pressure, Effective_Z, Atoms_Per_Unit)
            Fit_Results[Model_Name] = {
                **Fit,
                "entry": Model,
                "meas_dense": Measurement_Dense,
                "z_val": Effective_Z,
                "atoms_per_unit": Atoms_Per_Unit,
            }
            Reports.append(f"=== {Model_Name} ===\n{Fit['result'].fit_report()}\n")
        except Exception as Error:
            Reports.append(f"=== {Model_Name} ===\nFIT FAILED: {Error}\n")
            print(f"EoSFitting fit error [{Model_Name}]: {Error}")

    return Fit_Results, Reports



# Convert the pressures to each target calibration and refit every model to the converted pressures
    # Read_Parameters(Model_Name, Model) -> (guesses, fixed parameter names, fixed uncertainties); only the fixed ones are used
def Run_Alignment(Fit_Results, Source_Calibration, Target_Calibrations, Read_Parameters, Measurement, Sigma_Measurement, Pressure, Sigma_Pressure, Reference_Pressure, Random_Generator):

    Aligned_Results = {}

    for Target_Calibration in Target_Calibrations:
        # Convert the pressures to the target calibration
        Converted_Pressure = np.zeros_like(Pressure)
        Converted_Sigma_Pressure = np.zeros_like(Sigma_Pressure)
        for Index, (Value, Sigma) in enumerate(zip(Pressure, Sigma_Pressure)):
            Converted_Pressure[Index], Converted_Sigma_Pressure[Index] = Convert_Pressure_Between_Calibrations(Value, Sigma, Source_Calibration, Target_Calibration)

        # Refit all models with the converted pressures
        Target_Model_Results = {}
        for Model_Name, Original_Fit in Fit_Results.items():
            Model = Original_Fit["entry"]
            try:
                # Refit from the original best fit, with the same fixed parameters and uncertainties
                _, Fixed, Fixed_Uncertainties = Read_Parameters(Model_Name, Model)
                Guesses = {Parameter["name"]: Original_Fit["result"].params[Parameter["name"]].value for Parameter in Model["params"] if Parameter["name"] in Original_Fit["result"].params}
                # The fit weights by 1/sigma of the converted pressure, folding in 1/sigma of the measurement through the effective variance
                Fit = Fit_Fitting_Model(Model, Guesses, Fixed, Fixed_Uncertainties, Measurement, Converted_Pressure, Sigma_Measurement, Converted_Sigma_Pressure, Original_Fit["meas_dense"], Random_Generator, Reference_Pressure, Original_Fit["z_val"], Original_Fit.get("atoms_per_unit"))
                Target_Model_Results[Model_Name] = {
                    "result": Fit["result"],
                    "param_stderr": Fit["param_stderr"],
                    "meas_dense": Original_Fit["meas_dense"],
                    "p_nominal": Fit["p_nominal"],
                    "p_std": Fit["p_std"],
                    "p_converted": Converted_Pressure,
                    "sp_converted": Converted_Sigma_Pressure,
                    "tgt_label": Target_Calibration,
                }
            except Exception as Error:
                print(f"EoSFitting alignment refit [{Model_Name}/{Target_Calibration}]: {Error}")

        Aligned_Results[Target_Calibration] = {
            "tgt_label": Target_Calibration,
            "model_results": Target_Model_Results,
            "p_converted": Converted_Pressure,
            "sp_converted": Converted_Sigma_Pressure,
        }

    return Aligned_Results
