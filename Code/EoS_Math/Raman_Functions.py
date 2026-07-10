# Load libraries
    # Load statistics libraries
import numpy as np
    # Load third party libraries
from scipy.optimize import root_scalar
from scipy.optimize import brentq





# Raman Functions
    # Splitting of the Diamond Edge
        # Akahama and Kawamura, 2004 - Diamond - Polynomial
        # Akahama and Kawamura, 2006 - Diamond - Finite Strain Approximation
        # Akahama and Kawamura, 2010 - Diamond
        # Eremets et al., 2023 - Diamond
    # Study Specific
        # Evans et al., 2005 - Beryllium - Polynomial
        # Olijnyk et al., 2001 - Beryllium and Rhenium - Polynomial
        # Pease et al., 2025 - Rhenium - Polynomial
        # Goncharov et al., 2005 - Cubic Boron Nitride
        # Datchi and Canny, 2004; Ono et al., 2015; Ren et al., 2023 - Cubic Boron Nitride
            # Datchi and Canny, 2004 - Cubic Boron Nitride
            # Ren et al., 2023 - Cubic Boron Nitride
        # Datchi et al., 2007 - Cubic Boron Nitride





########################################
# Splitting of the Diamond Edge
########################################



####################
# Akahama and Kawamura, 2004 - Diamond - Polynomial

    # P(υ) = A + B·υ + C·υ²
    # υ(P) = D + E·(P + F)^½
####################


# Calculate pressure from a wavenumber
def Akahama_and_Kawamura_2004__Diamond__Polynomial__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant,
    C__Fitting_Constant):

    # Akahama and Kawamura, 2004 - Diamond - Polynomial
    Pressure = A__Fitting_Constant + (B__Fitting_Constant * Wavenumber) + (C__Fitting_Constant * (Wavenumber ** 2))
    
    return Pressure

# Calculate wavenumber from a pressure
def Akahama_and_Kawamura_2004__Diamond__Polynomial__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    D__Fitting_Constant,
    E__Fitting_Constant,
    F__Fitting_Constant):

    # Akahama and Kawamura, 2004 - Diamond - Polynomial
    Wavenumber = D__Fitting_Constant + (E__Fitting_Constant * ((Pressure + F__Fitting_Constant) ** (1 / 2)))

    return Wavenumber



####################
# Akahama and Kawamura, 2006 - Diamond - Finite Strain Approximation

    # P(υ) = K₀ · (υ-υ₀)/υ₀ · (1 + (K₀′-1)/2 · (υ-υ₀)/υ₀)
####################


# Calculate pressure from a wavenumber
def Akahama_and_Kawamura_2006__Diamond__Finite_Strain_Approximation__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Akahama and Kawamura, 2006 - Diamond - Finite Strain Approximation
        # Aleksandrov et al., 1987 
            # Finite Strain Approximation
    Pressure = (A__Fitting_Constant) * ((Wavenumber - Initial_Peak_Position__Wavenumber) / Initial_Peak_Position__Wavenumber) * (1 + (((B__Fitting_Constant - 1) * ((Wavenumber - Initial_Peak_Position__Wavenumber) / Initial_Peak_Position__Wavenumber)) / 2))

    return Pressure

