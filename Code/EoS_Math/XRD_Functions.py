# Load libraries
    # Load statistics libraries
import numpy as np
    # Load third party libraries
from scipy.optimize import root_scalar
from scipy.optimize import brentq
from scipy.optimize import newton





# XRD Functions
    # Grouped by the type of equation of state and order
        # Murnaghan
            # First-Order
            # Second-Order
        # Birch-Murnaghan
            # Second-Order
            # Third-Order
            # Fourth-Order
        # Rydberg-Vinet
            # Third-Order
            # Extended
        # Adapted Polynomial
        # Keane
        # Rydberg-Stacey





########################################
# Murnaghan
########################################

####################
# First-Order

    # P(V) = K₀/K₀′ · ((V₀/V)^K₀′ - 1)
####################


# Calculate pressure from a volume
def Murnaghan__First_Order__Calculate_Pressure_From_Input_Volume(
    Volume, 
    Initial_Volume__Angstroms_Per_Unit_Cell, 
    K0, 
    K0_Prime, 
    Initial_Pressure=0):

    # First-Order Murnaghan Equation of State
        # Murnaghan, 1937
    Pressure = ( K0 / K0_Prime ) * ( ( Initial_Volume__Angstroms_Per_Unit_Cell / Volume ) ** K0_Prime - 1 ) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Murnaghan__First_Order__Calculate_Volume_From_Input_Pressure(
    Pressure, 
    Initial_Volume__Angstroms_Per_Unit_Cell, 
    K0, 
    K0_Prime, 
    Initial_Pressure=0):

    # Start with the equation for calculating pressure from a volume and rearrange it to solve for volume
        # Pressure = ( K0 / K0_Prime ) * ( ( Initial_Volume__Angstroms_Per_Unit_Cell / Volume ) ** K0_Prime - 1 ) + Initial_Pressure
    # subtract the initial pressure from both sides
        # Pressure - Initial_Pressure = ( K0 / K0_Prime ) * ( ( Initial_Volume__Angstroms_Per_Unit_Cell / Volume ) ** K0_Prime - 1 )
    # divide both sides by (K0 / K0_Prime)
        # equivalently, multiply both sides by (K0_Prime / K0)
        # (Pressure - Initial_Pressure) * (K0_Prime / K0) = (Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** K0_Prime - 1
    # add 1 to both sides
        # 1 + (Pressure - Initial_Pressure) * (K0_Prime / K0) = (Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** K0_Prime
    # check that the left hand side of the equation is greater than 0
    Left_Hand_Side_of_the_Equation = 1 + (Pressure - Initial_Pressure) * (K0_Prime / K0)
    if Left_Hand_Side_of_the_Equation <= 0:
        # The result is not valid
        return None
    # raise both sides to the power of the inverse of the first pressure derivative of the Initial Bulk Modulus
        # Left_Hand_Side_of_the_Equation ** (1 / K0_Prime) = Initial_Volume__Angstroms_Per_Unit_Cell / Volume
    # take the reciprocal of both sides
        # (1 / (Left_Hand_Side_of_the_Equation ** (1 / K0_Prime))) = Volume / Initial_Volume__Angstroms_Per_Unit_Cell
    # multiply both sides by the initial volume
    Volume = (Initial_Volume__Angstroms_Per_Unit_Cell / (Left_Hand_Side_of_the_Equation ** (1 / K0_Prime)))

    return Volume


####################
# Second-Order

    # q = √(K₀′² - 2K₀K₀″)
    # P(V) = 2K₀ · ((V₀/V)^q - 1) / (q·((V₀/V)^q + 1) - K₀′·((V₀/V)^q - 1))
####################

