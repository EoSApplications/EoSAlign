# Load libraries
    # Load statistics libraries
import numpy as np
    # Load third party libraries
from scipy.optimize import root_scalar
from scipy.optimize import brentq





# Luminescence Functions
    # Linear Scale
    # Power
    # Second-Order Polynomial
    # Third-Order Modified Freud-Ingalls-Form
    # SrB4O7





####################
# Linear Scale

    # P(λ) = (λ - λ₀) / A
####################

# Calculate pressure from a peak position
def Linear_Scale__Luminescence__Calculate_Pressure_from_Peak_Position(
    Peak_Position_At_A_Pressure,
    Initial_Peak_Position__Nanometers,
    Slope_Of_Peak_Position_Change_With_Pressure):

    # Linear Scale
        # Historically used in initial ruby fluourescence studies
        # Commonly used for materials that do not require higher order expansions
    Pressure = (Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers) / Slope_Of_Peak_Position_Change_With_Pressure

    return Pressure

# Calculate peak position from a pressure
def Linear_Scale__Luminescence__Calculate_Peak_Position_from_Pressure(
    Pressure,
    Initial_Peak_Position__Nanometers,
    Slope_Of_Peak_Position_Change_With_Pressure):

    # Start with the equation for calculating pressure from a peak position and rearrange to calculate peak position
        # Pressure = (Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers) / Slope_Of_Peak_Position_Change_With_Pressure
    # Multiply both sides by Slope_Of_Peak_Position_Change_With_Pressure
        # Pressure * Slope_Of_Peak_Position_Change_With_Pressure = Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers
    # Add Initial_Peak_Position__Nanometers to both sides
        # Pressure * Slope_Of_Peak_Position_Change_With_Pressure + Initial_Peak_Position__Nanometers = Peak_Position_At_A_Pressure
    Peak_Position_At_A_Pressure = (Pressure * Slope_Of_Peak_Position_Change_With_Pressure) + Initial_Peak_Position__Nanometers

    return Peak_Position_At_A_Pressure



####################
# Power

    # P(λ) = A/B · ((λ/λ₀)^B - 1)
####################

# Calculate pressure from a peak position
def Power__Calculate_Pressure_from_Peak_Position(
    Peak_Position_At_A_Pressure,
    Initial_Peak_Position__Nanometers,
    A__Fitting_Parameter,
    B__Fitting_Parameter):

    # Make sure B_Fitting_Parameter is not zero
    if B__Fitting_Parameter == 0:
        raise ValueError("B_Fitting_Parameter cannot be zero for the Power equation of state.")

    # Power
        # Mao et al., 1986
        # this is a modification of the Murnaghan equation of state
    Pressure = (A__Fitting_Parameter / B__Fitting_Parameter) * (((Peak_Position_At_A_Pressure / Initial_Peak_Position__Nanometers) ** B__Fitting_Parameter) - 1)

    return Pressure