# Calculate wavenumber from a pressure
def Akahama_and_Kawamura_2006__Diamond__Finite_Strain_Approximation__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Start with the equation for calculating pressure from a wavenumber and rearrange to calculate wavenumber
        # Pressure = (A__Fitting_Constant) * ((Wavenumber - Initial_Peak_Position__Wavenumber) / Initial_Peak_Position__Wavenumber) * (1 + (((B__Fitting_Constant - 1) * ((Wavenumber - Initial_Peak_Position__Wavenumber) / Initial_Peak_Position__Wavenumber)) / 2))
    # Now substitute a temperary variable for the Wavenumber minus the Ambient Wavenumber divided by the Ambient Wavenumber
        # Temporary_Variable = (Wavenumber - Initial_Peak_Position__Wavenumber) / Initial_Peak_Position__Wavenumber
        # Pressure = (A__Fitting_Constant) * (Temporary_Variable) * (1 + (((B__Fitting_Constant - 1) * (Temporary_Variable)) / 2))
    # Subtract Pressure from both sides to set the equation equal to zero
        # 0 = (A__Fitting_Constant) * (Temporary_Variable) * (1 + (((B__Fitting_Constant - 1) * (Temporary_Variable)) / 2)) - Pressure
    # Rearrange into standard form of a quadratic equation
        # 0 = - Pressure + (A__Fitting_Constant * Temperary_Variable) + ((A__Fitting_Constant * (B__Fitting_Constant - 1) * (Temperary_Variable ** 2)) / 2)
    # Now we can use the quadratic formula to solve for the Temperary_Variable
        # 0 = c + bx + ax^2
            # c = - Pressure
            # b = A__Fitting_Constant
            # a = (A__Fitting_Constant * (B__Fitting_Constant - 1)) / 2
        # x = (-b ± sqrt(b^2 - 4ac)) / (2a)
            # We want to solve for the Temperary_Variable
        # Temporary_Variable = (-A__Fitting_Constand ± sqrt((A__Fitting_Constant ** 2) - (4 * ((A__Fitting_Constant * (B__Fitting_Constant - 1)) / 2) * (- Pressure)))) / (2 * ((A__Fitting_Constant * (B__Fitting_Constant - 1)) / 2))
    # We want to use the positive root of the quadratic formula
        # If we used the negative root then the wavenumber would be negative
    # First we should check if we can make a simplification
        # If the a term from the quadratic formula is essensially zero then the quadratic term zeros out and the equation becomes linear
        # So the Temperary_Variable would be equal to the Pressure divided by the A_Fitting_Constant
    if abs((A__Fitting_Constant * (B__Fitting_Constant - 1)) / 2) < 1e-6:
        Temporary_Variable = Pressure / A__Fitting_Constant
    # Otherwise we can use the quadratic formula to solve for the Temperary_Variable
    else:
        # Check if the inside of the square root is negative
            # If it is negative then there are no real roots and we cannot solve for the wavenumber
        if (A__Fitting_Constant ** 2) - (4 * ((A__Fitting_Constant * (B__Fitting_Constant - 1)) / 2) * (- Pressure)) < 0:
            return None
        # Solve for the positive root
        Temperary_Variable = (-A__Fitting_Constant + np.sqrt((A__Fitting_Constant ** 2) - (4 * ((A__Fitting_Constant * (B__Fitting_Constant - 1)) / 2) * (- Pressure)))) / (2 * ((A__Fitting_Constant * (B__Fitting_Constant - 1)) / 2))
    # Now we can substitute back in for the Temperary_Variable to solve for the Wavenumber
        # Temporary_Variable = (Wavenumber - Initial_Peak_Position__Wavenumber) / Initial_Peak_Position__Wavenumber
        # Temporary_Variable * Initial_Peak_Position__Wavenumber = Wavenumber - Initial_Peak_Position__Wavenumber
        # Wavenumber = (Temperary_Variable * Initial_Peak_Position__Wavenumber) + Initial_Peak_Position__Wavenumber
    Wavenumber = (Temperary_Variable * Initial_Peak_Position__Wavenumber) + Initial_Peak_Position__Wavenumber

    return Wavenumber



####################
# Akahama and Kawamura, 2010 - Diamond

    # P(υ, if < 200 GPa) = K₀ · (υ-υ₀)/υ₀ · (1 + (K₀′-1)/2 · (υ-υ₀)/υ₀)
    # P(υ, if ≥ 200 GPa) = C - D·υ + E·υ²
####################