# Calculate pressure from a volume
def Murnaghan__Second_Order__Calculate_Pressure_From_Input_Volume(
    Volume, 
    Initial_Volume__Angstroms_Per_Unit_Cell, 
    K0, 
    K0_Prime, 
    K0_Double_Prime, 
    Initial_Pressure=0):

    # Second-Order Murnaghan Equation of State
        # Finger et al., 1981
    q = np.sqrt((K0_Prime ** 2) - (2 * K0 * K0_Double_Prime))

    Pressure = 2 * K0 * ((((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** q) - 1) / (q * ((((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** q) + 1)) - K0_Prime * ((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** q - 1))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Murnaghan__Second_Order__Calculate_Volume_From_Input_Pressure(
    Pressure, 
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    K0_Double_Prime,
    Initial_Pressure=0):

    # The Second-Order Murnaghan equation cannot be rearranged to isolate Volume because Volume is in the numerator and denominator
        # So instead we can use an iterative solver to find Volume

    # Call the Second-Order Murnaghan equation
    def Second_Order_Murnaghan_Equation(Volume):
        return Murnaghan__Second_Order__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, K0_Double_Prime, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Second_Order_Murnaghan_Equation
            # The Volume should be between 30% and 150% of the Initial Volume
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.5 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        # Try a wider bracket
        try:
            Equation = Second_Order_Murnaghan_Equation
                # The Volume should be between 1% and 300% of the Initial Volume
            Bracket = [0.01 * Initial_Volume__Angstroms_Per_Unit_Cell, 3 * Initial_Volume__Angstroms_Per_Unit_Cell]
                # Use the inverse quadratic interpolation of Brent's method
            Method = 'brentq'
            # Use scipy to solve for Volume
            Solution = root_scalar(Equation, bracket=Bracket, method=Method)
            if Solution.converged:
                return Solution.root
            else:
                return None
        except ValueError:
            return None



########################################
# Birch-Murnaghan
########################################

####################
# Second-Order

    # P(V) = ³⁄₂ K₀ · ((V₀/V)^⁷⁄₃ - (V₀/V)^⁵⁄₃)
####################

# Calculate pressure from a volume
def Birch_Murnaghan__Second_Order__Calculate_Pressure_From_Input_Volume(
    Volume, 
    Initial_Volume__Angstroms_Per_Unit_Cell, 
    K0, 
    Initial_Pressure=0):

    # Second-Order Birch-Murnaghan Equation of State
        # Birch, 1947
    Pressure = (3 / 2) * K0 * (((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (7/3)) - ((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (5/3))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Birch_Murnaghan__Second_Order__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    Initial_Pressure=0):

    # The Second-Order Birch-Murnaghan equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers
        # So instead we can use an iterative solver to find Volume

    # Call the Second-Order Birch-Murnaghan equation
    def Second_Order_Birch_Murnaghan_Equation(Volume):
        return Birch_Murnaghan__Second_Order__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Second_Order_Birch_Murnaghan_Equation
            # The Volume should be between 30% and 150% of the Initial Volume
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.5 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        # Try a wider bracket
        try:
            Equation = Second_Order_Birch_Murnaghan_Equation
                # The Volume should be between 1% and 300% of the Initial Volume
            Bracket = [0.01 * Initial_Volume__Angstroms_Per_Unit_Cell, 3 * Initial_Volume__Angstroms_Per_Unit_Cell]
                # Use the inverse quadratic interpolation of Brent's method
            Method = 'brentq'
            # Use scipy to solve for Volume
            Solution = root_scalar(Equation, bracket=Bracket, method=Method)
            if Solution.converged:
                return Solution.root
            else:
                return None
        except ValueError:
            return None


####################
# Third-Order

    # P(V) = ³⁄₂ K₀ · ((V₀/V)^⁷⁄₃ - (V₀/V)^⁵⁄₃) · (1 + ¾(K₀′-4)·((V₀/V)^²⁄₃ - 1))
####################

# Calculate pressure from a volume
def Birch_Murnaghan__Third_Order__Calculate_Pressure_From_Input_Volume(
    Volume, 
    Initial_Volume__Angstroms_Per_Unit_Cell, 
    K0, 
    K0_Prime, 
    Initial_Pressure=0):

    # Third-Order Birch-Murnaghan Equation of State
        # Birch, 1947
    Pressure = (3 / 2) * K0 * ((((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (7/3)) - ((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (5/3))) * (1 + (3 / 4) * (K0_Prime - 4) * (((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (2 / 3)) - 1))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Birch_Murnaghan__Third_Order__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Initial_Pressure=0):

    # The Third-Order Birch-Murnaghan equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers
        # So instead we can use an iterative solver to find Volume

    # Call the Third-Order Birch-Murnaghan equation
    def Third_Order_Birch_Murnaghan_Equation(Volume):
        return Birch_Murnaghan__Third_Order__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Third_Order_Birch_Murnaghan_Equation
            # The Volume should be between 30% and 150% of the Initial Volume
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.5 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        # Try a wider bracket
        try:
            Equation = Third_Order_Birch_Murnaghan_Equation
                # The Volume should be between 1% and 300% of the Initial Volume
            Bracket = [0.01 * Initial_Volume__Angstroms_Per_Unit_Cell, 3 * Initial_Volume__Angstroms_Per_Unit_Cell]
                # Use the inverse quadratic interpolation of Brent's method
            Method = 'brentq'
            # Use scipy to solve for Volume
            Solution = root_scalar(Equation, bracket=Bracket, method=Method)
            if Solution.converged:
                return Solution.root
            else:
                return None
        except ValueError:
            return None


####################
# Fourth-Order

    # P(V) = ³⁄₂ K₀ · ((V₀/V)^⁷⁄₃ - (V₀/V)^⁵⁄₃) · (1 + ¾(K₀′-4)·((V₀/V)^²⁄₃-1) + ³⁄₈(K₀K₀″+(K₀′-4)(K₀′-3)+³⁵⁄₉)·((V₀/V)^²⁄₃-1)²)
####################

# Calculate pressure from a volume
def Birch_Murnaghan__Fourth_Order__Calculate_Pressure_From_Input_Volume(
    Volume, 
    Initial_Volume__Angstroms_Per_Unit_Cell, 
    K0, 
    K0_Prime, 
    K0_Double_Prime, 
    Initial_Pressure=0):

    # Fourth-Order Birch-Murnaghan Equation of State
        # Birch, 1947
    Pressure = (3 / 2) * K0 * (((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (7/3)) - ((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (5/3))) * (1 + (3 / 4) * (K0_Prime - 4) * (((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (2 / 3)) - 1) + (3 / 8) * (K0 * K0_Double_Prime + (K0_Prime - 4) * (K0_Prime - 3) + (35 / 9)) * ((((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (2 / 3)) - 1) ** 2)) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Birch_Murnaghan__Fourth_Order__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    K0_Double_Prime,
    Initial_Pressure=0):

    # The Fourth-Order Birch-Murnaghan equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers
        # So instead we can use an iterative solver to find Volume

    # Call the Fourth-Order Birch-Murnaghan equation
    def Fourth_Order_Birch_Murnaghan_Equation(Volume):
        return Birch_Murnaghan__Fourth_Order__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, K0_Double_Prime, Initial_Pressure) - Pressure

    # Get a starting guess for the volume using the Third-Order Birch-Murnaghan equation
    try:
        Initial_Volume__Angstroms_Per_Unit_Cell_Guess = Birch_Murnaghan__Third_Order__Calculate_Volume_From_Input_Pressure(Pressure, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, Initial_Pressure)
        if Initial_Volume__Angstroms_Per_Unit_Cell_Guess is None:
            # The Third-Order solution failed
                # Try 80% of the initial volume as a guess
            Initial_Volume__Angstroms_Per_Unit_Cell_Guess = Initial_Volume__Angstroms_Per_Unit_Cell * 0.8
    except:
        Initial_Volume__Angstroms_Per_Unit_Cell_Guess = Initial_Volume__Angstroms_Per_Unit_Cell * 0.8
    # Use the Newton-Raphson method to solve for Volume starting from the Third-Order Birch-Murnaghan guess
    try:
        Solution = newton(Fourth_Order_Birch_Murnaghan_Equation, Initial_Volume__Angstroms_Per_Unit_Cell_Guess, tol=1e-10, maxiter=100)
        # Check that the volume is between 10% and 150% of the initial volume
        if 0.1 * Initial_Volume__Angstroms_Per_Unit_Cell < Solution < 1.5 * Initial_Volume__Angstroms_Per_Unit_Cell:
            if abs(Fourth_Order_Birch_Murnaghan_Equation(Solution)) < 1e-6:
                return Solution
    except:
        pass
    # If the Newton-Raphson method did not work use Brent's method to solve for Volume starting from the Third-Order Birch-Murnaghan guess
    if Initial_Volume__Angstroms_Per_Unit_Cell_Guess is not None and 0.1 * Initial_Volume__Angstroms_Per_Unit_Cell < Initial_Volume__Angstroms_Per_Unit_Cell_Guess < 1.5 * Initial_Volume__Angstroms_Per_Unit_Cell:
        # Set the lower bound to be between 10% and 90% of the initial volume
        Lower_Volume_Bound = max(0.1 * Initial_Volume__Angstroms_Per_Unit_Cell, Initial_Volume__Angstroms_Per_Unit_Cell_Guess * 0.9)
        # Set the upper bound to be between 110% and 150% of the initial volume
        Upper_Volume_Bound = min(1.5 * Initial_Volume__Angstroms_Per_Unit_Cell, Initial_Volume__Angstroms_Per_Unit_Cell_Guess * 1.1)
        try:
            if Fourth_Order_Birch_Murnaghan_Equation(Lower_Volume_Bound) * Fourth_Order_Birch_Murnaghan_Equation(Upper_Volume_Bound) < 0:
                Solution = brentq(Fourth_Order_Birch_Murnaghan_Equation, Lower_Volume_Bound, Upper_Volume_Bound)
                return Solution
        except:
            pass
    # If Brent's method did not work try scanning across the full physical volume range to find a valid bracket for the root
        # The volume should be between 30% and 120% of the Initial Volume
    Scan = np.linspace(0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.2 * Initial_Volume__Angstroms_Per_Unit_Cell, 100)
    Scan_Values = [Fourth_Order_Birch_Murnaghan_Equation(Volume) for Volume in Scan]
    for i in range(len(Scan_Values) - 1):
        if Scan_Values[i] * Scan_Values[i + 1] < 0:
            try:
                Solution = brentq(Fourth_Order_Birch_Murnaghan_Equation, Scan[i], Scan[i + 1])
                return Solution
            except:
                continue

    # No solution was found
    return None



########################################
# Rydberg-Vinet
########################################

####################
# Third-Order

    # P(V) = 3K₀ · (1-(V/V₀)^⅓) / (V/V₀)^²⁄₃ · e^(³⁄₂(K₀′-1)·(1-(V/V₀)^⅓))
####################

# Calculate pressure from a volume
def Rydberg_Vinet__Third_Order__Calculate_Pressure_From_Input_Volume(
    Volume,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Initial_Pressure=0):

    # Third-Order Rydberg-Vinet Equation of State
        # Vinet et al., 1987
    Pressure = (3 * K0 * ((1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3))) / ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (2 / 3))) * (np.e ** (1.5 * (K0_Prime - 1) * (1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3)))))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Rydberg_Vinet__Third_Order__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Initial_Pressure=0):

    # The Third-Order Rydberg-Vinet equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers
        # So instead we can use an iterative solver to find Volume

    # Call the Third-Order Rydberg-Vinet equation
    def Third_Order_Rydberg_Vinet_Equation(Volume):
        return Rydberg_Vinet__Third_Order__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Third_Order_Rydberg_Vinet_Equation
            # The Volume should be between 30% and 150% of the Initial Volume
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.5 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        # Try a wider bracket
        try:
            Equation = Third_Order_Rydberg_Vinet_Equation
                # The Volume should be between 1% and 300% of the Initial Volume
            Bracket = [0.01 * Initial_Volume__Angstroms_Per_Unit_Cell, 3 * Initial_Volume__Angstroms_Per_Unit_Cell]
                # Use the inverse quadratic interpolation of Brent's method
            Method = 'brentq'
            # Use scipy to solve for Volume
            Solution = root_scalar(Equation, bracket=Bracket, method=Method)
            if Solution.converged:
                return Solution.root
            else:
                return None
        except ValueError:
            return None


####################
# Extended

    # P(V) = 3K₀ · (1-(V/V₀)^⅓) / (V/V₀)^²⁄₃ · e^(η·(1-(V/V₀)^⅓) + β·(1-(V/V₀)^⅓)² + ψ·(1-(V/V₀)^⅓)³ + γ·(1-(V/V₀)^⅓)⁴)
####################

# Calculate pressure from a volume
def Rydberg_Vinet__Extended__Calculate_Pressure_From_Input_Volume(
    Volume,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    eta,
    beta,
    psi,
    gamma,
    Initial_Pressure=0):

    # Extended Rydberg-Vinet Equation of State
        # Vinet et al., 1987
    Pressure = (3 * K0 * ((1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3))) / ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (2 / 3))) * (np.e ** ((eta * (1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3)))) + (beta * ((1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3))) ** 2)) + (psi * ((1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3))) ** 3)) + (gamma * ((1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3))) ** 4)) ))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Rydberg_Vinet__Extended__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    eta,
    beta,
    psi,
    gamma,
    Initial_Pressure=0):

    # The Extended Rydberg-Vinet equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers and exponential functions
        # So instead we can use an iterative solver to find Volume

    # Call the Extended Rydberg-Vinet equation
    def Extended_Rydberg_Vinet_Equation(Volume):
        return Rydberg_Vinet__Extended__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, eta, beta, psi, gamma, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Extended_Rydberg_Vinet_Equation
            # The Volume should be between 30% and 150% of the Initial Volume
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.5 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        # Try a wider bracket
        try:
            Equation = Extended_Rydberg_Vinet_Equation
                # The Volume should be between 1% and 300% of the Initial Volume
            Bracket = [0.01 * Initial_Volume__Angstroms_Per_Unit_Cell, 3 * Initial_Volume__Angstroms_Per_Unit_Cell]
                # Use the inverse quadratic interpolation of Brent's method
            Method = 'brentq'
            # Use scipy to solve for Volume
            Solution = root_scalar(Equation, bracket=Bracket, method=Method)
            if Solution.converged:
                return Solution.root
            else:
                return None
        except ValueError:
            return None



