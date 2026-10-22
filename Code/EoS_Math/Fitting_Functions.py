# Load libraries
    # Load third-party libraries
import numpy as np
from lmfit import Model
    # Load local libraries
from .Error_Propagation_Functions import Numerical_Derivative
from .Fitting_Models import Build_Model_Function, Get_Fixed_Variable_Values, Get_Atoms_Divisor, Evaluate_Model_Pressures





# The math EoSFitting uses to fit a pressure model to measured values (volumes, peak positions or wavenumbers)
    # Everything here works on lmfit objects and numpy arrays only, nothing here depends on the GUI



# Fit "pressure = model(measurement)" while accounting for the measurement uncertainties
    # The dependent variable is pressure, so the main weight is 1 / (the uncertainty in pressure)
    # When the measurement (the independent variable, for example volume) also has an uncertainty the effective variance method
    # (Orear, 1982) adds it in:
        # Effective_Uncertainty^2 = Pressure_Uncertainty^2 + (d_Model / d_Measurement * Measurement_Uncertainty)^2
        # Weight = 1 / Effective_Uncertainty
    # d_Model / d_Measurement is calculated numerically at the current best fit and the fit is repeated twice
    # Falls back to weighting by 1 / (the uncertainty in pressure) alone, or to an unweighted fit, when uncertainties are missing
def Fit_Model_With_Measurement_Uncertainties(LMFit_Model, LMFit_Parameters, Pressure_Values, Measurement_Values, Pressure_Uncertainties, Measurement_Uncertainties):

    # Make sure the uncertainties are arrays and check which of them were entered
    Pressure_Uncertainties = np.asarray(Pressure_Uncertainties, dtype=float)
    Measurement_Uncertainties = np.asarray(Measurement_Uncertainties, dtype=float)
    Has_Pressure_Uncertainties = np.any(Pressure_Uncertainties > 0)
    Has_Measurement_Uncertainties = np.any(Measurement_Uncertainties > 0)

    # If no uncertainties were entered then do an unweighted fit
    if not Has_Pressure_Uncertainties and not Has_Measurement_Uncertainties:
        return LMFit_Model.fit(Pressure_Values, LMFit_Parameters, x=Measurement_Values)

    # Find the first weights from the uncertainty in pressure
    if Has_Pressure_Uncertainties:
        # Points without a pressure uncertainty use the smallest uncertainty that was entered
        Safe_Pressure_Uncertainties = np.where(Pressure_Uncertainties > 0, Pressure_Uncertainties, np.nan)
        Smallest_Uncertainty = np.nanmin(Safe_Pressure_Uncertainties)
        Safe_Pressure_Uncertainties = np.where(np.isfinite(Safe_Pressure_Uncertainties), Safe_Pressure_Uncertainties, Smallest_Uncertainty)
        Initial_Weights = 1.0 / Safe_Pressure_Uncertainties
    else:
        Initial_Weights = np.ones_like(np.asarray(Pressure_Values, dtype=float))
    Fit_Result = LMFit_Model.fit(Pressure_Values, LMFit_Parameters, x=Measurement_Values, weights=Initial_Weights)

    # If there are no measurement uncertainties then the first fit is the final fit
    if not Has_Measurement_Uncertainties:
        return Fit_Result

    # Repeat the fit with the effective variance weights so the measurement uncertainties are included
    try:
        Measurement_Array = np.asarray(Measurement_Values, dtype=float)
        for _ in range(2):
            # Find the slope of the model at every measurement with a central difference
            Step_Size = np.where(np.abs(Measurement_Array) > 0, np.abs(Measurement_Array) * 1e-6, 1e-6) + 1e-12
            Model_Slope = (Fit_Result.eval(x=Measurement_Array + Step_Size) - Fit_Result.eval(x=Measurement_Array - Step_Size)) / (2.0 * Step_Size)
            # Combine the pressure uncertainty and the measurement uncertainty (as a pressure uncertainty)
            Effective_Variance = np.where(Pressure_Uncertainties > 0, Pressure_Uncertainties, 0.0) ** 2 + (Model_Slope * Measurement_Uncertainties) ** 2
            Positive_Variances = Effective_Variance[Effective_Variance > 0]
            # Stop if no point has an uncertainty
            if Positive_Variances.size == 0:
                break
            # Points without an uncertainty use the smallest variance
            Effective_Variance = np.where(Effective_Variance > 0, Effective_Variance, Positive_Variances.min())
            Weights = 1.0 / np.sqrt(Effective_Variance)
            # Stop if any weight is not a number
            if not np.all(np.isfinite(Weights)):
                break
            Fit_Result = LMFit_Model.fit(Pressure_Values, LMFit_Parameters, x=Measurement_Values, weights=Weights)
    except Exception as Exception_Message:
        print(f"Fit_Model_With_Measurement_Uncertainties effective variance fallback: {Exception_Message}")

    return Fit_Result