# Calculate pressure from a wavenumber
def Akahama_and_Kawamura_2010__Diamond__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant,
    C__Fitting_Constant,
    D__Fitting_Constant,
    E__Fitting_Constant):

    # Akahama and Kawamura, 2010 - Diamond
        # there are two equations created to adjust for the divergence that occurs around 200 GPa
            # The first equation is for pressures below 200 GPa and uses the Akahama and Kawaura, 2006 Diamond Finite Strain Approximation equation
            # Akahama and Kawamura, 2010 state once the first equation produces a pressure greater than 200 GPa then the second equation should be used
            # The two equations intersect near ~171 GPa and ~251 GPa
        # Note: There is an inherent ~2.5 GPa discontinuity at the transition due to the separate calibration of the two equations. 

    # Below 200 GPa Equation
        # Call the Akahama and Kawamura, 2006 Diamond Finite Strain Approximation equation
            # A__Fitting_Constant = K0
            # B__Fitting_Constant = First_Pressure_Derivative_of_Bulk
    def Akahama_and_Kawamura_2010__Diamond__Below_200_GPa__Equation(Wavenumber):
            return Akahama_and_Kawamura_2006__Diamond__Finite_Strain_Approximation__Calculate_Pressure_From_A_Wavenumber(Wavenumber, Initial_Peak_Position__Wavenumber, A__Fitting_Constant, B__Fitting_Constant)
    # Above 200 GPa Equation
    def Akahama_and_Kawamura_2010__Diamond__Above_200_GPa__Equation(Wavenumber):
        return (C__Fitting_Constant - (D__Fitting_Constant * Wavenumber) + (E__Fitting_Constant * (Wavenumber ** 2)))

    # Solve for pressure using the below 200 GPa equation
    Pressure_Value_Check = Akahama_and_Kawamura_2010__Diamond__Below_200_GPa__Equation(Wavenumber)
    # Check if the presser is less than 200 GPa
    if Pressure_Value_Check < 200:
        # The pressure is less than 200 GPa so we can use the below 200 GPa equation
        Pressure = Akahama_and_Kawamura_2010__Diamond__Below_200_GPa__Equation(Wavenumber)
        return Pressure
    # Otherwise the pressure is greater than 200 GPa so we can use the above 200 GPa equation
    elif Pressure_Value_Check >= 200:
        # The pressure is greater than 200 GPa so we can use the above 200 GPa equation
        Pressure = Akahama_and_Kawamura_2010__Diamond__Above_200_GPa__Equation(Wavenumber)
        return Pressure
    # If we cannot determine if the pressure is above or below 200 GPa then we cannot solve for the pressure
    else:
        return None

# Calculate wavenumber from a pressure
def Akahama_and_Kawamura_2010__Diamond__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant,
    C__Fitting_Constant,
    D__Fitting_Constant,
    E__Fitting_Constant):

    # The Akahama and Kawamura, 2010 Diamond equations cannot be rearranged to isolate the wavenumber because the wavenumber appears in multiple terms with different fractional powers
        # So instead we can use an iterative solver to find the wavenumber for a given pressure
            # Note: The above 200 GPa equation is a quadratic equation so we could use the quadratic formula to solve for the wavenumber but it is easier to just use an iterative solver that can solve for both equations

    # Call the Akahama and Kawamura, 2010 Diamond equations
    def Akahama_and_Kawamura_2010__Diamond__Equation(Wavenumber):
        return Akahama_and_Kawamura_2010__Diamond__Calculate_Pressure_From_A_Wavenumber(Wavenumber, Initial_Peak_Position__Wavenumber, A__Fitting_Constant, B__Fitting_Constant, C__Fitting_Constant, D__Fitting_Constant, E__Fitting_Constant) - Pressure
    
    # Use Brent's method to solve for the wavenumber
    try:
        Equation = Akahama_and_Kawamura_2010__Diamond__Equation
            # The wavenumber should be between the ambient wavenumber and 250% the ambient wavenumber
        Bracket = [Initial_Peak_Position__Wavenumber, 2.5 * Initial_Peak_Position__Wavenumber]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for the wavenumber
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        # Try a wider bracket
        try:
            Equation = Akahama_and_Kawamura_2010__Diamond__Equation
                # The wavenumber should be between 90% and 300% the ambient wavenumber
            Bracket = [0.9 * Initial_Peak_Position__Wavenumber, 3.0 * Initial_Peak_Position__Wavenumber]
                # Use the inverse quadratic interpolation of Brent's method
            Method = 'brentq'
            # Use scipy to solve for the wavenumber
            Solution = root_scalar(Equation, bracket=Bracket, method=Method)
            if Solution.converged:
                return Solution.root
            else:
                return None
        except ValueError:
            return None