########################################
# Adapted Polynomial

    # P(V) = 3K₀ · (1-(V/V₀)^⅓) / (V/V₀)^⁵⁄₃ · (1 + (³⁄₂(K₀′-3) + ln(3K₀/2337) + ⁵⁄₃·ln(V₀/Z)) · (V/V₀)^⅓ · (1-(V/V₀)^⅓)) · e^((-ln(3K₀/2337) - ⁵⁄₃·ln(V₀/Z))·(1-(V/V₀)^⅓))
########################################

# Calculate pressure from a volume
def Adapted_Polynomial__Calculate_Pressure_From_Input_Volume(
    Volume,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Atomic_Number,
    Initial_Pressure=0):

    Fermi_Gas_Parameter = 2337    # GPa 

    # Adapted Polynomial (Holzapfel) Equation of State
        # Holzapfel, 2002
    Pressure = (3 * K0 * ((1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3))) / ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (5 / 3))) * (1 + ((3 / 2) * (K0_Prime - 3) + (np.log((3 * K0) / (Fermi_Gas_Parameter))) + ((5 / 3) * (np.log(Initial_Volume__Angstroms_Per_Unit_Cell / Atomic_Number)))) * ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3)) * (1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3)))) * (np.e ** ((((- np.log((3 * K0) / (Fermi_Gas_Parameter))) - ((5 / 3) * (np.log(Initial_Volume__Angstroms_Per_Unit_Cell / Atomic_Number)))) * (1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3))))))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Adapted_Polynomial__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Atomic_Number,
    Initial_Pressure=0):

    # The Adapted Polynomial equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers and exponential functions
        # So instead we can use an iterative solver to find Volume

    # Call the Adapted Polynomial equation
    def Adapted_Polynomial_Equation(Volume):
        return Adapted_Polynomial__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, Atomic_Number, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Adapted_Polynomial_Equation
            # The upper bound is tighter (110%) than other equations because the AP2 equation
            # incorporates the Thomas-Fermi high-pressure limit and can behave poorly near ambient
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.1 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return np.nan
    except ValueError:
        return np.nan



