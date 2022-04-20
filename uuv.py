import math

df_threshold = 90
energy_needed = 260 # kWh


# constants 
payload_x = 1000 # mm
payload_y = 1000 # mm
payload_z = 300 # mm
payload_volume = payload_x * payload_y * payload_z * 1e-9 # m^3

water_density = 1027 # kg/m^3
bat_energy_density_per_vol = 370 # kWh/m^3
bat_density = 1446 # kg/m^3
PV_density = 3950 # kg/m^3
PV_thickness = 0.026 # m
fairing_thickness = 0.0127 # m
fairing_density = 1465 # kg/m^3
float_density = 465 # kg/m^3

def pack(_length, _vehicle_volume, _fairing_area):
    length = _length * 1e-3 # m
    vehicle_volume = _vehicle_volume * 1e-9 # m^3

    # Assume batteries and pressure vessels are rectangles

    # energy_needed = # kWh
    bat_volume = energy_needed / bat_energy_density_per_vol # m^3
    bat_mass = bat_volume * bat_density # kg
    bat_length = length # m
    bat_width = math.sqrt(bat_volume / length) # m
    bat_height = math.sqrt(bat_volume / length) # m

    PV_disp_volume = (bat_length + PV_thickness) * (bat_width + PV_thickness) * (bat_height + PV_thickness) # m^3
    PV_volume = PV_disp_volume - bat_volume # m^3
    PV_mass = PV_volume * PV_density # kg
    PV_buoyancy = PV_disp_volume * water_density # kg
    PV_in_water_weight = PV_mass - PV_buoyancy # kg


    fairing_area = _fairing_area * 1e-6 # m^2
    fairing_disp_volume = fairing_area * fairing_thickness # m^3
    fairing_mass = fairing_volume * fairing_density # kg
    fairing_buoyancy = fairing_volume * water_density # kg
    fairing_in_water_weight = fairing_mass - fairing_buoyancy # kg

    total_in_water_weight = bat_mass + PV_in_water_weight + fairing_in_water_weight # kg
    assert total_in_water_weight > 0

    float_volume = total_in_water_weight / (water_density - float_density) # m^3
    spare_volume = vehicle_volume - fairing_disp_volume - PV_disp_volume - payload_volume # m^3
    is_neutrally_buoyant = spare_volume > float_volume
    

    # TODO: check whether PV and payload can fit in vehicle