####################
# Eremets et al., 2023 - Diamond

    # P(υ) = A·(υ-υ₀)/υ₀ + B·((υ-υ₀)/υ₀)²
####################


# Calculate pressure from a wavenumber
def Eremets_et_al_2023__Diamond__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Eremets et al., 2023 - Diamond
        # Akahama and Kawamura, 2006
            # same formula but with different A and B fitting constants
    Pressure = (A__Fitting_Constant * ((Wavenumber - Initial_Peak_Position__Wavenumber) / Initial_Peak_Position__Wavenumber)) + (B__Fitting_Constant * (((Wavenumber - Initial_Peak_Position__Wavenumber) / Initial_Peak_Position__Wavenumber) ** 2))

    return Pressure

# Calculate wavenumber from a pressure
def Eremets_et_al_2023__Diamond__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # The Eremets et al., 2023 Diamond cannot be rearranged to isolate the wavenumber because the wavenumber appears in multiple terms with different fractional powers
        # So instead we can use an iterative solver to find the wavenumber for a given pressure
            # Note: The equation is a quadratic equation so we could use the quadratic formula to solve for the wavenumber but it is easier to just use an iterative solver

    # Call the Eremets et al., 2023 Diamond equation
    def Eremets_et_al_2023__Diamond__Equation(Wavenumber):
        return Eremets_et_al_2023__Diamond__Calculate_Pressure_From_A_Wavenumber(Wavenumber, Initial_Peak_Position__Wavenumber, A__Fitting_Constant, B__Fitting_Constant) - Pressure
    
    # Use Brent's method to solve for the wavenumber
    try:
        Equation = Eremets_et_al_2023__Diamond__Equation
            # The wavenumber should be between 95% and 200% the ambient wavenumber
        Bracket = [0.95 * Initial_Peak_Position__Wavenumber, 2 * Initial_Peak_Position__Wavenumber]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for the wavenumber
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        return None



####################
# Linear Scale

    # P(λ) = (λ - λ₀) / A
####################

# Calculate pressure from a wavenumber
def Linear_Scale__Raman__Calculate_Pressure_from_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    Slope_Of_Peak_Position_Change_With_Pressure):

    # Linear Scale
        # Historically used in initial ruby fluourescence studies
        # Commonly used for materials that do not require higher order expansions
    Pressure = (Wavenumber - Initial_Peak_Position__Wavenumber) / Slope_Of_Peak_Position_Change_With_Pressure

    return Pressure

# Calculate wavenumber from a pressure
def Linear_Scale__Raman__Calculate_Wavenumber_from_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    Slope_Of_Peak_Position_Change_With_Pressure):

    # Start with the equation for calculating pressure from a wavenumber and rearrange to calculate wavenumber
        # Pressure = (Wavenumber - Initial_Peak_Position__Wavenumber) / Slope_Of_Peak_Position_Change_With_Pressure
    # Multiply both sides by Slope_Of_Peak_Position_Change_With_Pressure
        # Pressure * Slope_Of_Peak_Position_Change_With_Pressure = Wavenumber - Initial_Peak_Position__Wavenumber
    # Add Initial_Peak_Position__Wavenumber to both sides
        # Pressure * Slope_Of_Peak_Position_Change_With_Pressure + Initial_Peak_Position__Wavenumber = Wavenumber
    Wavenumber = (Pressure * Slope_Of_Peak_Position_Change_With_Pressure) + Initial_Peak_Position__Wavenumber

    return Wavenumber



########################################
# Study Specific
########################################



####################
# Evans et al., 2005 - Beryllium - Polynomial

    # υ(P) = A + B·P + C·P²
####################