########################################
# H02

    # P(V) = 3K₀ · (1-(V/V₀)^⅓) / (V/V₀)^⁵⁄₃ · e^(c₂·(1-(V/V₀)^⅓))
    # where c₂ = (3/2)(K₀′-3)
########################################

# Calculate pressure from a volume
def Holzapfel_H02__Calculate_Pressure_From_Input_Volume(
    Volume,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Initial_Pressure=0):

    # H02 Equation of State
        # Holzapfel, 2002
    c2 = (3 / 2) * (K0_Prime - 3)
    x = (Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3)
    Pressure = 3 * K0 * ((1 - x) / x**5) * np.exp(c2 * (1 - x)) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Holzapfel_H02__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Initial_Pressure=0):

    # The H02 equation cannot be rearranged to isolate Volume
        # So instead we use an iterative solver to find Volume

    def Holzapfel_H02_Equation(Volume):
        return Holzapfel_H02__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, Initial_Pressure) - Pressure

    try:
        Equation = Holzapfel_H02_Equation
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.1 * Initial_Volume__Angstroms_Per_Unit_Cell]
        Method = 'brentq'
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return np.nan
    except ValueError:
        return np.nan



########################################
# H12

    # P(V) = 3K₀ · (1-(V/V₀)^⅓) / (V/V₀)^⁵⁄₃ · e^(c₀·(1-(V/V₀)^⅓) + c₂·(V/V₀)^⅓·(1-(V/V₀)^⅓))
    # where c₀ = -ln(3K₀/a_FG) - (5/3)·ln(V₀/Z),  c₂ = (3/2)(K₀′-3) - c₀,  a_FG = 2337 GPa·Å⁵