# Combine the uncertainty of every parameter by adding the user entered uncertainties of the fixed parameters into the fitted parameters
    # For every fixed parameter F with an uncertainty Sigma_F the sensitivity of each fitted parameter Theta to F is estimated
    # with a central difference (two refits with F shifted by +Sigma_F and -Sigma_F):
        # d_Theta / d_F = (Theta(F + Sigma_F) - Theta(F - Sigma_F)) / (2 * Sigma_F)
    # Its contribution is added in quadrature to the uncertainty from the fit (the covariance):
        # Sigma_Theta_Total^2 = Sigma_Theta_Fit^2 + Sum over F of (d_Theta / d_F * Sigma_F)^2
    # Returns {parameter name: uncertainty}: the combined uncertainty for the fitted parameters and the entered uncertainty for the fixed parameters
def Propagate_Fixed_Parameter_Uncertainties(LMFit_Model, LMFit_Parameters, Fit_Result, Fixed_Parameter_Uncertainties,
                                            Pressure_Values, Measurement_Values, Pressure_Uncertainties, Measurement_Uncertainties):

    # Start with the uncertainty from the fit for every fitted parameter
    Combined_Uncertainties = {}
    Fitted_Parameter_Names = [Name for Name in Fit_Result.params if Fit_Result.params[Name].vary]
    for Name in Fitted_Parameter_Names:
        Fit_Uncertainty = Fit_Result.params[Name].stderr
        Combined_Uncertainties[Name] = float(Fit_Uncertainty) if Fit_Uncertainty else 0.0

    # Find how much each fixed parameter's uncertainty adds to every fitted parameter
    Added_Variances = {Name: 0.0 for Name in Fitted_Parameter_Names}
    for Fixed_Name, Fixed_Uncertainty in Fixed_Parameter_Uncertainties.items():
        # Skip fixed parameters that do not have an uncertainty
        if Fixed_Uncertainty is None or Fixed_Uncertainty <= 0 or Fixed_Name not in Fit_Result.params:
            continue
        try:
            Fixed_Value = Fit_Result.params[Fixed_Name].value

            # Refit with the fixed parameter shifted by a given amount
            def Refit_With_Shifted_Fixed_Parameter(Shift):
                Shifted_Parameters = LMFit_Parameters.copy()
                # Start the fitted parameters at the best fit so the refit is stable
                for Name in Shifted_Parameters:
                    if Shifted_Parameters[Name].vary and Name in Fit_Result.params:
                        Shifted_Parameters[Name].set(value=Fit_Result.params[Name].value)
                Shifted_Parameters[Fixed_Name].set(value=Fixed_Value + Shift, vary=False)
                return Fit_Model_With_Measurement_Uncertainties(LMFit_Model, Shifted_Parameters, Pressure_Values, Measurement_Values, Pressure_Uncertainties, Measurement_Uncertainties)

            Result_Plus = Refit_With_Shifted_Fixed_Parameter(+Fixed_Uncertainty)
            Result_Minus = Refit_With_Shifted_Fixed_Parameter(-Fixed_Uncertainty)
            for Name in Fitted_Parameter_Names:
                # The shift is Sigma_F so half of the change in the fitted parameter is already d_Theta / d_F * Sigma_F
                Half_Change = (Result_Plus.params[Name].value - Result_Minus.params[Name].value) / 2.0
                Added_Variances[Name] += Half_Change * Half_Change
        except Exception as Exception_Message:
            print(f"Propagate_Fixed_Parameter_Uncertainties [{Fixed_Name}]: {Exception_Message}")

    # Add the uncertainty from the fit and the uncertainty from the fixed parameters in quadrature
    for Name in Fitted_Parameter_Names:
        Combined_Uncertainties[Name] = float(np.sqrt(Combined_Uncertainties[Name] ** 2 + Added_Variances[Name]))
    # The uncertainty of a fixed parameter is the one that was entered
    for Fixed_Name, Fixed_Uncertainty in Fixed_Parameter_Uncertainties.items():
        if Fixed_Uncertainty and Fixed_Uncertainty > 0:
            Combined_Uncertainties[Fixed_Name] = float(Fixed_Uncertainty)

    return Combined_Uncertainties