# Calculate pressure from a wavenumber
def Evans_et_al_2005__Beryllium__Polynomial__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant,
    C__Fitting_Constant):

    # Start with the equation for calculating wavenumber from a pressure and rearrange to calculate pressure
        # Wavenumber = A__Fitting_Constant + (B__Fitting_Constant * Pressure) + (C__Fitting_Constant * (Pressure ** 2))
    # Subtract wavenumber from both sides to set the equation equal to zero
        # 0 = A__Fitting_Constant + (B__Fitting_Constant * Pressure) + (C__Fitting_Constant * (Pressure ** 2)) - Wavenumber
    # Rearrange into standard form of a quadratic equation
        # 0 = - Wavenumber + A__Fitting_Constant + (B__Fitting_Constant * Pressure) + (C__Fitting_Constant * (Pressure ** 2))
    # Now we can use the quadratic formula to solve for the Pressure
        # 0 = c + bx + ax^2
            # c = - Wavenumber + A__Fitting_Constant
            # b = B__Fitting_Constant
            # a = C__Fitting_Constant
        # x = (-b ± sqrt(b^2 - 4ac)) / (2a)
            # We want to solve for the Pressure
        # Pressure = (-B__Fitting_Constant ± sqrt((B__Fitting_Constant ** 2) - (4 * C__Fitting_Constant * (- Wavenumber + A__Fitting_Constant)))) / (2 * C__Fitting_Constant)
    # We want to use the positive root of the quadratic formula
        # If we used the negative root then the pressures would be negative
    # Check if the inside of the square root is negative
        # If it is negative then there are no real roots and we cannot solve for the pressure
    if ((B__Fitting_Constant ** 2) - (4 * C__Fitting_Constant * (- Wavenumber + A__Fitting_Constant))) < 0:
        raise ValueError("The inside of the square root is negative. There are no real roots and we cannot solve for the pressure.")
    # Now we can solve for the positive root
    Pressure = (-B__Fitting_Constant + np.sqrt((B__Fitting_Constant ** 2) - (4 * C__Fitting_Constant * (- Wavenumber + A__Fitting_Constant)))) / (2 * C__Fitting_Constant)

    return Pressure


# Calculate wavenumber from a pressure
def Evans_et_al_2005__Beryllium__Polynomial__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    A__Fitting_Constant,
    B__Fitting_Constant,
    C__Fitting_Constant):

    # Evans et al., 2005 - Beryllium - Polynomial
    Wavenumber = A__Fitting_Constant + (B__Fitting_Constant * Pressure) + (C__Fitting_Constant * (Pressure ** 2))

    return Wavenumber



####################
# Olijnyk et al., 2001 - Beryllium and Rhenium - Polynomial

    # υ(P) = υ₀ · (1 - B/A · P)^(-A²/B)
    # P(υ) = A/B · (1 - (υ/υ₀)^(-B/A²))
####################


# Calculate pressure from a wavenumber
def Olijnyk_et_al_2001__Beryllium_and_Rhenium__Polynomial__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Olijnyk et al., 2001 - Beryllium and Rhenium - Polynomial
    Pressure = (A__Fitting_Constant / B__Fitting_Constant) * (1 - ((Wavenumber / Initial_Peak_Position__Wavenumber) ** (- (B__Fitting_Constant / (A__Fitting_Constant ** 2)))))

    return Pressure


# Calculate wavenumber from a pressure
def Olijnyk_et_al_2001__Beryllium_and_Rhenium__Polynomial__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Olijnyk et al., 2001 - Beryllium and Rhenium - Polynomial
    Wavenumber = (Initial_Peak_Position__Wavenumber) * ((1 - ((B__Fitting_Constant / A__Fitting_Constant) * Pressure)) ** (- ((A__Fitting_Constant ** 2) / B__Fitting_Constant)))

    return Wavenumber



####################
# Pease et al., 2025 - Rhenium - Polynomial

    # P(υ) = A·(υ-υ₀) + B·(υ-υ₀)²
####################


# Calculate pressure from a wavenumber
def Pease_et_al_2025__Rhenium__Polynomial__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Pease et al., 2025 - Rhenium - Polynomial
    Pressure = (A__Fitting_Constant * (Wavenumber - Initial_Peak_Position__Wavenumber)) + (B__Fitting_Constant * ((Wavenumber - Initial_Peak_Position__Wavenumber) ** 2))

    return Pressure