# Calculate peak position from a pressure
def Power__Calculate_Peak_Position_from_Pressure(
    Pressure,
    Initial_Peak_Position__Nanometers,
    A__Fitting_Parameter,
    B__Fitting_Parameter):

    # Make sure A_Fitting_Parameter is not zero
    if A__Fitting_Parameter == 0:
        raise ValueError("A_Fitting_Parameter cannot be zero for the Power equation of state.")
    # Make sure B_Fitting_Parameter is not zero
    if B__Fitting_Parameter == 0:
        raise ValueError("B_Fitting_Parameter cannot be zero for the Power equation of state.")
    # Make sure the Initial_Peak_Position__Nanometers is greater than zero
    if Initial_Peak_Position__Nanometers <= 0:
        raise ValueError("Initial_Peak_Position__Nanometers must be greater than zero for the Power equation of state.")

    # Start with the equation for calculating pressure from a peak position and rearrange to calculate peak position
        # Pressure = (A__Fitting_Parameter / B__Fitting_Parameter) * (((Peak_Position_At_A_Pressure / Initial_Peak_Position__Nanometers) ** B__Fitting_Parameter) - 1)
    # Multiply both sides by (B__Fitting_Parameter / A__Fitting_Parameter)
        # Pressure * (B__Fitting_Parameter / A__Fitting_Parameter) = ((Peak_Position_At_A_Pressure / Initial_Peak_Position__Nanometers) ** B__Fitting_Parameter) - 1
    # Add 1 to both sides
        # Pressure * (B__Fitting_Parameter / A__Fitting_Parameter) + 1 = (Peak_Position_At_A_Pressure / Initial_Peak_Position__Nanometers) ** B__Fitting_Parameter
    # Take the B__Fitting_Parameter root of both sides
        # ((Pressure * (B__Fitting_Parameter / A__Fitting_Parameter)) + 1) ** (1 / B__Fitting_Parameter) = Peak_Position_At_A_Pressure / Initial_Peak_Position__Nanometers
    # Multiply both sides by Initial_Peak_Position__Nanometers
        # Initial_Peak_Position__Nanometers * (((Pressure * (B__Fitting_Parameter / A__Fitting_Parameter)) + 1) ** (1 / B__Fitting_Parameter)) = Peak_Position_At_A_Pressure
    Peak_Position_At_A_Pressure = Initial_Peak_Position__Nanometers * (((Pressure * (B__Fitting_Parameter / A__Fitting_Parameter)) + 1) ** (1 / B__Fitting_Parameter))

    return Peak_Position_At_A_Pressure



####################
# Second-Order Polynomial

    # P(λ) = A · (λ-λ₀)/λ₀ · (1 + B·(λ-λ₀)/λ₀)
####################

# Calculate pressure from a peak position
def Second_Order_Polynomial__Calculate_Pressure_from_Peak_Position(
    Peak_Position_At_A_Pressure,
    Initial_Peak_Position__Nanometers,
    A__Fitting_Parameter,
    B__Fitting_Parameter):

    # Second-Order Polynomial
        # Shen et al., 2020
        # proposed to better agree with experimental and theoretical observations at high pressure
    Pressure = (A__Fitting_Parameter) * ((Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers) / Initial_Peak_Position__Nanometers) * (1 + (B__Fitting_Parameter * ((Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers) / Initial_Peak_Position__Nanometers)))

    return Pressure