# Draw random parameter sets from a finished fit (Monte Carlo), used to show the uncertainty of the fitted curve
    # The fitted parameters are drawn from the covariance matrix of the fit
    # A parameter with an entered uncertainty in Standard_Error_Overrides uses that uncertainty instead:
        # a fitted parameter has its row and column of the covariance matrix rescaled
        # a fixed parameter is drawn on its own from a normal distribution around its value
    # Returns a list of dictionaries (parameter name: value), one for each draw
def Sample_Parameter_Draws(Fit_Result, Number_Of_Draws, Random_Generator, Standard_Error_Overrides=None):

    Standard_Error_Overrides = Standard_Error_Overrides or {}
    Fitted_Parameter_Names = list(Fit_Result.var_names)

    # If there is no covariance matrix then every draw is the best fit
    if Fit_Result.covar is None or len(Fitted_Parameter_Names) == 0:
        Best_Fit_Values = {Name: Parameter.value for Name, Parameter in Fit_Result.params.items()}
        Draws = [dict(Best_Fit_Values) for _ in range(Number_Of_Draws)]
    else:
        Mean_Values = np.array([Fit_Result.params[Name].value for Name in Fitted_Parameter_Names], dtype=float)
        Covariance = np.array(Fit_Result.covar, dtype=float)

        # Rescale the rows and columns of the covariance matrix for fitted parameters with an entered uncertainty
        for Name, Uncertainty in Standard_Error_Overrides.items():
            if Name in Fitted_Parameter_Names:
                Index = Fitted_Parameter_Names.index(Name)
                Old_Standard_Deviation = np.sqrt(abs(Covariance[Index, Index]))
                if Old_Standard_Deviation > 0:
                    Scale = Uncertainty / Old_Standard_Deviation
                    Covariance[Index, :] *= Scale
                    Covariance[:, Index] *= Scale
                else:
                    Covariance[Index, Index] = Uncertainty ** 2

        # Draw the fitted parameters and keep the fixed parameters at their values
        Drawn_Values = Random_Generator.multivariate_normal(Mean_Values, Covariance, size=Number_Of_Draws)
        Best_Fit_Values = {Name: Parameter.value for Name, Parameter in Fit_Result.params.items()}
        Draws = [dict(Best_Fit_Values, **dict(zip(Fitted_Parameter_Names, Drawn_Row))) for Drawn_Row in Drawn_Values]

    # Draw the fixed parameters that have an entered uncertainty (each on its own)
    for Name, Uncertainty in Standard_Error_Overrides.items():
        if Name not in Fitted_Parameter_Names and Uncertainty > 0:
            Drawn_Fixed_Values = Random_Generator.normal(
                Fit_Result.params[Name].value if Name in Fit_Result.params else 0.0,
                Uncertainty, size=len(Draws)
            )
            for Draw, Drawn_Value in zip(Draws, Drawn_Fixed_Values):
                Draw[Name] = Drawn_Value

    return Draws