# Calculate wavenumber from a pressure
def Pease_et_al_2025__Rhenium__Polynomial__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Start with the equation for calculating pressure from a wavenumber and rearrange to calculate wavenumber
        # Pressure = (A__Fitting_Constant * (Wavenumber - Initial_Peak_Position__Wavenumber)) + (B__Fitting_Constant * ((Wavenumber - Initial_Peak_Position__Wavenumber) ** 2))
    # Now substitute a temperary variable for the Wavenumber minus the Ambient Wavenumber
        # Temporary_Variable = Wavenumber - Initial_Peak_Position__Wavenumber
        # Pressure = (A__Fitting_Constant * Temporary_Variable) + (B__Fitting_Constant * (Temporary_Variable ** 2))
    # Subtract Pressure from both sides to set the equation equal to zero
        # 0 = (A__Fitting_Constant * Temporary_Variable) + (B__Fitting_Constant * (Temporary_Variable ** 2)) - Pressure
    # Rearrange into standard form of a quadratic equation
        # 0 = - Pressure + (A__Fitting_Constant * Temporary_Variable) + (B__Fitting_Constant * (Temporary_Variable ** 2))
    # Now we can use the quadratic formula to solve for the Temporary_Variable
        # 0 = c + bx + ax^2
            # c = - Pressure
            # b = A__Fitting_Constant
            # a = B__Fitting_Constant
        # x = (-b ± sqrt(b^2 - 4ac)) / (2a)
            # We want to solve for the Temporary_Variable
        # Temporary_Variable = (-A__Fitting_Constant ± sqrt((A__Fitting_Constant ** 2) - (4 * B__Fitting_Constant * (- Pressure)))) / (2 * B__Fitting_Constant)
    # We want to use the positive root of the quadratic formula
        # If we used the negative root then the wavenumber would be negative
    # Check if the inside of the square root is negative
        # If it is negative then there are no real roots and we cannot solve for the wavenumber
    if ((A__Fitting_Constant ** 2) - (4 * B__Fitting_Constant * (- Pressure))) < 0:
        raise ValueError("The inside of the square root is negative. There are no real roots and we cannot solve for the wavenumber.")  
    # Now we can solve for the positive root
    Temporary_Variable = (-A__Fitting_Constant + np.sqrt((A__Fitting_Constant ** 2) - (4 * B__Fitting_Constant * (- Pressure)))) / (2 * B__Fitting_Constant)
    # Now we can substitute back in for the Temporary_Variable to solve for the Wavenumber
        # Temporary_Variable = Wavenumber - Initial_Peak_Position__Wavenumber
        # Wavenumber = Temporary_Variable + Initial_Peak_Position__Wavenumber
    Wavenumber = Temporary_Variable + Initial_Peak_Position__Wavenumber

    return Wavenumber



####################
# Goncharov et al., 2005 - Cubic Boron Nitride

    # P(υ) = A/B · ((υ/υ₀)^B - 1)
####################


# Calculate pressure from a wavenumber
def Goncharov_et_al_2005__Cubic_Boron_Nitride__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Goncharov et al., 2005 - Cubic Boron Nitride
    Pressure = (A__Fitting_Constant / B__Fitting_Constant) * (((Wavenumber / Initial_Peak_Position__Wavenumber) ** B__Fitting_Constant) - 1)

    return Pressure


# Calculate wavenumber from a pressure
def Goncharov_et_al_2005__Cubic_Boron_Nitride__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # The Goncharov et al., 2005 Cubic Boron Nitride equation could be rearranged to solve for wavenumber but it is easier to just use an iterative solver to find the wavenumber for a given pressure

    # Call the Goncharov et al., 2005 Cubic Boron Nitride equation
    def Goncharov_et_al_2005__Cubic_Boron_Nitride__Equation(Wavenumber):
        return Goncharov_et_al_2005__Cubic_Boron_Nitride__Calculate_Pressure_From_A_Wavenumber(Wavenumber, Initial_Peak_Position__Wavenumber, A__Fitting_Constant, B__Fitting_Constant) - Pressure
    
    # Use Brent's method to solve for the wavenumber
    try:
        Equation = Goncharov_et_al_2005__Cubic_Boron_Nitride__Equation
            # The wavenumber should be between 95% and 200% the ambient wavenumber
        Bracket = [0.95 * Initial_Peak_Position__Wavenumber, 2 * Initial_Peak_Position__Wavenumber]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for the wavenumber
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        return None