########################################

# Calculate pressure from a volume
def Holzapfel_H12__Calculate_Pressure_From_Input_Volume(
    Volume,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Atomic_Number,
    Initial_Pressure=0):

    Fermi_Gas_Parameter = 2337    # GPa

    # H12 Equation of State
        # Holzapfel, 2012
    c0 = -np.log((3 * K0) / Fermi_Gas_Parameter) - (5 / 3) * np.log(Initial_Volume__Angstroms_Per_Unit_Cell / Atomic_Number)
    c2 = (3 / 2) * (K0_Prime - 3) - c0
    x = (Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3)
    Pressure = (3 * K0 * ((1 - x) / x**5) * np.exp(c0 * (1 - x) + c2 * x * (1 - x))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Holzapfel_H12__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    Atomic_Number,
    Initial_Pressure=0):

    # The H12 equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers and exponential functions
        # So instead we can use an iterative solver to find Volume

    # Call the H12 equation
    def Holzapfel_H12_Equation(Volume):
        return Holzapfel_H12__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, Atomic_Number, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Holzapfel_H12_Equation
            # The upper bound is tighter (110%) than other equations because the H12 equation
            # incorporates the Thomas-Fermi high-pressure limit and can behave poorly near ambient
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.1 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return np.nan
    except ValueError:
        return np.nan