# Calculate peak position from a pressure
def Second_Order_Polynomial__Calculate_Peak_Position_from_Pressure(
    Pressure,
    Initial_Peak_Position__Nanometers,
    A__Fitting_Parameter,
    B__Fitting_Parameter):

    # Make sure A_Fitting_Parameter is not zero
    if A__Fitting_Parameter == 0:
        raise ValueError("A_Fitting_Parameter cannot be zero for the Second-Order Polynomial equation of state.")
    # Make sure the Initial_Peak_Position__Nanometers is greater than zero
    if Initial_Peak_Position__Nanometers <= 0:
        raise ValueError("Initial_Peak_Position__Nanometers must be greater than zero for the Second-Order Polynomial equation of state.")

    # Start with the equation for calculating pressure from a peak position and rearrange to calculate peak position
        # Pressure = (A__Fitting_Parameter) * ((Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers) / Initial_Peak_Position__Nanometers) * (1 + (B__Fitting_Parameter * ((Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers) / Initial_Peak_Position__Nanometers)))
    # Now substitute a temperary variable for the Peak_Position_At_A_Pressure minus Initial_Peak_Position__Nanometers divided by Initial_Peak_Position__Nanometers
        # Temperary_Variable = (Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers) / Initial_Peak_Position__Nanometers
        # Pressure = (A__Fitting_Parameter) * (Temperary_Variable) * (1 + (B__Fitting_Parameter * Temperary_Variable))
    # Subtract Pressure from both sides to set the equation equal to zero
        # 0 = (A__Fitting_Parameter) * (Temperary_Variable) * (1 + (B__Fitting_Parameter * Temperary_Variable)) - Pressure
    # Rearrange into standard form of a quadratic equation
        # 0 = - Pressure + ((A__Fitting_Parameter) * (Temperary_Variable)) + ((A__Fitting_Parameter) * (B__Fitting_Parameter) * (Temperary_Variable ** 2))
    # Now we can use the quadratic formula to solve for the Temperary_Variable
        # 0 = c + bx + ax^2
            # c = - Pressure
            # b = A__Fitting_Parameter
            # a = A__Fitting_Parameter * B__Fitting_Parameter
        # x = (-b ± sqrt(b^2 - 4ac)) / (2a)
            # We want to solve for the Temperary_Variable
        # Temperary_Variable = (- A__Fitting_Parameter ± sqrt((A__Fitting_Parameter ** 2) - (4 * (A__Fitting_Parameter * B__Fitting_Parameter) * (- Pressure)))) / (2 * (A__Fitting_Parameter * B__Fitting_Parameter))
    # We want to use the positive root of the quadratic formula
        # If we used the negative root then the peak positions would be negative
    # First we should check if we can make a simplification
        # If B__Fitting_Parameter is essensioally zero then the quadratic term zeros out and the equation becomes linear
        # So the Temperary_Variable would be equal to Pressure divided by A__Fitting_Parameter
    if abs(B__Fitting_Parameter) < 1e-6:
        Temperary_Variable = Pressure / A__Fitting_Parameter
    # Otherwise we can use the quadratic formula to solve for the Temperary_Variable
    else:
        # Check if the inside of the square root is negative
            # If it is negative then there are no real roots and we cannot solve for the peak position
        if (A__Fitting_Parameter ** 2) - (4 * (A__Fitting_Parameter * B__Fitting_Parameter) * (- Pressure)) < 0:
            raise ValueError("The inside of the square root is negative, so there are no real roots and we cannot solve for the peak position for the polynomial equation of state")
        # Solve for the positive root
        Temperary_Variable = (- A__Fitting_Parameter + np.sqrt((A__Fitting_Parameter ** 2) - (4 * (A__Fitting_Parameter * B__Fitting_Parameter) * (- Pressure)))) / (2 * (A__Fitting_Parameter * B__Fitting_Parameter))
    # Now we can substitute back in for the Temperary_Variable to solve for the Peak_Position_At_A_Pressure
        # Temperary_Variable = (Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers) / Initial_Peak_Position__Nanometers
        # (Temperary_Variable * Initial_Peak_Position__Nanometers) = Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers
        # Peak_Position_At_A_Pressure = (Temperary_Variable * Initial_Peak_Position__Nanometers) + Initial_Peak_Position__Nanometers
    Peak_Position_At_A_Pressure = (Temperary_Variable * Initial_Peak_Position__Nanometers) + Initial_Peak_Position__Nanometers

    return Peak_Position_At_A_Pressure



####################
# Third-Order Modified Freud-Ingalls-Form

    # λ(P) = λ₀ · (1 - C/(B+C)·ln(1 + (B+C)/A·P))^(-1/C)
    # P(λ) = A/(B+C) · (e^((B+C)/C · (1-(λ/λ₀)^(-C))) - 1)
####################

# Calculate pressure from a peak position
def Third_Order_Modified_Freud_Ingalls_Form__Calculate_Pressure_from_Peak_Position(
    Peak_Position_At_A_Pressure,
    Initial_Peak_Position__Nanometers,
    A__Fitting_Parameter,
    B__Fitting_Parameter,
    C__Fitting_Parameter):

    # Third-Order Modified Freud-Ingalls-Form
        # Holzapfel, 2003 and 2005
        # matches the slope and curvature of the Murnaghan form at low pressure and adopts a different curvature at high pressures
    Pressure = (A__Fitting_Parameter / (B__Fitting_Parameter + C__Fitting_Parameter)) * ((np.e ** ((((B__Fitting_Parameter + C__Fitting_Parameter) / C__Fitting_Parameter) * (1 - ((Peak_Position_At_A_Pressure / Initial_Peak_Position__Nanometers) ** (- C__Fitting_Parameter)))))) - 1)

    return Pressure