# Convert a pressure from one pressure calibration to another
    # The pressure is turned back into the measured value with the inverse of the source calibration
    # and then into a pressure with the forward function of the target calibration
    # The pressure uncertainty is propagated with the slope of that conversion (found numerically)
    # Returns (the new pressure, the new pressure uncertainty)
    # If the conversion fails the pressure and uncertainty are returned unchanged
def Convert_Pressure_Between_Calibrations(Pressure, Pressure_Uncertainty, Source_Calibration_Label, Target_Calibration_Label):

    try:
        # Load the calibrations here because loading them at the top of the file would load every calibration file
        from .Build_Dataframe import Calibration_Functions
        Source_Forward_Function, Source_Inverse_Function = Calibration_Functions[Source_Calibration_Label]
        Target_Forward_Function, _ = Calibration_Functions[Target_Calibration_Label]
        # Source pressure -> measured value -> target pressure
        Measured_Value = Source_Inverse_Function(Pressure)
        New_Pressure = Target_Forward_Function(Measured_Value)
        # The slope of the target pressure with respect to the source pressure
        Slope = Numerical_Derivative(lambda Source_Pressure: Target_Forward_Function(Source_Inverse_Function(Source_Pressure)), Pressure)
        New_Uncertainty = abs(Slope) * Pressure_Uncertainty if (np.isfinite(Slope) and Pressure_Uncertainty > 0) else 0.0
        return float(New_Pressure), float(New_Uncertainty)
    except Exception as Exception_Message:
        print(f"Convert_Pressure_Between_Calibrations: {Exception_Message}")
        return float(Pressure), float(Pressure_Uncertainty)



# Make the measurements the fitted curve is calculated at: evenly spaced points just past the smallest and largest measurement
def Make_Measurement_Grid(Measurement_Values, Number_Of_Points=300):

    return np.linspace(np.min(Measurement_Values) * 0.995, np.max(Measurement_Values) * 1.005, Number_Of_Points)



# Calculate the uncertainty of a fitted curve from the Monte Carlo parameter draws
    # Evaluate_Curve: a function that calculates the curve for one draw (a dictionary of parameter values)
    # Nominal_Curve: the curve at the best fit (the uncertainty is zero everywhere if too few draws give a usable curve)
    # Only the first Maximum_Draws draws are used (for speed) and a draw that does not give a finite curve is left out
    # The uncertainty at each point is the standard deviation of the curves (with one degree of freedom removed)
def Calculate_Uncertainty_Band(Evaluate_Curve, Parameter_Draws, Nominal_Curve, Maximum_Draws=500):

    Curves = []
    for Draw in Parameter_Draws[:Maximum_Draws]:
        try:
            Curve = Evaluate_Curve(Draw)
            if np.all(np.isfinite(Curve)):
                Curves.append(Curve)
        except Exception:
            pass
    if len(Curves) >= 2:
        return np.std(np.array(Curves), axis=0, ddof=1)
    return np.zeros_like(Nominal_Curve)



# Calculate the ellipse that shows how two fitted parameters trade off against each other
    # The ellipse has Number_Of_Standard_Deviations standard deviations along each of the main axes of the covariance
    # Returns (the width, the height, the angle in degrees) to give to a matplotlib Ellipse
def Calculate_Covariance_Ellipse(Variance_A, Variance_B, Covariance_AB, Number_Of_Standard_Deviations):

    # The main axes of the covariance are its eigenvectors, and their lengths come from its eigenvalues
    Eigenvalues, Eigenvectors = np.linalg.eigh(np.array([[Variance_A, Covariance_AB], [Covariance_AB, Variance_B]]))
    Eigenvalues = np.maximum(Eigenvalues, 0)
    Angle = np.degrees(np.arctan2(Eigenvectors[1, 1], Eigenvectors[0, 1]))
    Width = 2 * Number_Of_Standard_Deviations * np.sqrt(Eigenvalues[1])
    Height = 2 * Number_Of_Standard_Deviations * np.sqrt(Eigenvalues[0])
    return Width, Height, Angle