########################################
# Keane

    # P(V) = K₀ · (K₀′/K∞′² · ((V₀/V)^K∞′ - 1) - (K₀′/K∞′ - 1) · ln(V₀/V))
########################################

# Calculate pressure from a volume
def Keane__Calculate_Pressure_From_Input_Volume(
    Volume,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    K_Infinity_Prime,
    Initial_Pressure=0):

    # Keane Equation of State
        # Keane, 1954
    Pressure = ((K0) * ((((K0_Prime / (K_Infinity_Prime ** 2)) * (((Initial_Volume__Angstroms_Per_Unit_Cell / Volume) ** (K_Infinity_Prime)) - 1))) - (((K0_Prime / K_Infinity_Prime) - 1) * (np.log(Initial_Volume__Angstroms_Per_Unit_Cell / Volume))))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Keane__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    K_Infinity_Prime,
    Initial_Pressure=0):

    # The Keane equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers and exponential functions
        # So instead we can use an iterative solver to find Volume

    # Call the Keane equation
    def Keane_Equation(Volume):
        return Keane__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, K_Infinity_Prime, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Keane_Equation
            # The Volume should be between 30% and 110% of the Initial Volume
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.1 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        return None



########################################
# Rydberg-Stacey

    # P(V) = 3K₀ · (V/V₀)^(-K∞′) · (1-(V/V₀)^⅓) · e^((³⁄₂K₀′ - 3K∞′ + ½)·(1-(V/V₀)^⅓))
