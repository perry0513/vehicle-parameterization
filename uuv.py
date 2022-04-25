import math
from py3dbp import Packer, Bin, Item
import math

df_threshold = 90
energy_needed = 260 # kWh


# constants
water_density = 1027 # kg/m^3

payload_x = 1000 # mm
payload_y = 1000 # mm
payload_z = 300 # mm
payload_volume = payload_x * payload_y * payload_z * 1e-9 # m^3
payload_density = 2810 # kg/m^3
payload_mass = payload_volume * payload_density # kg
payload_buoyancy = payload_volume * water_density # kg
payload_in_water_weight = payload_mass - payload_buoyancy # kg

bat_energy_density_per_vol = 370 # kWh/m^3
bat_density = 1446 # kg/m^3
PV_density = 3950 # kg/m^3
PV_thickness = 0.026 # m
fairing_thickness = 0.0127 # m
fairing_density = 1465 # kg/m^3
float_density = 465 # kg/m^3

class packing_problem:
    def __init__(self, sol):
        self.sol = sol
        self.items = {}
        self.evaluated = False
        self.feasible = False
        self.loss = float("inf")


    def pack(self):
        params = self.sol.params
        length = params[0] * 1e-3 # m
        vehicle_volume = params[0] * params[1] * params[2] * 1e-9 # m^3
        _fairing_area = self.sol.area
        fairing_volume = self.sol.vol

        # Assume batteries and pressure vessels are rectangles

        # energy_needed = # kWh
        bat_volume = energy_needed / bat_energy_density_per_vol # m^3
        bat_mass = bat_volume * bat_density # kg
        bat_length = length - 2 * PV_thickness # m
        bat_width = math.sqrt(bat_volume / length) # m
        bat_height = math.sqrt(bat_volume / length) # m

        PV_length = length # m
        PV_width = bat_width + 2 * PV_thickness # m
        PV_height = bat_height + 2 * PV_thickness # m
        PV_disp_volume = PV_length * PV_width * PV_height # m^3
        PV_volume = PV_disp_volume - bat_volume # m^3
        PV_mass = PV_volume * PV_density # kg
        PV_buoyancy = PV_disp_volume * water_density # kg
        PV_in_water_weight = PV_mass - PV_buoyancy # kg


        fairing_area = _fairing_area * 1e-6 # m^2
        fairing_disp_volume = fairing_area * fairing_thickness # m^3
        fairing_mass = fairing_volume * fairing_density # kg
        fairing_buoyancy = fairing_volume * water_density # kg
        fairing_in_water_weight = fairing_mass - fairing_buoyancy # kg

        total_in_water_weight = bat_mass + PV_in_water_weight + fairing_in_water_weight + payload_in_water_weight # kg
        assert total_in_water_weight > 0

        float_volume = total_in_water_weight / (water_density - float_density) # m^3
        spare_volume = vehicle_volume - fairing_disp_volume - PV_disp_volume - payload_volume # m^3
        is_neutrally_buoyant = spare_volume > float_volume
        packer = Packer()
        packer.add_item(Item("pv", PV_length * 1e3, PV_width * 1e3, PV_height * 1e3, 0)) # not using weight for packing
        packer.add_item(Item("payload", payload_x, payload_y, payload_z, 0)) # not using weight for packing
        packer.add_bin(Bin('main-cabin', self.sol.params[0], self.sol.params[1], self.sol.params[2], 10))
        packing_loss = self._pack(packer) # volume needed
        # self.loss = math.exp(math.log10(total_in_water_weight) * packingloss) + total_in_water_weight
        # TODO: need normalizing
        print(packing_loss * 1e-9, (float_volume - spare_volume) * 1e-9)
        self.loss = max(packing_loss, 0) + max(float_volume - spare_volume, 0)
        self.evaluated = True
        return packing_loss

    def _pack(self, packer):
        x = self.sol.params[0]
        y = self.sol.params[1]
        z = self.sol.params[2]
        orig_x, orig_y, orig_z = x, y, z

        packer.pack()
        # loss = 0
        inx = x * 0.1
        iny = y * 0.1
        inz = z * 0.1
#         print(self.sol.params)
        while len(packer.bins[0].unfitted_items) != 0:
            # loss += 1
            x += inx
            packer.bins[0] = Bin('main-cabin', x,y,z, 10)
            packer.pack()
            if len(packer.bins[0].unfitted_items) == 0:
                print("new x:", x)
                break
            x -= inx
            y += iny
            packer.bins[0] = Bin('main-cabin', x,y,z, 10)
            packer.pack()
            if len(packer.bins[0].unfitted_items) == 0:
                print("new y:", y)
                break
            y -= iny
            z += inz
            packer.bins[0] = Bin('main-cabin', x,y,z, 10)
            packer.pack()
            if len(packer.bins[0].unfitted_items) == 0:
                print("new z:", z)
                break
            x += inx
            y += iny
            packer.bins[0] = Bin('main-cabin', x,y,z, 10)
            packer.pack()
            if len(packer.bins[0].unfitted_items) == 0:
                print("new:", x, y, z)
                break

        loss = x * y * z - orig_x * orig_y * orig_z
        # self.feasible = is_neutrally_buoyant and len(packer.bins[0].unfitted_items) == 0
        self.feasible = loss == 0
        if self.feasible:
            for item in packer.bins[0].items:
                self.items[item.name] = item.position
        # print(f"loss: {loss}")
        return loss