####################
# Datchi and Canny, 2004; Ono et al., 2015; Ren et al., 2023 - Cubic Boron Nitride
####################


##########
# Datchi and Canny, 2004 - Cubic Boron Nitride

    # υ(P,T) = υ₀ + A·T + B·T² + (C + D·T + E·T²)·P + F·P²
##########

# Calculate pressure from a wavenumber
def Datchi_and_Canny_2004__Cubic_Boron_Nitride__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    Temperature_Dependence,
    A__Fitting_Constant,
    B__Fitting_Constant,
    C__Fitting_Constant,
    D__Fitting_Constant,
    E__Fitting_Constant,
    F__Fitting_Constant):

    # The Datchi and Canny, 2004 Cubic Boron Nitride equation cannot be rearranged to isolate the wavenumber because the wavenumber appears in multiple terms with different fractional powers
        # So instead we can use an iterative solver to find the wavenumber for a given

    # Call the Datchi and Canny, 2004 Cubic Boron Nitride equation
    def Datchi_and_Canny_2004__Cubic_Boron_Nitride__Equation(Pressure):
        return Datchi_and_Canny_2004__Cubic_Boron_Nitride__Calculate_Wavenumber_From_A_Pressure(Pressure, Initial_Peak_Position__Wavenumber, Temperature_Dependence, A__Fitting_Constant, B__Fitting_Constant, C__Fitting_Constant, D__Fitting_Constant, E__Fitting_Constant, F__Fitting_Constant) - Wavenumber
    
    # Use Brent's method to solve for the wavenumber
    try:
        Equation = Datchi_and_Canny_2004__Cubic_Boron_Nitride__Equation
            # The wavenumber should be between 0 and 150
        Bracket = [0, 150]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for the wavenumber
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        # Try a wider bracket
        try:
            Equation = Datchi_and_Canny_2004__Cubic_Boron_Nitride__Equation
                # The wavenumber should be between -20 and 150
            Bracket = [-20, 150]
                # Use the inverse quadratic interpolation of Brent's method
            Method = 'brentq'
            # Use scipy to solve for the wavenumber
            Solution = root_scalar(Equation, bracket=Bracket, method=Method)
            if Solution.converged:
                return Solution.root
            else:
                return None
        except ValueError:
            return None


# Calculate wavenumber from a pressure
def Datchi_and_Canny_2004__Cubic_Boron_Nitride__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    Temperature_Dependence,
    A__Fitting_Constant,
    B__Fitting_Constant,
    C__Fitting_Constant,
    D__Fitting_Constant,
    E__Fitting_Constant,
    F__Fitting_Constant):

    # Note:
        # Temperature_Dependence is assumed to be ~ room temperature (300 K)
    Temperature_Dependence = 300

    # Datchi and Canny, 2004 - Cubic Boron Nitride
        # fitted constants are directly related to the P-V-T equation of state from Datchi and Canny, 2004
        # Temperature_Dependence is assumed to be ~ room temperature (300 K)
    Wavenumber = Initial_Peak_Position__Wavenumber + (A__Fitting_Constant * Temperature_Dependence) + (B__Fitting_Constant * (Temperature_Dependence ** 2)) + ((C__Fitting_Constant + (D__Fitting_Constant * Temperature_Dependence) + (E__Fitting_Constant * (Temperature_Dependence ** 2))) * Pressure) + (F__Fitting_Constant * (Pressure ** 2))

    return Wavenumber


##########
# Ren et al., 2023 - Cubic Boron Nitride

    # υ(P) = υ₀ + A·P + B·P²
##########