########################################

# Calculate pressure from a volume
def Rydberg_Stacey__Calculate_Pressure_From_Input_Volume(
    Volume,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    K_Infinity_Prime,
    Initial_Pressure=0):

    # Rydberg-Stacey Equation of State
        # Stacey, 2005
    Pressure = (3 * K0 * ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (- K_Infinity_Prime)) * (1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3))) * (np.e ** ((((3 / 2) * K0_Prime) - (3 * K_Infinity_Prime) + (1 / 2)) * (1 - ((Volume / Initial_Volume__Angstroms_Per_Unit_Cell) ** (1 / 3)))))) + Initial_Pressure

    return Pressure

# Calculate volume from a pressure
def Rydberg_Stacey__Calculate_Volume_From_Input_Pressure(
    Pressure,
    Initial_Volume__Angstroms_Per_Unit_Cell,
    K0,
    K0_Prime,
    K_Infinity_Prime,
    Initial_Pressure=0):

    # The Rydberg-Stacey equation cannot be rearranged to isolate Volume because Volume appears in multiple terms with different fractional powers and exponential functions
        # So instead we can use an iterative solver to find Volume

    # Call the Rydberg-Stacey equation
    def Rydberg_Stacey_Equation(Volume):
        return Rydberg_Stacey__Calculate_Pressure_From_Input_Volume(Volume, Initial_Volume__Angstroms_Per_Unit_Cell, K0, K0_Prime, K_Infinity_Prime, Initial_Pressure) - Pressure

    # Use Brent's method to solve for Volume
    try:
        Equation = Rydberg_Stacey_Equation
            # The Volume should be between 30% and 110% of the Initial Volume
        Bracket = [0.3 * Initial_Volume__Angstroms_Per_Unit_Cell, 1.1 * Initial_Volume__Angstroms_Per_Unit_Cell]
            # Use the inverse quadratic interpolation of Brent's method
        Method = 'brentq'
        # Use scipy to solve for Volume
        Solution = root_scalar(Equation, bracket=Bracket, method=Method)
        if Solution.converged:
            return Solution.root
        else:
            return None
    except ValueError:
        return None