# Fit one model to the measured values and pressures, and find everything needed to show the result
    # Fitting_Model: one of the models from Get_Fitting_Models_For_Method
    # Starting_Values: the starting value of each parameter, by name (a parameter that is missing starts at the model's default)
    # Fixed_Parameters: the names of the parameters that are held at their starting value
    # Fixed_Uncertainties: the uncertainty of each fixed parameter that has one, by name (empty if none do)
    # Measurement_Grid: the measurements the fitted curve is calculated at
    # Random_Generator: the numpy random generator the Monte Carlo draws come from
    # Reference_Pressure, Atomic_Number, Atoms_Per_Unit: the values the user enters for the model (see Build_Model_Function)
    # Returns a dictionary:
        # result: the lmfit result
        # param_stderr: the uncertainty of every parameter with the uncertainty of the fixed parameters added in (None if there are none)
        # draws: the Monte Carlo draws of the parameters
        # p_nominal: the pressure of the fitted curve at the measurement grid
        # p_std: the uncertainty of the pressure of the fitted curve
def Fit_Fitting_Model(Fitting_Model, Starting_Values, Fixed_Parameters, Fixed_Uncertainties,
                      Measurement_Values, Pressure_Values, Measurement_Uncertainties, Pressure_Uncertainties,
                      Measurement_Grid, Random_Generator, Reference_Pressure, Atomic_Number=None, Atoms_Per_Unit=None, Number_Of_Draws=2000):

    # Build the model and give every parameter its starting value, limit and whether it is fixed
    LMFit_Model = Model(Build_Model_Function(Fitting_Model, Reference_Pressure, Atomic_Number, Atoms_Per_Unit), independent_vars=['x'])
    LMFit_Parameters = LMFit_Model.make_params()
    for Parameter in Fitting_Model['params']:
        Name = Parameter['name']
        if Name not in LMFit_Parameters:
            continue
        LMFit_Parameters[Name].set(value=Starting_Values.get(Name, Parameter['default']), vary=Name not in Fixed_Parameters,
                                   min=1e-9 if Parameter.get('positive_only') else -np.inf)

    # Fit: weight by 1 / (the uncertainty in pressure), and use the measurement uncertainty too when there is one
    Fit_Result = Fit_Model_With_Measurement_Uncertainties(LMFit_Model, LMFit_Parameters, Pressure_Values, Measurement_Values, Pressure_Uncertainties, Measurement_Uncertainties)

    # Monte Carlo draws of the parameters
    Draws = Sample_Parameter_Draws(Fit_Result, Number_Of_Draws, Random_Generator, Fixed_Uncertainties)

    # The uncertainty of every parameter, with the uncertainty of the fixed parameters added into the fitted parameters
    Parameter_Uncertainties = (
        Propagate_Fixed_Parameter_Uncertainties(LMFit_Model, LMFit_Parameters, Fit_Result, Fixed_Uncertainties,
                                                Pressure_Values, Measurement_Values, Pressure_Uncertainties, Measurement_Uncertainties)
        if Fixed_Uncertainties else None
    )

    # The fitted curve and its uncertainty
    Fixed_Variable_Values = Get_Fixed_Variable_Values(Fitting_Model, Reference_Pressure, Atomic_Number)
    Atoms_Divisor = Get_Atoms_Divisor(Fitting_Model, Atoms_Per_Unit)
    Nominal_Curve = Evaluate_Model_Pressures(Fitting_Model, Fixed_Variable_Values, Measurement_Grid,
                                             {Name: Fit_Result.params[Name].value for Name in Fit_Result.params}, Atoms_Divisor)
    Uncertainty_Band = Calculate_Uncertainty_Band(
        lambda Draw: Evaluate_Model_Pressures(Fitting_Model, Fixed_Variable_Values, Measurement_Grid, Draw, Atoms_Divisor),
        Draws, Nominal_Curve)

    return {'result': Fit_Result, 'param_stderr': Parameter_Uncertainties, 'draws': Draws, 'p_nominal': Nominal_Curve, 'p_std': Uncertainty_Band}