# Calculate pressure from a wavenumber
def Ren_et_al_2023__Cubic_Boron_Nitride__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # The Ren et al., 2023 Cubic Boron Nitride equation could be rearranged to solve for wavenumber but it is easier to just use an iterative solver to find the wavenumber for a given pressure

    # Call the Ren et al., 2023 Cubic Boron Nitride equation
    def Ren_et_al_2023__Cubic_Boron_Nitride__Equation(Pressure):
        return Ren_et_al_2023__Cubic_Boron_Nitride__Calculate_Wavenumber_From_A_Pressure(Pressure, Initial_Peak_Position__Wavenumber, A__Fitting_Constant, B__Fitting_Constant) - Wavenumber
    
    # Use Brent's method to solve for the wavenumber
    try:
        Equation = Ren_et_al_2023__Cubic_Boron_Nitride__Equation
            # The wavenumber should be between 0 and 200
        Bracket = [0, 200]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for the wavenumber
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        # Try a wider bracket
        try:
            Equation = Ren_et_al_2023__Cubic_Boron_Nitride__Equation
                # The wavenumber should be between -20 and 200
            Bracket = [-20, 200]
                # Use the inverse quadratic interpolation of Brent's method
            Method = 'brentq'
            # Use scipy to solve for the wavenumber
            Solution = root_scalar(Equation, bracket=Bracket, method=Method)
            if Solution.converged:
                return Solution.root
            else:
                return None
        except ValueError:
            return None


# Calculate wavenumber from a pressure
def Ren_et_al_2023__Cubic_Boron_Nitride__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant,
    B__Fitting_Constant):

    # Ren et al., 2023 - Cubic Boron Nitride
    Wavenumber = Initial_Peak_Position__Wavenumber + (A__Fitting_Constant * Pressure) + (B__Fitting_Constant * (Pressure ** 2))

    return Wavenumber



####################
# Datchi et al., 2007 - Cubic Boron Nitride

    # P(υ) = A/3.62 · ((υ/υ₀)^2.876 - 1)
####################


# Calculate pressure from a wavenumber
def Datchi_et_al_2007__Cubic_Boron_Nitride__Calculate_Pressure_From_A_Wavenumber(
    Wavenumber,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant):

    # Note:
        # First_Pressure_Derivative_of_Bulk_Modulus = 3.62
        # gamma = First_Pressure_Derivative_of_Bulk_Modulus divided by 2.876 = 3.62 / 2.876 = 1.257
        # A__Fitting_Constant = K0

    # Datchi et al., 2007 - Cubic Boron Nitride
    First_Pressure_Derivative_of_Bulk_Modulus = 3.62
    gamma = 1.257
    First_Pressure_Derivative_of_Bulk_Modulus_Divided_By_gamma = 2.876

    Pressure = (A__Fitting_Constant / First_Pressure_Derivative_of_Bulk_Modulus) * (((Wavenumber / Initial_Peak_Position__Wavenumber) ** (First_Pressure_Derivative_of_Bulk_Modulus_Divided_By_gamma)) - 1)

    return Pressure


# Calculate wavenumber from a pressure
def Datchi_et_al_2007__Cubic_Boron_Nitride__Calculate_Wavenumber_From_A_Pressure(
    Pressure,
    Initial_Peak_Position__Wavenumber,
    A__Fitting_Constant):

    # Note:
        # First_Pressure_Derivative_of_Bulk_Modulus = 3.62
        # gamma = First_Pressure_Derivative_of_Bulk_Modulus divided by 2.876 = 3.62 / 2.876 = 1.257
        # A__Fitting_Constant = K0

    # The Datchi et al., 2007 Cubic Boron Nitride equation could be rearranged to solve for wavenumber but it is easier to just use an iterative solver to find the wavenumber for a given pressure

    # Call the Datchi et al., 2007 Cubic Boron Nitride equation
    def Datchi_et_al_2007__Cubic_Boron_Nitride__Equation(Wavenumber):
        return Datchi_et_al_2007__Cubic_Boron_Nitride__Calculate_Pressure_From_A_Wavenumber(Wavenumber, Initial_Peak_Position__Wavenumber, A__Fitting_Constant) - Pressure
    
    # Use Brent's method to solve for the wavenumber
    try:
        Equation = Datchi_et_al_2007__Cubic_Boron_Nitride__Equation
            # The wavenumber should be between 95% and 200% the ambient wavenumber
        Bracket = [0.95 * Initial_Peak_Position__Wavenumber, 2 * Initial_Peak_Position__Wavenumber]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for the wavenumber
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        return None