# Calculate peak position from a pressure
def Third_Order_Modified_Freud_Ingalls_Form__Calculate_Peak_Position_from_Pressure(
    Pressure,
    Initial_Peak_Position__Nanometers,
    A__Fitting_Parameter,
    B__Fitting_Parameter,
    C__Fitting_Parameter):

    # Third-Order Modified Freud-Ingalls-Form
        # Holzapfel, 2003 and 2005
        # matches the slope and curvature of the Murnaghan form at low pressure and adopts a different curvature at high pressures
    Peak_Position_At_A_Pressure = (Initial_Peak_Position__Nanometers) * ((1 - ((C__Fitting_Parameter / (B__Fitting_Parameter + C__Fitting_Parameter)) * (np.log(1 + (((B__Fitting_Parameter + C__Fitting_Parameter) / A__Fitting_Parameter) * Pressure))))) ** (- (1 / C__Fitting_Parameter)))

    return Peak_Position_At_A_Pressure



####################
# SrB4O7

    # P(λ) = A · Δλ · (1 + B·Δλ) / (1 + C·Δλ), Δλ = λ - λ₀
####################

# Calculate pressure from a peak position
def SrB4O7__Calculate_Pressure_from_Peak_Position(
    Peak_Position_At_A_Pressure,
    Initial_Peak_Position__Nanometers,
    A__Fitting_Parameter,
    B__Fitting_Parameter,
    C__Fitting_Parameter):

    # SrB4O7 
        # Datchi et al., 1997
        # baised on the Pade approximation technique
    Change_In_Peak_Position = (Peak_Position_At_A_Pressure - Initial_Peak_Position__Nanometers)
    Pressure = (A__Fitting_Parameter) * ((Change_In_Peak_Position) * ((1 + (B__Fitting_Parameter * Change_In_Peak_Position)) / (1 + C__Fitting_Parameter * Change_In_Peak_Position)))

    return Pressure

# Calculate peak position from a pressure
def SrB4O7__Calculate_Peak_Position_from_Pressure(
    Pressure,
    Initial_Peak_Position__Nanometers,
    A__Fitting_Parameter,
    B__Fitting_Parameter,
    C__Fitting_Parameter):

    # The SrB4O7 equation cannot be rearranged to isolate Peak_Position_At_A_Pressure because Peak_Position_At_A_Pressure appears in multiple terms with different fractional powers
        # So instead we can use an iterative solver to find Peak_Position_At_A_Pressure for a given Pressure
    
    # Call the SrB4O7 equation
    def SrB4O7_Equation(Peak_Position_At_A_Pressure):
        return SrB4O7__Calculate_Pressure_from_Peak_Position(Peak_Position_At_A_Pressure, Initial_Peak_Position__Nanometers, A__Fitting_Parameter, B__Fitting_Parameter, C__Fitting_Parameter) - Pressure
    
    # Use Brent's method to solve for Peak_Position_At_A_Pressure
    try:
        Equation = SrB4O7_Equation
            # The peak position should be between 95% and 110% of the ambient peak position
        Bracket = [0.95 * Initial_Peak_Position__Nanometers, 1.1 * Initial_Peak_Position__Nanometers]
            # Use the invverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Peak_Position_At_A_Pressure
        Solution = root_scalar(Equation, bracket = Bracket, method = Method)
        if Solution.converged:
            return Solution.root
        else:
            return np.nan
    except ValueError:
        # The function did not converge 
        return np.nan




