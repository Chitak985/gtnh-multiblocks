"""
TODO

Fix Fusion Reactor's per-hatch limits not working
Fix images to display properly (tiered multis have no tiered images)
Fix casing that has a dynamic and fixed cost (see fluid drilling rig) not combining into one
Fix the game saying you can't use steam output buses if the multi can't support output buses
Check Compact Fusion Reactor's max hatch amounts
Check Fusion Reactor wallsharing
Check if Wireless Energy Hatches (normal ones) don't use Amps
Add Compact Fusion Reactor wallsharing
Add ORC (Optical Reception Connector), start with Dyson
Add coil changing (everything uses either tiers or worst coils)
Add overclocks (also research what happens with 2+ hatches)
Add images changing with tiers
Add the better multiblock selector
Add the better IO selector (IO slots) for all multis
Add byproduct handling
"""

debugFile = False  # Use True to export an HTML file rendered on the index page

from flask import Flask, render_template

app = Flask(__name__)

# This exists to be able to change glass types automatically, even though that isn't implemented yet.
# To get the block it represents, str it or similar (str the array it is in)
# Another set of quotes inside to make it JavaScript friendly
class Item:
    def __init__(self, n):
        self.type_ = n
    def __str__(self):
        if(self.type_ == "GLASS"):
            return "'Borosilicate Glass Block'"
    def __repr__(self):
        if(self.type_ == "GLASS"):
            return "'Borosilicate Glass Block'"

##### VARIABLES #####
recipeChoices = {}
recipeSelected = {}
blockToInternal = {
    "Cupronickel Coil Block": "gregtech:gt.blockcasings5:0",
    "Kanthal Coil Block": "gregtech:gt.blockcasings5:1",
    "Nichrome Coil Block": "gregtech:gt.blockcasings5:2",
    "TPV-Alloy Coil Block": "gregtech:gt.blockcasings5:3",
    "HSS-G Coil Block": "gregtech:gt.blockcasings5:4",
    "HSS-S Coil Block": "gregtech:gt.blockcasings5:5",
    "Naquadah Coil Block": "gregtech:gt.blockcasings5:6",
    "Naquadah Alloy Coil Block": "gregtech:gt.blockcasings5:7",
    "Trinium Coil Block": "gregtech:gt.blockcasings5:8",
    "Electrum Flux Coil Block": "gregtech:gt.blockcasings5:9",
    "Awakened Draconium Coil Block": "gregtech:gt.blockcasings5:10",
    "Infinity Coil Block": "gregtech:gt.blockcasings5:11",
    "Hypogen Coil Block": "gregtech:gt.blockcasings5:12",
    "Eternal Coil Block": "gregtech:gt.blockcasings5:13",
}

##### HELPER FUNCTIONS #####
# Get multiblock size
# Returns either a string if the multiblock has a custom size, None if the multiblock is not implemented yet, or a list like this: [x, y, z, HasGapsOnTheSurface]
def multiblockSize(name):
    if(name == "Coke Oven"):
        return [3,3,3, False]
    elif(name == "Water Tank"):
        return [3,3,3, False]
    elif(name == "Bricked Blast Furnace"):
        return [3,4,3, False]
    elif(name == "Railcraft Boiler"):
        return "Railcraft Boiler"
    elif(name == "Railcraft Tank"):
        return "Railcraft Tank"
    elif(name == "Water Pump"):
        return [4,3,3, True]
    elif(name == "Charcoal Pile Igniter"):
        return "Charcoal Pile Igniter"
    elif(name == "Steam Oven"):
        return [2,2,2]
    else:
        return None

# Size -> wallshare table
# Currently only makes the front side
def getWallshareTable(x,y,z):
    tmp = "<table><tr>"
    for i in range(x-1):
        tmp += '<td style="border-top: 1px solid gray;">1</td>'
    tmp += '<td style="border-top: 1px solid gray; border-right: 1px solid gray">1</td></tr>'
    for i in range(y-1):
        tmp += "<tr>"
        for i2 in range(x-1):
            tmp += "<td>1</td>"
        tmp += '<td style="border-right: 1px solid gray">1</td></tr>'
    return tmp

##### RECIPIES #####
# For circuits, do "LV Circuit" or similar
# For using a wrench or similar, use "{Wrench Use}": 1
# For using a wooden form (brick), use "{Wooden Form (Brick) Use}": 1
##### means This Recipe Has Been Fact Checked by Real GTNH NEI
# !TODO:
    # "Reinforced Temporal Structure Casing": Check first two [FLUID] to get correct quantities
    # Add byproduct handling
    # "ULV Energy Hatch": Does it consume lubricant cells or return them empty?
    # "UXV 256A Wireless Energy Hatch": Check mutated living solder quantity
recipeList = {"Bronze Plated Bricks": [["Crafting", 0, {"Bronze Plate": 6, "Bricks": 1, "{Wrench Use}": 1, "{Hammer Use}": 1}],
                                       ["Assembler (LV)", 2, {"Bronze Plate": 6, "Bricks": 1, "Programmed Circuit (1)": 0}]],
              "Steam Hatch": [["Crafting", 0, {"Bronze Plate": 6, "Large Clay Pipe": 2, "Ultra Low Voltage Fluid Tank": 1}]],
              "Ultra Low Voltage Fluid Tank": [["Crafting", 0, {"Iron Plate": 4, "Tin Plate": 2, "Steel Plate": 1, "Large Clay Fluid Pipe": 1, "Water Bucket": 1}]],
              "Large Clay Fluid Pipe": [["Crafting", 0, {"Clay Plate": 6, "{Wrench Use}": 1, "{Hammer Use}": 1}],
                                        ["Extruder (MV)", 3, {"Clay": 12, "Extruder Shape (Large Pipe)": 0}]],
              "Bronze Fluid Pipe": [["Crafting", 0, {"Bronze Plate": 6, "{Wrench Use}": 1, "{Hammer Use}": 1}, {"Bronze Fluid Pipe": 2}],
                                    ["Extruder (MV)", 3, {"Bronze Ingot": 3, "Extruder Shape (Normal Pipe)": 0}],
                                    ["Fluid Soldifier (MV)", 3, {"[FLUID] Molten Bronze": 432, "Mold (Normal Pipe)": 0}]],
              "Input Bus (Steam)": [["Crafting", 0, {"Bronze Plate": 4, "Tin Plate": 2, "Tumbaga Plate": 2, "Hopper": 1}]],
              "Output Bus (Steam)": [["Crafting", 0, {"Bronze Plate": 4, "Tin Plate": 2, "Tumbaga Plate": 2, "Hopper": 1}]],
              "Hopper": [["Crafting", 0, {"Iron Plate": 5, "Iron Gear": 1, "Chest": 1, "{Hammer Use}": 1, "{File Use}": 1}],
                         ["Crafting", 0, {"Wrought Iron Plate": 5, "Iron Gear": 1, "Chest": 1, "{Hammer Use}": 1, "{File Use}": 1}],
                         ["Crafting", 0, {"Pig Iron Plate": 5, "Iron Gear": 1, "Chest": 1, "{Hammer Use}": 1, "{File Use}": 1}],
                         ["Crafting", 0, {"Iron Plate": 5, "Wrought Iron Gear": 1, "Chest": 1, "{Hammer Use}": 1, "{File Use}": 1}],
                         ["Crafting", 0, {"Wrought Iron Plate": 5, "Wrought Iron Gear": 1, "Chest": 1, "{Hammer Use}": 1, "{File Use}": 1}],
                         ["Crafting", 0, {"Pig Iron Plate": 5, "Wrought Iron Gear": 1, "Chest": 1, "{Hammer Use}": 1, "{File Use}": 1}],
                         ["Assembler (LV)", 2, {"Iron Plate": 5, "Chest": 1}],
                         ["Assembler (LV)", 2, {"Wrought Iron Plate": 5, "Chest": 1}],
                         ["Assembler (LV)", 2, {"Pig Iron Plate": 5, "Chest": 1}]],
              "Chest": [["Crafting", 0, {"Wood": 4, "Wood Planks": 4, "Flint": 1}],
                        ["Assembler (LV)", 2, {"Wood": 2, "Wood Planks": 2}],
                        ["Assembler (LV)", 2, {"Wood Planks": 8, "Programmed Circuit (8)": 0}],
                        ["Assembler (LV)", 2, {"Wood Plank": 8, "Programmed Circuit (8)": 0}]],
              "Giga Chad Token": [["DTPF (Eternal) (MAX)", 15, {"Field Generator (UEV)": 64, "Field Generator (UIV)": 64, "Field Generator (UMV)": 64, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 100000000, "[FLUID] Molten SpaceTime": 165888}]],
              "Block of Magmatter": [["Compressor (UMV)", 13, {"Magmatter Ingot": 9}],
                                     ["Extruder (UMV)", 13, {"Magmatter Ingot": 9, "Extruder Shape (Block)": 0}]],
              "Superdense Magmatter Plate": [["Compressor (UMV)", 13, {"Magmatter Plate": 64}]],
              "Coke Oven Brick (Block)": [["Crafting", 0, {"Coke Oven Brick (Item)": 4}],
                                          ["Compressor (LV)", 4, {"Coke Oven Brick (Item)": 4}]],
              "Coke Oven Brick (Item)": [["Alloy Smelter (LV)", 2, {"Sand": 1, "Clay": 1}, {"Coke Oven Brick (Item)": 2}],
                                         ["Alloy Smelter (LV)", 2, {"Red Sand": 1, "Clay": 1}, {"Coke Oven Brick (Item)": 2}],
                                         ["Furnace", 0, {"Unfired Coke Oven Brick": 1}]],
              "Unfired Coke Oven Brick": [["Crafting", 0, {"Sand": 5, "Clay": 3, "{Wooden Form (Brick) Use}": 1}, {"Unfired Coke Oven Brick": 3}],
                                          ["Crafting", 0, {"Red Sand": 5, "Clay": 3, "{Wooden Form (Brick) Use}": 1}, {"Unfired Coke Oven Brick": 3}]],
              "[FLUID] Milk (automagy)": [["Distillery (LV)", 2, {"[FLUID] Milk (adventurebackpack)": 1000, "Programmed Circuit (1)": 0}, {"[FLUID] Milk (automagy)": 1000}]],
              "[FLUID] Blood (biomesoplenty)": [["Large Chemical Reactor (LV)", 2, {"[FLUID] Blood (tconstruct)": 1000, "[FLUID] Nether Air": 100}, {"[FLUID] Blood (biomesoplenty)": 1000}]],
              "Keyboard": [["Assembler (MV)", 3, {"Button": 104, "Aluminium Casing": 1, "LV Circuit": 1}]],
              "Fireclay Dust": [["Crafting", 0, {"Brick Dust": 1, "Clay Dust": 1}, {"Fireclay Dust": 2}],
                                ["Multiblock Mixer (LV)", 2, {"Brick Dust": 1, "Clay Dust": 1}, {"Fireclay Dust": 2}],
                                ["Mixer (LV)", 2, {"Brick Dust": 1, "Clay Dust": 1}, {"Fireclay Dust": 2}]],
              "Compressed Fireclay": [["Compressor (LV)", 2, {"Fireclay Dust": 1}]],
              "Firebrick": [["Furnace", 0, {"Compressed Fireclay": 1}]],
              "Bricked Blast Furnace": [["Crafting", 0, {"Firebricks": 4, "Blast Furnace": 4, "{Wrench Use}": 1}]],
              "Crude Time Dilation Field Generator": [["Assemblyline Process (UMV)", 13, {"Reinforced Temporal Structure Casing": 1, "Fusion Control Computer Mark II": 1, "Compact Fusion Coil": 1, "Ultimate Solar Panel": 1, "UXV Circuit": 1, "Red Spectral Component": 64, "Green Spectral Component": 64, "Blue Spectral Component": 64, "Shirabon Bolt": 2, "Dyson Swarm Module Deployment Unit Base Casing": 4, "Dyson Swarm Energy Receiver Dish Block": 4, "Ultimate Time Anomaly": 4, "Energy Module": 1, "1x Superconductor UMV Wire": 4, "[FLUID] Mutated Living Solder": 2880, "[FLUID] Tachyon Rich Temporal Fluid": 1440, "[FLUID] Molten SpaceTime": 1440}]],
              "Reinforced Temporal Structure Casing": [["Assemblyline Process (UMV)", 13, {"Singularity Reinforced Stellar Shielding Casing": 32, "Cosmic Neutronium Block": 64, "Block of Neutronium": 64, "Neutronium Nanites": 48, "Bedrockium Large Plate": 1, "Neutronium Large Plate": 1, "Shirabon Large Plate": 1, "Infinity Large Plate": 1, "Ultimate Solar Panel": 1, "Ultimate Time Anomaly": 4, "Gravitation Engine": 64, "Energised Tesseract": 1, "[FLUID] Molten Neutronium": 147500, "[FLUID] Molten Cosmic Neutronium": 147500, "[FLUID] Mutated Living Solder": 73728, "[FLUID] Tachyon Rich Temporal Fluid": 1440}, {"Reinforced Temporal Structure Casing": 4}]],
              "Ridiculously Large Capacitor": [["Extreme Crafting", 6, {"Emitter (UXV)": 2, "Stargate-Radiation-Containment-Plate": 12, "Field Generator (UXV)": 4, "Chaotic Capacitor Bank": 8, "Stellar Energy Siphon Casing": 4, "Mega Ultimate Battery": 3}]],
              "ME Fluid Digital Singularity Storage Cell": [["Space Assembler (UHV)", 10, {"Eternal Singularity": 1, "Fluid Cell Block T7": 4, "16384k ME Fluid Storage Component": 8, "Quantum Tank V": 8, "Infinity Block": 4, "Infinity Catalyst": 4, "Cosmic Neutronium Block": 12, "[FLUID] Mutated Living Solder": 2304}]], #####
              "Eye of Harmony": [["Assemblyline Process (UMV)", 13, {"Space Elevator": 16, "Forge of the Gods": 4, "Dimensionally Transcendent Plasma Forge": 4, "Infinite Spacetime Energy Boundary Casing": 1, "Crude Time Dilation Field Generator": 1, "Crude Spacetime Compression Field Generator": 1, "Crude Stabilisation Field Generator": 1, "Quantum Computer": 64, "Ultimate Time Anomaly": 64, "Quantum Chest V": 64, "Void Miner III": 64, "Infinite Fluid Drilling Rig": 64, "Field Generator (UMV)": 16, "Robot Arm (UMV)": 16, "Insanely Ultimate Battery": 4, "16x Superconductor UMV Wire": 64, "[FLUID] Tachyon Rich Temporal Fluid": 144000, "[FLUID] Spatially Enlarged Fluid": 144000, "[FLUID] Molten Metastable Oganesson": 147456, "[FLUID] Molten Shirabon": 147456}]],
              "Blast Furnace": [["Crafting", 0, {"Furnace": 1, "Iron Plate": 7, "{Wrench Use}": 1}],
                                ["Crafting", 0, {"Furnace": 1, "Wrought Iron Plate": 7, "{Wrench Use}": 1}],
                                ["Crafting", 0, {"Furnace": 1, "Pig Iron Plate": 7, "{Wrench Use}": 1}],
                                ["Assembler (LV)", 2, {"Furnace": 1, "Iron Plate": 5}],
                                ["Assembler (LV)", 2, {"Furnace": 1, "Wrought Iron Plate": 5}],
                                ["Assembler (LV)", 2, {"Furnace": 1, "Pig Iron Plate": 5}]],
              "Energised Tesseract": [["Neutron Activator (LV)", 2, {"Raw Tesseract": 1, "[FLUID] Naquadah Based Liquid Fuel MKVI": 64}, {"Energised Tesseract": 1, "[FLUID] Naquadah Based Liquid Fuel MKVI (Depleted)": 64}],
                                      ["Neutron Activator (LV)", 2, {"Raw Tesseract": 1, "[FLUID] Naquadah Based Liquid Fuel MKV": 64}, {"Energised Tesseract": 1, "[FLUID] Naquadah Based Liquid Fuel MKV (Depleted)": 64}],
                                      ["Laser Engraver (UIV)", 12, {"Raw Tesseract": 1, "Quantum Anomaly": 0}, {"Energised Tesseract": 1, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 100}]],
              "ME Fluid Artificial Universe Storage Cell": [["Space Assembler (UXV)", 14, {"Field Generator (UXV)": 1, "Magmatter Nanites": 4, "ME Fluid Digital Singularity Storage Cell": 1, "Dense Shirabon Plate": 16, "Fluid Cell Block T10": 2, "T.F.F.T Storage Field Block (Tier X)": 2, "Gallifreyan Spacetime Compression Field Generator": 4, "Eternity Nanites": 4, "[FLUID] Molten Eternity": 36864}]],
              "Magmatter Nanites": [["Nano Forge (Tier 4) (MAX)", 15, {"Forcicium Lens": 0, "Forcillium Lens": 0, "Universium Nanites": 1, "Block of Magmatter": 1, "Pico Wafer": 64, "UXV Circuit": 1, "[FLUID] Degenerate Quark Gluon Plasma": 10000, "[FLUID] Lossless Phonon Transfer Medium": 64000, "[FLUID] Liquid Primordial Matter": 128000}]],
              "Singularity Crafting Storage": [["Extreme Crafting", 6, {"Neutronium Energy Cell": 4, "Pico Circuit": 8, "Field Generator (UIV)": 12, "Reactor Stabilizer": 8, "Transcendent Metal Nanites": 4, "Dense Infinity Plate": 24, "1x SpaceTime Wire": 12, "SpaceTime Frame Box": 4, "Crafting Unit": 4, "Digital Singularity ME Storage Cell": 1}]], #####
              "Artificial Universe ME Storage Cell": [["Space Assembler (UXV)", 14, {"Digital Singularity ME Storage Cell": 1, "Dense Transcendent Metal Plate": 64, "Field Generator (UXV)": 1, "Mega Ultimate Battery": 1, "Gallifreyan Spacetime Compression Field Generator": 4, "Magmatter Nanites": 4, "Eternity Nanites": 4, "[FLUID] Molten Eternity": 36864}]], #####
              "Firebricks": [["Crafting", 0, {"Firebrick": 6, "Gypsum Dust": 2, "Bucket of Concrete": 1}], #####
                             ["Crafting", 0, {"Firebrick": 6, "Calcium Sulfate (Gypsum) Dust": 2, "Bucket of Concrete": 1}], #####
                             ["Assembler (LV)", 2, {"Firebrick": 24, "Gypsum Dust": 8, "[FLUID] Concrete": 4608}, {"Firebricks": 4}], #####
                             ["Assembler (LV)", 2, {"Firebrick": 24, "Calcium Sulfate (Gypsum) Dust": 8, "[FLUID] Concrete": 4608}, {"Firebricks": 4}], #####
                             ["Assembler (LV)", 2, {"Firebrick": 24, "Gypsum Dust": 8, "[FLUID] Wet Concrete": 4608}, {"Firebricks": 4}], #####
                             ["Assembler (LV)", 2, {"Firebrick": 24, "Calcium Sulfate (Gypsum) Dust": 8, "[FLUID] Wet Concrete": 4608}, {"Firebricks": 4}]], #####
              "Reactor Stabilizer": [["Extreme Crafting", 6, {"Black Plutonium Plate": 4, "Awakened Draconium Plate": 17, "Reactor Stabilizer Frame": 1, "Engraved Manyullyn Crystal Chip": 4, "Draconic Flux Capacitor": 4, "Chaotic Core": 2, "Reactor Stabilizer Focus Ring": 1, "Reactor Stabilizer Rotor Assembly": 1, "Cosmic Neutronium Block": 1}]], #####
              "Reactor Stabilizer Rotor Assembly": [["Extreme Crafting", 6, {"Long Draconium Rod": 6, "Charged Draconium Block": 1, "Fusion Coil Block": 4, "Wyvern Core": 1, "Draconium Plate": 1, "Reactor Stabilizer Outer Rotor": 10, "Reactor Stabilizer Inner Rotor": 10}]],
              "Reactor Stabilizer Outer Rotor": [["Extreme Crafting", 6, {"Draconium Plate": 4, "Draconic Core": 2, "Engraved Diamond Crystal Chip": 15}]],
              "Reactor Stabilizer Inner Rotor": [["Extreme Crafting", 6, {"Awakened Draconium Plate": 4, "Wyvern Core": 2, "Engraved Energy Chip": 15}]],
              "Reactor Stabilizer Focus Ring": [["Extreme Crafting", 6, {"Reactor Stabilizer Outer Rotor": 4, "Reactor Stabilizer Inner Rotor": 4, "Rose Gold Rod": 20, "Wyvern Core": 4, "Nether Star Lens": 4, "Diamond Lens": 1}]],
              "Reactor Stabilizer Frame": [["Extreme Crafting", 6, {"Black Plutonium Plate": 52, "Awakened Draconium Plate": 8, "Awakened Core": 1}]],
              "Draconic Flux Capacitor": [["Extreme Crafting", 6, {"Awakened Draconium Plate": 12, "Draconic Energy Core": 3, "Awakened Core": 1, "Enriched Naquadria Sunnarium Alloy": 4, "Wyvern Flux Capacitor": 1, "4x Superconductor UHV Wire": 8}]],
              "Wyvern Flux Capacitor": [["Extreme Crafting", 6, {"Draconium Plate": 12, "Wyvern Energy Core": 4, "Vibrant Capacitor Bank": 4, "Wyvern Core": 1, "2x Superconductor UHV Wire": 8}]],
              "Active Transformer": [["Assembler", 7, {"Ludicrous Power Transformer": 1, "High Energy Flow Circuit": 1, "1x Superconduction LuV Wire": 16, "Ultra High Power IC": 2, "[FLUID] Molten Tungstensteel": 576}]],
              "High Power Casing": [["Assembler", 7, {"Iridium Frame Box": 1, "Double Iridium Plate": 6, "LuV Circuit": 1, "Fine Cobalt Wire": 16, "Fine Copper Wire": 16, "2x Niobium-Titanium Wire": 2, "[FLUID] Molten Tungstensteel": 576}]],
              # Energy Hatches (normal tiered)
              "ULV Energy Hatch": [["Crafting", 0, {"1x Lead Cable": 2, "Ultra Low Voltage Coil": 2, "Lubricant Cell": 2, "Lead Rotor": 1, "ULV Machine Hull": 1, "ULV Circuit": 1}]],
              "LV Energy Hatch": [["Crafting", 0, {"1x Tin Cable": 2, "LV Circuit": 1, "Low Volatge Coil": 2, "LV Machine Hull": 1, "Electric Pump (LV)": 1, "Lubricant Cell": 2}],
                                  ["Assembler (LV)", 2, {"Programmed Circuit (4)": 0, "1x Tin Cable": 2, "LV Circuit": 1, "Low Volatge Coil": 2, "LV Machine Hull": 1, "Electric Pump (LV)": 1, "[FLUID] Lubricant": 2000}]],
              "MV Energy Hatch": [["Crafting", 0, {"1x Copper Cable": 1, "Ultra Low Power IC": 2, "Medium Volatge Coil": 2, "MV Machine Hull": 1, "Electric Pump (MV)": 1, "Lubricant Cell": 2}],
                                  ["Assembler (MV)", 3, {"Programmed Circuit (4)": 0, "1x Copper Cable": 1, "Ultra Low Power IC": 2, "Medium Volatge Coil": 2, "MV Machine Hull": 1, "Electric Pump (MV)": 1, "[FLUID] Lubricant": 2000}]],
              "HV Energy Hatch": [["Assembler (HV)", 4, {"HV Machine Hull": 1, "1x Gold Cable": 1, "Low Power IC": 2, "High Voltage Coil": 2, "60k He Coolant Cell": 1, "Electric Pump (HV)": 1}],
                                  ["Assembler (HV)", 4, {"HV Machine Hull": 1, "1x Gold Cable": 1, "Low Power IC": 2, "High Voltage Coil": 2, "60k NaK Coolant Cell": 1, "Electric Pump (HV)": 1}]],
              "EV Energy Hatch": [["Assembler (EV)", 5, {"EV Machine Hull": 1, "1x Aluminium Cable": 1, "Power IC": 2, "Extreme Voltage Coil": 2, "60k He Coolant Cell": 1, "Electric Pump (EV)": 1}],
                                  ["Assembler (EV)", 5, {"EV Machine Hull": 1, "1x Aluminium Cable": 1, "Power IC": 2, "Extreme Voltage Coil": 2, "60k NaK Coolant Cell": 1, "Electric Pump (EV)": 1}]],
              "IV Energy Hatch": [["Assembler (IV)", 6, {"IV Machine Hull": 1, "1x Superconductor IV Wire": 1, "High Power IC": 2, "Insane Voltage Coil": 2, "180k He Coolant Cell": 1, "Electric Pump (IV)": 1}],
                                  ["Assembler (IV)", 6, {"IV Machine Hull": 1, "1x Superconductor IV Wire": 1, "High Power IC": 2, "Insane Voltage Coil": 2, "180k NaK Coolant Cell": 1, "Electric Pump (IV)": 1}]],
              "LuV Energy Hatch": [["Assemblyline Process (LuV)", 7, {"LuV Machine Hull": 1, "1x Superconductor LuV Wire": 2, "Ultra High Power IC": 2, "LuV Circuit": 2, "Ludicrous Voltage Coil": 2, "180k He Coolant Cell": 2, "Electric Pump (LuV)": 1, "[FLUID] IC2 Coolant": 2000, "[FLUID] Molten Indalloy 140": 720}]],
              "ZPM Energy Hatch": [["Assemblyline Process (ZPM)", 8, {"ZPM Machine Hull": 1, "2x Superconductor ZPM Wire": 2, "Nano Power IC": 2, "ZPM Circuit": 2, "ZPM Voltage Coil": 2, "360k He Coolant Cell": 2, "Electric Pump (ZPM)": 1, "[FLUID] IC2 Coolant": 4000, "[FLUID] Molten Indalloy 140": 1440}]],
              "UV Energy Hatch": [["Assemblyline Process (UV)", 9, {"UV Machine Hull": 1, "2x Superconductor UV Wire": 2, "Piko Power IC": 2, "UV Circuit": 2, "Ultimate Voltage Coil": 2, "360k He Coolant Cell": 4, "Electric Pump (UV)": 1, "[FLUID] IC2 Coolant": 8000, "[FLUID] Molten Indalloy 140": 2880}]],
              "UHV Energy Hatch": [["Assemblyline Process (UHV)", 10, {"UHV Machine Hull": 1, "4x Superconductor UHV Wire": 2, "Quantum Power IC": 2, "UHV Circuit": 2, "Highly Ultimate Voltage Coil": 2, "360k He Coolant Cell": 8, "Electric Pump (UHV)": 1, "[FLUID] IC2 Coolant": 16000, "[FLUID] Molten Indalloy 140": 5760}]],
              "UEV Energy Hatch": [["Assemblyline Process (UEV)", 11, {"UEV Machine Hull": 1, "4x Superconductor UEV Wire": 2, "Quantum Power IC": 4, "UEV Circuit": 2, "Highly Ultimate Voltage Coil": 4, "1080k Sp Coolant Cell": 3, "Electric Pump (UEV)": 1, "[FLUID] IC2 Coolant": 32000, "[FLUID] Mutated Living Solder": 2880, "[FLUID] UU-Matter": 8000}]],
              "UIV Energy Hatch": [["Assemblyline Process (UIV)", 12, {"UIV Machine Hull": 1, "4x Superconductor UIV Wire": 2, "Quantum Power IC": 8, "UIV Circuit": 2, "Highly Ultimate Voltage Coil": 8, "1080k Sp Coolant Cell": 6, "Electric Pump (UIV)": 1, "[FLUID] Super Coolant": 16000, "[FLUID] Mutated Living Solder": 2880, "[FLUID] UU-Matter": 16000}]],
              "UMV Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UMV Machine Hull": 1, "4x Superconductor UMV Wire": 2, "Quantum Power IC": 16, "UMV Circuit": 2, "Highly Ultimate Voltage Coil": 16, "1080k Sp Coolant Cell": 9, "Electric Pump (UMV)": 1, "[FLUID] Super Coolant": 32000, "[FLUID] Mutated Living Solder": 5760, "[FLUID] UU-Matter": 32000}]],
              "UXV Energy Hatch": [["Assemblyline Process (UXV)", 14, {"UXV Machine Hull": 1, "4x Superconductor UXV Wire": 8, "Quantum Power IC": 16, "UXV Circuit": 2, "Highly Ultimate Voltage Coil": 32, "1080k Sp Coolant Cell": 10, "Electric Pump (UXV)": 1, "[FLUID] Super Coolant": 64000, "[FLUID] Mutated Living Solder": 11520, "[FLUID] UU-Matter": 64000}]],
              # Dynamo Hatches (normal tiered)
              "ULV Dynamo Hatch": [["Crafting", 0, {"ULV Circuit": 2, "Ultra Low Voltage Coil": 2, "Lead Spring": 1, "ULV Machine Hull": 1, "Lead Rotor": 1, "Lubricant Cell": 2}]],
              "LV Dynamo Hatch": [["Crafting", 0, {"LV Circuit": 2, "Low Voltage Coil": 2, "Tin Spring": 1, "LV Machine Hull": 1, "Electric Pump (LV)": 1, "Lubricant Cell": 2}]],
              "MV Dynamo Hatch": [["Crafting", 0, {"Ultra Low Power IC": 2, "Medium Voltage Coil": 2, "Copper Spring": 1, "MV Machine Hull": 1, "Electric Pump (MV)": 1, "Lubricant Cell": 2}]],
              "HV Dynamo Hatch": [["Assembler (HV)", 4, {"Low Power IC": 2, "High Voltage Coil": 2, "Gold Spring": 1, "HV Machine Hull": 1, "Electric Pump (HV)": 1, "60k NaK Coolant Cell": 1}],
                                  ["Assembler (HV)", 4, {"Low Power IC": 2, "High Voltage Coil": 2, "Gold Spring": 1, "HV Machine Hull": 1, "Electric Pump (HV)": 1, "60k He Coolant Cell": 1}]],
              "EV Dynamo Hatch": [["Assembler (EV)", 5, {"Power IC": 2, "Extreme Voltage Coil": 2, "Aluminium Spring": 1, "EV Machine Hull": 1, "Electric Pump (EV)": 1, "60k NaK Coolant Cell": 1}],
                                  ["Assembler (EV)", 5, {"Power IC": 2, "Extreme Voltage Coil": 2, "Aluminium Spring": 1, "EV Machine Hull": 1, "Electric Pump (EV)": 1, "60k He Coolant Cell": 1}]],
              "IV Dynamo Hatch": [["Assembler (IV)", 6, {"High Power IC": 2, "Insane Voltage Coil": 2, "Superconductor Base IV Spring": 1, "IV Machine Hull": 1, "Electric Pump (IV)": 1, "180k NaK Coolant Cell": 1}],
                                  ["Assembler (IV)", 6, {"High Power IC": 2, "Insane Voltage Coil": 2, "Superconductor Base IV Spring": 1, "IV Machine Hull": 1, "Electric Pump (IV)": 1, "180k He Coolant Cell": 1}]],
              "LuV Dynamo Hatch": [["Assemblyline Process (LuV)", 7, {"Ultra High Power IC": 2, "Ludicrous Voltage Coil": 2, "Superconductor Base LuV Spring": 2, "LuV Machine Hull": 1, "Electric Pump (LuV)": 1, "180k NaK Coolant Cell": 2, "LuV Circuit": 2, "[FLUID] IC2 Coolant": 2000, "[FLUID] Molten Indalloy 140": 720}]],
              "ZPM Dynamo Hatch": [["Assemblyline Process (ZPM)", 8, {"Nano Power IC": 2, "ZPM Voltage Coil": 2, "Superconductor Base ZPM Spring": 4, "ZPM Machine Hull": 1, "Electric Pump (ZPM)": 1, "360k He Coolant Cell": 2, "ZPM Circuit": 2, "[FLUID] IC2 Coolant": 4000, "[FLUID] Molten Indalloy 140": 1440}]],
              "UV Dynamo Hatch": [["Assemblyline Process (UV)", 9, {"Piko Power IC": 2, "Ultimate Voltage Coil": 2, "Superconductor Base UV Spring": 4, "UV Machine Hull": 1, "Electric Pump (UV)": 1, "360k He Coolant Cell": 4, "UV Circuit": 2, "[FLUID] IC2 Coolant": 8000, "[FLUID] Molten Indalloy 140": 2880}]],
              "UHV Dynamo Hatch": [["Assemblyline Process (UHV)", 10, {"Quantum Power IC": 2, "Highly Ultimate Voltage Coil": 2, "Superconductor Base UHV Spring": 8, "UHV Machine Hull": 1, "Electric Pump (UHV)": 1, "360k He Coolant Cell": 8, "UHV Circuit": 2, "[FLUID] IC2 Coolant": 16000, "[FLUID] Molten Indalloy 140": 5760}]],
              "UEV Dynamo Hatch": [["Assemblyline Process (UEV)", 11, {"Quantum Power IC": 4, "Highly Ultimate Voltage Coil": 4, "Superconductor Base UEV Spring": 8, "UEV Machine Hull": 1, "Electric Pump (UEV)": 1, "1080k Sp Coolant Cell": 3, "UEV Circuit": 2, "[FLUID] IC2 Coolant": 32000, "[FLUID] Mutated Living Solder": 2880, "[FLUID] UU-Matter": 8000}]],
              "UIV Dynamo Hatch": [["Assemblyline Process (UIV)", 12, {"Quantum Power IC": 4, "Highly Ultimate Voltage Coil": 8, "Superconductor Base UIV Spring": 8, "UIV Machine Hull": 1, "Electric Pump (UIV)": 1, "1080k Sp Coolant Cell": 6, "UIV Circuit": 2, "[FLUID] Super Coolant": 16000, "[FLUID] Mutated Living Solder": 2880, "[FLUID] UU-Matter": 16000}]],
              "UMV Dynamo Hatch": [["Assemblyline Process (UMV)", 13, {"Quantum Power IC": 4, "Highly Ultimate Voltage Coil": 16, "Superconductor Base UMV Spring": 8, "UMV Machine Hull": 1, "Electric Pump (UMV)": 1, "1080k Sp Coolant Cell": 9, "UMV Circuit": 2, "[FLUID] Super Coolant": 32000, "[FLUID] Mutated Living Solder": 5760, "[FLUID] UU-Matter": 32000}]],
              "UXV Dynamo Hatch": [["Assemblyline Process (UXV)", 14, {"Quantum Power IC": 16, "Highly Ultimate Voltage Coil": 32, "Superconductor Base UMV Spring": 16, "UXV Machine Hull": 1, "Electric Pump (UXV)": 1, "1080k Sp Coolant Cell": 10, "UXV Circuit": 2, "[FLUID] Super Coolant": 64000, "[FLUID] Mutated Living Solder": 11520, "[FLUID] UU-Matter": 64000}]],
              # Input Buses (normal tiered)
              "Input Bus (ULV)": [["Assembler (LV)", 2, {"ULV Machine Hull": 1, "Baby Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Refined Glue": 144}],
                                  ["Assembler (LV)", 2, {"ULV Machine Hull": 1, "Baby Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polyethylene": 72}],
                                  ["Assembler (LV)", 2, {"ULV Machine Hull": 1, "Baby Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polytetrafluoroethylene": 18}],
                                  ["Assembler (LV)", 2, {"ULV Machine Hull": 1, "Baby Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 4}]],
              "Input Bus (LV)": [["Assembler (LV)", 2, {"LV Machine Hull": 1, "Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Refined Glue": 720}],
                                 ["Assembler (LV)", 2, {"LV Machine Hull": 1, "Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polyethylene": 144}],
                                 ["Assembler (LV)", 2, {"LV Machine Hull": 1, "Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polytetrafluoroethylene": 72}],
                                 ["Assembler (LV)", 2, {"LV Machine Hull": 1, "Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 9}]],
              "Input Bus (MV)": [["Assembler (MV)", 3, {"MV Machine Hull": 1, "Copper Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polyethylene": 288}],
                                 ["Assembler (MV)", 3, {"MV Machine Hull": 1, "Copper Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polytetrafluoroethylene": 144}],
                                 ["Assembler (MV)", 3, {"MV Machine Hull": 1, "Copper Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 18}]],
              "Input Bus (HV)": [["Assembler (HV)", 4, {"HV Machine Hull": 1, "Iron Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polyethylene": 432}],
                                 ["Assembler (HV)", 4, {"HV Machine Hull": 1, "Iron Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polytetrafluoroethylene": 288}],
                                 ["Assembler (HV)", 4, {"HV Machine Hull": 1, "Iron Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 36}]],
              "Input Bus (EV)": [["Assembler (EV)", 5, {"EV Machine Hull": 1, "Steel Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polytetrafluoroethylene": 576}],
                                 ["Assembler (EV)", 5, {"EV Machine Hull": 1, "Steel Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 72}]],
              "Input Bus (IV)": [["Assembler (IV)", 6, {"IV Machine Hull": 1, "Gold Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polytetrafluoroethylene": 1152}],
                                 ["Assembler (IV)", 6, {"IV Machine Hull": 1, "Gold Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 144}]],
              "Input Bus (LuV)": [["Assembler (LuV)", 7, {"LuV Machine Hull": 1, "Diamond Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polytetrafluoroethylene": 2304}],
                                  ["Assembler (LuV)", 7, {"LuV Machine Hull": 1, "Diamond Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 288}]],
              "Input Bus (ZPM)": [["Assembler (ZPM)", 8, {"ZPM Machine Hull": 1, "Crystal Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 576}]],
              "Input Bus (UV)": [["Assembler (UV)", 9, {"UV Machine Hull": 1, "Obsidian Chest": 2, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 1152}]],
              "Input Bus (UHV)": [["Assembler (UHV)", 10, {"UHV Machine Hull": 1, "Compressed Chest": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Polybenzimidazole": 2304}]],
              # Output Buses (normal tiered)
              "Output Bus (ULV)": [["Assembler (LV)", 2, {"ULV Machine Hull": 1, "Baby Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Refined Glue": 144}],
                                   ["Assembler (LV)", 2, {"ULV Machine Hull": 1, "Baby Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polyethylene": 72}],
                                   ["Assembler (LV)", 2, {"ULV Machine Hull": 1, "Baby Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polytetrafluoroethylene": 18}],
                                   ["Assembler (LV)", 2, {"ULV Machine Hull": 1, "Baby Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 4}]],
              "Output Bus (LV)": [["Assembler (LV)", 2, {"LV Machine Hull": 1, "Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Refined Glue": 720}],
                                  ["Assembler (LV)", 2, {"LV Machine Hull": 1, "Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polyethylene": 144}],
                                  ["Assembler (LV)", 2, {"LV Machine Hull": 1, "Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polytetrafluoroethylene": 72}],
                                  ["Assembler (LV)", 2, {"LV Machine Hull": 1, "Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 9}]],
              "Output Bus (MV)": [["Assembler (MV)", 3, {"MV Machine Hull": 1, "Copper Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polyethylene": 288}],
                                  ["Assembler (MV)", 3, {"MV Machine Hull": 1, "Copper Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polytetrafluoroethylene": 144}],
                                  ["Assembler (MV)", 3, {"MV Machine Hull": 1, "Copper Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 18}]],
              "Output Bus (HV)": [["Assembler (HV)", 4, {"HV Machine Hull": 1, "Iron Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polyethylene": 432}],
                                  ["Assembler (HV)", 4, {"HV Machine Hull": 1, "Iron Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polytetrafluoroethylene": 288}],
                                  ["Assembler (HV)", 4, {"HV Machine Hull": 1, "Iron Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 36}]],
              "Output Bus (EV)": [["Assembler (EV)", 5, {"EV Machine Hull": 1, "Steel Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polytetrafluoroethylene": 576}],
                                  ["Assembler (EV)", 5, {"EV Machine Hull": 1, "Steel Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 72}]],
              "Output Bus (IV)": [["Assembler (IV)", 6, {"IV Machine Hull": 1, "Gold Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polytetrafluoroethylene": 1152}],
                                  ["Assembler (IV)", 6, {"IV Machine Hull": 1, "Gold Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 144}]],
              "Output Bus (LuV)": [["Assembler (LuV)", 7, {"LuV Machine Hull": 1, "Diamond Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polytetrafluoroethylene": 2304}],
                                   ["Assembler (LuV)", 7, {"LuV Machine Hull": 1, "Diamond Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 288}]],
              "Output Bus (ZPM)": [["Assembler (ZPM)", 8, {"ZPM Machine Hull": 1, "Crystal Chest": 2, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 576}]],
              "Output Bus (UV)": [["Assembler (UV)", 9, {"UV Machine Hull": 1, "Obsidian Chest": 2, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 1152}]],
              "Output Bus (UHV)": [["Assembler (UHV)", 10, {"UHV Machine Hull": 1, "Compressed Chest": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Polybenzimidazole": 2304}]],
              "Output Bus (ME)": [["Assembler (HV)", 4, {"Output Bus (HV)": 1, "ME Interface": 1, "Acceleration Card": 4, "Programmed Circuit (1)": 0}]],
              #
              "Energized Wireless Dynamo Hatch": [["Assemblyline Process (UMV)", 13, {"UMV 65536A Laser Source Hatch": 1, "Really Ultimate Battery": 1, "UMV Circuit": 4, "Field Generator (UMV)": 1, "4x SpaceTime Wire": 16, "Active Transformer": 1, "[FLUID] Mutated Living Solder": 2880, "Excited Dimensionally Transcendent Stellar Catalyst": 8000, "Molten Shirabon": 2880}]],
              # UXV Wireless Energy Hatches (high amps)
              "UXV 256A Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV 256A Laser Target Hatch": 1, "Compact Fusion Coil MK-II Finaltype": 1, "Dyson Swarm Module Deployment Unit Superconducting Magnet": 1, "Active Transfer": 1, "High Power Casing": 64, "16x SpaceTime Wire": 64, "Dense Eternity Plate": 32, "Dense Magnetohydrodynamically Constrained Star Matter Plate": 16, "UXV Circuit": 16, "Energised Tesseract": 1, "Mutated Living Solder": 331800, "Excited Dimensionally Transcendent Stellar Catalyst": 32000}]],
              "UXV 1024A Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV 1024A Laser Target Hatch": 1, "Compact Fusion Coil MK-II Finaltype": 1, "Dyson Swarm Module Deployment Unit Superconducting Magnet": 1, "Active Transfer": 1, "High Power Casing": 64, "16x SpaceTime Wire": 64, "Dense Eternity Plate": 32, "Dense Magnetohydrodynamically Constrained Star Matter Plate": 16, "UXV Circuit": 16, "Energised Tesseract": 1, "Mutated Living Solder": 331800, "Excited Dimensionally Transcendent Stellar Catalyst": 32000}]],
              "UXV 4096A Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV 4096A Laser Target Hatch": 1, "Compact Fusion Coil MK-II Finaltype": 1, "Dyson Swarm Module Deployment Unit Superconducting Magnet": 1, "Active Transfer": 1, "High Power Casing": 64, "16x SpaceTime Wire": 64, "Dense Eternity Plate": 32, "Dense Magnetohydrodynamically Constrained Star Matter Plate": 16, "UXV Circuit": 16, "Energised Tesseract": 1, "Mutated Living Solder": 331800, "Excited Dimensionally Transcendent Stellar Catalyst": 32000}]],
              "UXV 16384A Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV 16384A Laser Target Hatch": 1, "Compact Fusion Coil MK-II Finaltype": 1, "Dyson Swarm Module Deployment Unit Superconducting Magnet": 1, "Active Transfer": 1, "High Power Casing": 64, "16x SpaceTime Wire": 64, "Dense Eternity Plate": 32, "Dense Magnetohydrodynamically Constrained Star Matter Plate": 16, "UXV Circuit": 16, "Energised Tesseract": 1, "Mutated Living Solder": 331800, "Excited Dimensionally Transcendent Stellar Catalyst": 32000}]],
              "UXV 65536A Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV 65536A Laser Target Hatch": 1, "Compact Fusion Coil MK-II Finaltype": 1, "Dyson Swarm Module Deployment Unit Superconducting Magnet": 1, "Active Transfer": 1, "High Power Casing": 64, "16x SpaceTime Wire": 64, "Dense Eternity Plate": 32, "Dense Magnetohydrodynamically Constrained Star Matter Plate": 16, "UXV Circuit": 16, "Energised Tesseract": 1, "Mutated Living Solder": 331800, "Excited Dimensionally Transcendent Stellar Catalyst": 32000}]],
              "UXV 262144A Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV 262144A Laser Target Hatch": 1, "Compact Fusion Coil MK-II Finaltype": 1, "Dyson Swarm Module Deployment Unit Superconducting Magnet": 1, "Active Transfer": 1, "High Power Casing": 64, "16x SpaceTime Wire": 64, "Dense Eternity Plate": 32, "Dense Magnetohydrodynamically Constrained Star Matter Plate": 16, "UXV Circuit": 16, "Energised Tesseract": 1, "Mutated Living Solder": 331800, "Excited Dimensionally Transcendent Stellar Catalyst": 32000}]],
              "UXV 1048576A Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV 1048576A Laser Target Hatch": 1, "Compact Fusion Coil MK-II Finaltype": 1, "Dyson Swarm Module Deployment Unit Superconducting Magnet": 1, "Active Transfer": 1, "High Power Casing": 64, "16x SpaceTime Wire": 64, "Dense Eternity Plate": 32, "Dense Magnetohydrodynamically Constrained Star Matter Plate": 16, "UXV Circuit": 16, "Energised Tesseract": 1, "Mutated Living Solder": 331800, "Excited Dimensionally Transcendent Stellar Catalyst": 32000}]],
              "UXV 4194304A Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV 4194304A Laser Target Hatch": 1, "Compact Fusion Coil MK-II Finaltype": 1, "Dyson Swarm Module Deployment Unit Superconducting Magnet": 1, "Active Transfer": 1, "High Power Casing": 64, "16x SpaceTime Wire": 64, "Dense Eternity Plate": 32, "Dense Magnetohydrodynamically Constrained Star Matter Plate": 16, "UXV Circuit": 16, "Energised Tesseract": 1, "Mutated Living Solder": 331800, "Excited Dimensionally Transcendent Stellar Catalyst": 32000}]],
              # Steam Multiblocks
              "Steam Grinder": [["Crafting", 0, {"Bronze Plated Bricks": 4, "Tumbaga Frame Box": 1, "Diamond": 2, "Industrial Diamond": 2, "Piston": 2}],
                                ["Crafting", 0, {"Bronze Plated Bricks": 4, "Tumbaga Frame Box": 1, "Industrial Diamond": 2, "Piston": 2}],
                                ["Crafting", 0, {"Bronze Plated Bricks": 4, "Tumbaga Frame Box": 1, "Diamond": 2, "Industrial Diamond": 2, "Sticky Piston": 2}],
                                ["Crafting", 0, {"Bronze Plated Bricks": 4, "Tumbaga Frame Box": 1, "Industrial Diamond": 2, "Sticky Piston": 2}]],
              "Steam Squasher": [["Crafting", 0, {"Bronze Plated Bricks": 4, "Tumbaga Gear": 2, "Piston": 2, "Tumbaga Frame Box": 1}],
                                 ["Crafting", 0, {"Bronze Plated Bricks": 4, "Tumbaga Gear": 2, "Sticky Piston": 2, "Tumbaga Frame Box": 1}]],
              "Steam Separator": [["Crafting", 0, {"Bronze Plated Bricks": 4, "Bronze Gear": 2, "Wrought Iron Plate": 2, "Tumbaga Frame Box": 1}]],
              "Steam Purifier": [["Crafting", 0, {"Bronze Plated Bricks": 4, "Tin Rotor": 2, "Wrought Iron Plate": 2, "Tumbaga Frame Box": 1}]],
              "Steam Presser": [["Crafting", 0, {"Bronze Plated Bricks": 4, "Anvil": 1, "Wrought Iron Plate": 3, "Tumbaga Frame Box": 1}]],
              "Steam Blender": [["Crafting", 0, {"Bronze Plated Bricks": 4, "Tumbaga Frame Box": 1, "Tumbaga Rotor": 2, "Tumbaga Ring": 2}]], #####
              "Steam Fuser": [["Crafting", 0, {"Bronze Plated Bricks": 4, "Blast Furnace": 2, "Tiny Bronze Fluid Pipe": 1, "Large Bronze Fluid Pipe": 1, "Tumbaga Frame Box": 1}]],
              # Wireless Energy Hatches (normal tiered)
              "ULV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"ULV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "MV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "LV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"LV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "Advanced Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "MV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"MV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "EV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "HV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"HV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "IV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "EV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"EV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "LuV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "IV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"IV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "ZPM Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "LuV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"LuV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "UV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "ZPM Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"ZPM Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "UHV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "UV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "UEV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "UHV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UHV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "UIV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "UEV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UEV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "UMV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "UIV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UIV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "UXV Circuit": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "UMV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UMV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "UXV Circuit": 4, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              "UXV Wireless Energy Hatch": [["Assemblyline Process (UMV)", 13, {"UXV Energy Hatch": 1, "Ameliorated Superconduct Coil": 1, "Superconducting Coil Block": 1, "Active Transformer": 1, "High Power Casing": 2, "1x SpaceTime Wire": 2, "Dense Infinity Plate": 1, "UXV Circuit": 16, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 1296, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 500}]],
              #"MAX Wireless Energy Hatch" it does not have a recipe lmfao
              "LuV Beamline Input Hatch": [["Assemblyline Process (LuV)", 7, {"LuV Machine Hull": 1, "LuV Circuit": 2, "Capillary Exchange": 2, "Electric Pump (LuV)": 1, "Beamline Pipe": 1, "Mu-metal Plate": 4, "Molten Soldering Alloy": 6000, "Argon": 1000, "Helium": 2000}]],
              "LuV Beamline Output Hatch": [["Assemblyline Process (LuV)", 7, {"LuV Machine Hull": 1, "LuV Circuit": 6, "Capillary Exchange": 4, "Electric Pump (LuV)": 2, "Electric Motor (LuV)": 4, "1x Superconductor LuV Wire": 8, "Beamline Pipe": 1, "Mu-metal Plate": 8, "Molten Soldering Alloy": 8000, "Argon": 1000, "Helium": 6000}]],
              "Humongous Input Hatch": [["Assembler (UMV)", 13, {"Input Hatch (UXV)": 1, "Quantum Tank V": 1, "[FLUID] Spatially Enlarged Fluid": 5760}]],
              "Humonogous Quadruple Input Hatch": [["Assembler (UXV)", 14, {"Huge SpaceTime Fluid Pipe": 4, "Humnogous Input Hatch": 1, "Programmed Circuit (4)": 0, "[FLUID] Spatially Enlarged Fluid": 5760}]],
              # Quadruple Input Hatch
              "Quadruple Input Hatch (EV)": [["Assembler (EV)", 5, {"Quadruple Stainless Steel Fluid Pipe": 1, "EV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Glass": 2304}]],
              "Quadruple Input Hatch (IV)": [["Assembler (IV)", 6, {"Quadruple Titanium Fluid Pipe": 1, "IV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Glass": 2304}]],
              "Quadruple Input Hatch (LuV)": [["Assembler (LuV)", 7, {"Quadruple Tungstensteel Fluid Pipe": 1, "LuV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Polytetrafluoroethylene": 2304}]],
              "Quadruple Input Hatch (ZPM)": [["Assembler (ZPM)", 8, {"Quadruple Niobium-Titanium Fluid Pipe": 1, "ZPM Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Polytetrafluoroethylene": 2304}]],
              "Quadruple Input Hatch (UV)": [["Assembler (UV)", 9, {"Quadruple Mysterious Crystal Fluid Pipe": 1, "UV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Polybenzimidazole": 2304}]],
              "Quadruple Input Hatch (UHV)": [["Assembler (UHV)", 10, {"Quadruple Neutronium Fluid Pipe": 1, "UHV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Polybenzimidazole": 2304}]],
              "Quadruple Input Hatch (UEV)": [["Assembler (UEV)", 11, {"Quadruple Infinity Fluid Pipe": 1, "UEV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Polybenzimidazole": 2304}]],
              "Quadruple Input Hatch (UIV)": [["Assembler (UIV)", 12, {"Quadruple Transcendent Metal Fluid Pipe": 1, "UIV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Polybenzimidazole": 2304}]],
              "Quadruple Input Hatch (UMV)": [["Assembler (UMV)", 13, {"Quadruple SpaceTime Fluid Pipe": 1, "UMV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Polybenzimidazole": 2304}]],
              "Quadruple Input Hatch (UXV)": [["Assembler (UXV)", 14, {"Quadruple SpaceTime Fluid Pipe": 4, "UXV Machine Hull": 1, "Programmed Circuit (4)": 0, "[FLUID] Molten Polybenzimidazole": 2304}]],
              #"MAX Machine Hull" no recipe but stuff uses it... (7 things below)
              "Input Hatch (MAX)": [["Assembler (MAX)", 15, {"MAX Machine Hull": 1, "Quantum Tank II": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Radox Polymer": 72}]],
              "Output Hatch (MAX)": [["Assembler (MAX)", 15, {"MAX Machine Hull": 1, "Quantum Tank II": 1, "Programmed Circuit (2)": 0, "[FLUID] Molten Radox Polymer": 72}]],
              "Energy Distributor MAX": [["Crafting", 0, {"SpaceTime Plate": 4, "16x Awakened Draconium Wire": 4, "MAX Machine Hull": 1}]],
              "Cable Diode 2A MAX": [["Crafting", 0, {"SpaceTime Plate": 2, "2x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "Diode": 4}],
                                     ["Crafting", 0, {"SpaceTime Plate": 2, "2x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "SMD Diode": 4}]],
              "Cable Diode 4A MAX": [["Crafting", 0, {"SpaceTime Plate": 2, "4x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "Diode": 4}],
                                     ["Crafting", 0, {"SpaceTime Plate": 2, "4x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "SMD Diode": 4}]],
              "Cable Diode 8A MAX": [["Crafting", 0, {"SpaceTime Plate": 2, "8x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "Diode": 4}],
                                     ["Crafting", 0, {"SpaceTime Plate": 2, "8x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "SMD Diode": 4}]],
              "Cable Diode 12A MAX": [["Crafting", 0, {"SpaceTime Plate": 2, "12x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "Diode": 4}],
                                      ["Crafting", 0, {"SpaceTime Plate": 2, "12x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "SMD Diode": 4}]],
              "Cable Diode 16A MAX": [["Crafting", 0, {"SpaceTime Plate": 2, "16x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "Diode": 3, "SMD Inductor": 1}],
                                      ["Crafting", 0, {"SpaceTime Plate": 2, "16x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "SMD Diode": 3, "SMD Inductor": 1}],
                                      ["Crafting", 0, {"SpaceTime Plate": 2, "16x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "Diode": 3, "Small Coil": 1}],
                                      ["Crafting", 0, {"SpaceTime Plate": 2, "16x Awakened Draconium Wire": 2, "MAX Machine Hull": 1, "SMD Diode": 3, "Small Coil": 1}]],
              "Black Hole Utility Hatch": [["Assembler (UIV)", 12, {"UIV Machine Hull": 1, "Redstone Singularity": 1, "Sensor (UIV)": 2, "Superdense Redstone Alloy Plate": 16, "[FLUID] Dimensionally Shifted Superfluid": 16000}]],
              # Maintenance Hatches
              "Maintenance Hatch": [["Crafting", 0, {"LV Machine Hull": 1, "{Screwdriver Use}": 1, "{Wrench Use}": 1, "{Wirecutters Use}": 1, "{Hammer Use}": 1, "{Soft Mallet Use}": 1, "{Crowbar Use}": 1, "{File Use}": 1, "{Saw Use}": 1}],
                                    ["Assembler (LV)", 2, {"LV Machine Hull": 1, "BrainTech Aerospace Advanced Reinforced Duct Tape FAL-84": 1, "Programmed Circuit (1)": 0, "[FLUID] Ethyl Cyanoacrylate (Super Glue)": 100}],
                                    ["Assembler (LV)", 2, {"LV Machine Hull": 1, "BrainTech Aerospace Advanced Reinforced Duct Tape FAL-84": 2, "Programmed Circuit (3)": 0, "[FLUID] Advanced Glue": 200}],
                                    ["Assembler (LV)", 2, {"LV Machine Hull": 1, "BrainTech Aerospace Advanced Reinforced Duct Tape FAL-84": 2, "Programmed Circuit (2)": 0, "[FLUID] Refined Glue": 1000}]],
              "Auto Maintenance Hatch": [["Crafting", 0, {"LuV Machine Hatch": 1, "Maintenance Hatch": 2, "ZPM Circuit": 4, "Robot Arm (LuV)": 2}]],
              "Auto-Taping Maintenance Hatch": [["Assemblyline Process (UV)", 9, {"Auto Maintenance Hatch": 1, "Robot Atm (UV)": 1, "Electric Pump (UV)": 1, "Conveyor Module (UV)": 1, "UV Circuit": 4, "Lapotronic Energy Ord Cluster": 1, "BrainTech Aerospace Advanced Reinforced Duct Tape FAL-84": 128, "Fine Americium Wire": 64, "[FLUID] Lubricant": 256000, "[FLUID] Molten Indalloy 140": 1296}]],
              "Wireless Needs Maintenance Hatch": [["Assembler (MV)", 3, {"Needs Maintenance Hatch": 1, "Emitter (UV)": 1, "Programmed Circuit (1)": 0}]],
              "Needs Maintenance Hatch": [["Assembler (LV)", 2, {"Emitter (MV)": 1, "Aluminium Plate": 1, "Programmed Circuit (1)": 0}]],
              # Electric Motors
              "Electric Motor (LV)": [["Crafting", 0, {"1x Tin Cable": 2, "1x Copper Wire": 4, "Iron Rod": 2, "Magnetic Iron Rod": 1}],
                                      ["Crafting", 0, {"1x Tin Cable": 2, "1x Copper Wire": 4, "Wrought Iron Rod": 2, "Magnetic Iron Rod": 1}],
                                      ["Crafting", 0, {"1x Tin Cable": 2, "1x Copper Wire": 4, "Pig Iron Rod": 2, "Magnetic Iron Rod": 1}],
                                      ["Crafting", 0, {"1x Tin Cable": 2, "1x Annealed Copper Wire": 4, "Iron Rod": 2, "Magnetic Iron Rod": 1}],
                                      ["Crafting", 0, {"1x Tin Cable": 2, "1x Annealed Copper Wire": 4, "Wrought Iron Rod": 2, "Magnetic Iron Rod": 1}],
                                      ["Crafting", 0, {"1x Tin Cable": 2, "1x Annealed Copper Wire": 4, "Pig Iron Rod": 2, "Magnetic Iron Rod": 1}],
                                      ["Crafting", 0, {"1x Tin Cable": 2, "1x Copper Wire": 4, "Steel Rod": 2, "Magnetic Steel Rod": 1}],
                                      ["Crafting", 0, {"1x Tin Cable": 2, "1x Annealed Copper Wire": 4, "Steel Rod": 2, "Magnetic Steel Rod": 1}],
                                      #["Sifter (LV)", 2, {"Lump of Electronics": 1}],  # includes chances
                                      ["Assembler (LV)", 2, {"1x Tin Cable": 2, "1x Copper Wire": 4, "Iron Rod": 2, "Magnetic Iron Rod": 1}],
                                      ["Assembler (LV)", 2, {"1x Tin Cable": 2, "1x Copper Wire": 4, "Steel Rod": 2, "Magnetic Steel Rod": 1}],
                                      ["Assembler (LV)", 2, {"1x Tin Cable": 2, "1x Annealed Copper Wire": 4, "Iron Rod": 2, "Magnetic Iron Rod": 1}],
                                      ["Assembler (LV)", 2, {"1x Tin Cable": 2, "1x Annealed Copper Wire": 4, "Steel Rod": 2, "Magnetic Steel Rod": 1}],
                                      ["Component Assembly Line (LV)", 2, {"Long Magnetic Iron Rod": 24, "Long Iron Rod": 48, "16x Copper Wire": 12, "16x Tin Cable": 6}, {"Electric Motor (LV)": 64}],
                                      ["Component Assembly Line (LV)", 2, {"Long Magnetic Steel Rod": 24, "Long Steel Rod": 48, "16x Copper Wire": 12, "16x Tin Cable": 6}, {"Electric Motor (LV)": 64}],
                                      ["Component Assembly Line (LV)", 2, {"Long Magnetic Iron Rod": 24, "Long Iron Rod": 48, "16x Annealed Copper Wire": 12, "16x Tin Cable": 6}, {"Electric Motor (LV)": 64}],
                                      ["Component Assembly Line (LV)", 2, {"Long Magnetic Steel Rod": 24, "Long Steel Rod": 48, "16x Annealed Copper Wire": 12, "16x Tin Cable": 6}, {"Electric Motor (LV)": 64}]],
              "Electric Motor (MV)": [["Crafting", 0, {"Magnetic Steel Rod": 1, "Aluminium Rod": 2, "1x Cupronickel Wire": 4, "1x Copper Cable": 2}],
                                      ["Crafting", 0, {"Magnetic Steel Rod": 1, "Aluminium Rod": 2, "1x Cupronickel Wire": 4, "1x Annealed Copper Cable": 2}],
                                      ["Assembler (LV)", 2, {"Magnetic Steel Rod": 1, "Aluminium Rod": 2, "1x Cupronickel Wire": 4, "1x Copper Cable": 2}],
                                      ["Assembler (LV)", 2, {"Magnetic Steel Rod": 1, "Aluminium Rod": 2, "1x Cupronickel Wire": 4, "1x Annealed Copper Cable": 2}],
                                      ["Component Assembly Line (LV)", 2, {"Long Magnetic Steel Rod": 24, "Long Aluminium Rod": 48, "16x Cupronickel Wire": 24, "16x Copper Cable": 6}, {"Electric Motor (MV)": 64}],
                                      ["Component Assembly Line (LV)", 2, {"Long Magnetic Steel Rod": 24, "Long Aluminium Rod": 48, "16x Cupronickel Wire": 24, "16x Annealed Copper Cable": 6}, {"Electric Motor (MV)": 64}]],
              "Electric Motor (HV)": [["Crafting", 0, {"Magnetic Steel Rod": 1, "Stainless Steel Rod": 2, "4x Electrum Wire": 4, "2x Silver Cable": 2}],
                                      ["Assembler (LV)", 2, {"Magnetic Steel Rod": 1, "Stainless Steel Rod": 2, "4x Electrum Wire": 4, "2x Silver Cable": 2}],
                                      ["Component Assembly Line (MV)", 3, {"Long Magnetic Steel Rod": 24, "Long Stainless Steel Rod": 48, "16x Electrum Wire": 48, "16x Silver Cable": 12}, {"Electric Motor (HV)": 64}]],
              "Electric Motor (EV)": [["Crafting", 0, {"Magnetic Neodymium Rod": 1, "Titanium Rod": 2, "4x Black Steel Wire": 4, "2x Aluminium Cable": 2}],
                                      ["Assembler (LV)", 2, {"Magnetic Neodymium Rod": 1, "Titanium Rod": 2, "4x Black Steel Wire": 4, "2x Aluminium Cable": 2}],
                                      ["Component Assembly Line (HV)", 4, {"Long Magnetic Neodymium Rod": 24, "Long Titanium": 48, "16x Black Steel Wire": 48, "16x Aluminium Cable": 12}, {"Electric Motor (EV)": 64}]],
              "Electric Motor (IV)": [["Crafting", 0, {"Magnetic Neodymium Rod": 1, "Tungstensteel Rod": 2, "4x Graphene Wire": 4, "2x Tungsten Cable": 2}],
                                      ["Assembler (LV)", 2, {"Magnetic Neodymium Rod": 1, "Tungstensteel Rod": 2, "4x Graphene Wire": 4, "2x Tungsten Cable": 2}],
                                      ["Component Assembly Line (EV)", 5, {"Long Magnetic Neodymium Rod": 24, "Long Tungstensteel Rod": 48, "16x Graphene Wire": 48, "16x Tungsten Cable": 12}, {"Electric Motor (IV)": 64}]],
              "Electric Motor (LuV)": [["Assemblyline Process (IV)", 6, {"Magnetic Samarium Rod": 1, "Long HSS-S Rod": 2, "Fine Ruridit Wire": 128, "2x Yttrium Barium Cuprate Cable": 2, "[FLUID] Molten Indalloy 140": 144, "[FLUID] Lubricant": 250}],
                                       ["Component Assembly Line (IV)", 6, {"Long Magnetic Samarium Rod": 24, "[FLUID] Molten HSS-S": 13824, "Molten Ruridit": 110600, "16x Yttrium Barium Cuprate Cable": 6, "[FLUID] Molten Indalloy 140": 6912, "[FLUID] Lubricant": 12000, "Programmable Circuit (1)": 0}, {"Electric Motor (LuV)": 64}]],
              "Electric Motor (ZPM)": [["Assemblyline Process (LuV)", 7, {"Magnetic Samarium Rod": 2, "Long Naquadah Alloy Rod": 4, "Naquadah Alloy Ring": 4, "Naquadah Alloy Round": 16, "Fine Europium Wire": 192, "2x Vanadium-Gallium Cable": 2, "[FLUID] Molten Indalloy 140": 288, "[FLUID] Lubricant": 750}],
                                       ["Component Assembly Line (LuV)", 7, {"Long Magnetic Samarium Rod": 48, "[FLUID] Molten Naquadah Alloy": 46848, "Molten Europium": 165900, "16x Vanadium-Gallium Cable": 24, "[FLUID] Molten Indalloy 140": 13824, "[FLUID] Lubricant": 36000, "Programmable Circuit (1)": 0}, {"Electric Motor (ZPM)": 64}]],
              "Electric Motor (UV)": [["Assemblyline Process (ZPM)", 8, {"Long Magnetic Samarium Rod": 2, "Long Neutronium Rod": 4, "Neutronium Ring": 4, "Neutronium Round": 16, "Fine Europium Wire": 384, "4x Naquadah Alloy Cable": 2, "[FLUID] Molten Indalloy 140": 1296, "[FLUID] Lubricant": 2000, "[FLUID] Molten Naquadria": 1296}],
                                      ["Component Assembly Line (ZPM)", 8, {"16x Naquadah Alloy Cable": 24, "Programmable Circuit (1)": 0, "[FLUID] Molten Indalloy 140": 62208, "[FLUID] Lubricant": 96000, "[FLUID] Molten Americium": 331800, "[FLUID] Molten Naquadria": 62208, "[FLUID] Molten Neutronium": 46848, "[FLUID] Molten Samarium": 13824}, {"Electric Motor (UV)": 64}]],
              "Electric Motor (UHV)": [["Assemblyline Process (UV)", 9, {"Long Magnetic Samarium Rod": 4, "Long Cosmic Neutronium Rod": 8, "Cosmic Neutronium Ring": 8, "Cosmic Neutronium Round": 32, "Fine Neutronium Wire": 512, "4x Bedrockium Cable": 2, "[FLUID] Molten Indalloy 140": 2592, "[FLUID] Lubricant": 4000, "[FLUID] Molten Naquadria": 2592}],
                                       ["Component Assembly Line (UV)", 9, {"16x Bedrockium Cable": 24, "Programmable Circuit (1)": 0, "[FLUID] Molten Indalloy 140": 124400, "[FLUID] Lubricant": 192000, "[FLUID] Molten Neutronium": 442400, "[FLUID] Molten Naquadria": 124400, "[FLUID] Molten Cosmic Neutronium": 93696, "[FLUID] Molten Samarium": 27648}, {"Electric Motor (UHV)": 64}]],
              "Electric Motor (UEV)": [["Assemblyline Process (UHV)", 10, {"Long Attuned Tengam Rod": 8, "Long Infinity Rod": 16, "Infinity Ring": 8, "Infinity Round": 32, "Fine Cosmic Neutronium Wire": 512, "2x Draconium Cable": 2, "[FLUID] Mutated Living Solder": 2592, "[FLUID] Lubricant": 4000, "[FLUID] Molten Quantium": 2592}],
                                       ["Component Assembly Line (UHV)", 10, {"16x Draconium Cable": 24, "Programmable Circuit (1)": 0, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Lubricant": 192000, "[FLUID] Molten Cosmic Neutronium": 442400, "[FLUID] Molten Infinity": 129000, "[FLUID] Molten Quantium": 124400, "[FLUID] Molten Purified Tengam": 55296}, {"Electric Motor (UEV)": 64}]],
              "Electric Motor (UIV)": [["Assemblyline Process (UEV)", 11, {"Long Attuned Tengam Rod": 16, "Long Transcendent Metal Rod": 16, "Transcendent Metal Ring": 8, "Transcendent Metal Round": 32, "Fine Proto-Halkonite Wire": 512, "2x Nether Star Cable": 2, "[FLUID] Molten Celestial Tungsten": 576, "[FLUID] Mutated Living Solder": 2592, "[FLUID] Dimensionally Shifted Superfluid": 4000}],
                                       ["Component Assembly Line (UEV)", 11, {"16x Nether Star Cable": 24, "Programmable Circuit (1)": 0, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Dimensionally Shifted Superfluid": 302600, "[FLUID] Molten Proto-Halkonite Steel Base": 442400, "[FLUID] Molten Infinity": 442400, "[FLUID] Molten Transcendent Metal": 149000, "[FLUID] Molten Purified Tengam": 110600, "[FLUID] Molten Celestial Tungsten": 27648}, {"Electric Motor (UIV)": 64}],
                                       ["Component Assembly Line (UEV)", 11, {"16x Nether Star Cable": 24, "Programmable Circuit (1)": 0, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Dimensionally Shifted Superfluid": 302600, "[FLUID] Molten Proto-Halkonite Steel Base": 221200, "[FLUID] Molten Creon": 221200, "[FLUID] Molten Mellion": 221200, "[FLUID] Molten Transcendent Metal": 149000, "[FLUID] Molten Purified Tengam": 110600, "[FLUID] Molten Celestial Tungsten": 27648}, {"Electric Motor (UIV)": 64}]],
              "Electric Motor (UMV)": [["Assemblyline Process (UIV)", 12, {"Long Attuned Tengam Rod": 32, "Long SpaceTime Rod": 16, "SpaceTime Ring": 8, "SpaceTime Round": 32, "Fine Hypogen Wire": 512, "4x Quantium Cable": 2, "[FLUID] Molten Hypogen": 576, "[FLUID] Molten Celestial Tungsten": 576, "[FLUID] Mutated Living Solder": 2592, "[FLUID] Dimensionally Shifted Superfluid": 4000}],
                                       ["Component Assembly Line (UIV)", 12, {"16x Quantium Cable": 24, "Programmable Circuit (1)": 0, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Dimensionally Shifted Superfluid": 192000, "[FLUID] Molten Hypogen": 470000, "[FLUID] Molten Purified Tengam": 221200, "[FLUID] Molten SpaceTime": 149000, "[FLUID] Molten Celestial Tungsten": 27648}, {"Electric Motor (UMV)": 64}]],
              "Electric Motor (UXV)": [["Assemblyline Process (UMV)", 13, {"Energised Tesseract": 1, "Long Magnetohydrodynamically Constrained Star Matter Rod": 16, "Magnetohydrodynamically Constrained Star Matter Ring": 8, "Magnetohydrodynamically Constrained Star Matter Round": 32, "Fine Superconductor Base UMV Wire": 128, "Fine Magnetohydrodynamically Constrained Star Matter Wire": 128, "Fine Universium Wire": 128, "Fine Magmatter Wire": 128, "4x SpaceTime Wire": 4, "Neutronium Nanites": 4, "[FLUID] Molten Magnetohydrodynamically Constrained Star Matter": 576, "[FLUID] Molten SpaceTime": 576, "[FLUID] Mutated Universium": 576, "[FLUID] Dimensionally Shifted Superfluid": 8000}],
                                       ["Component Assembly Line (UMV)", 13, {"Energised Tesseract": 48, "Wrap of UHV Circuit": 114, "16x SpaceTime Wire": 48, "Gold Nanites": 12, "Programmable Circuit (1)": 0, "[FLUID] Dimensionally Shifted Superfluid": 384000, "[FLUID] Molten Magnetohydrodynamically Constrained Star Matter": 287200, "[FLUID] Molten Eternity": 259600, "[FLUID] Molten Universium": 138200, "[FLUID] Molten Magmatter": 110600, "[FLUID] Molten Superconductor Base UMV": 110600, "[FLUID] Molten SpaceTime": 27648}, {"Electric Motor (UXV)": 64}]],
              # Circuit Wraps
              "Wrap of ULV Circuits": [["Assembler (LV)", 2, {"ULV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of LV Circuits": [["Assembler (LV)", 2, {"LV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of MV Circuits": [["Assembler (LV)", 2, {"MV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of HV Circuits": [["Assembler (LV)", 2, {"HV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of EV Circuits": [["Assembler (LV)", 2, {"EV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of IV Circuits": [["Assembler (LV)", 2, {"IV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of LuV Circuits": [["Assembler (LV)", 2, {"LuV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of ZPM Circuits": [["Assembler (LV)", 2, {"ZPM Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of UV Circuits": [["Assembler (LV)", 2, {"UV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of UHV Circuits": [["Assembler (LV)", 2, {"UHV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of UEV Circuits": [["Assembler (LV)", 2, {"UEV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of UIV Circuits": [["Assembler (LV)", 2, {"UIV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of UMV Circuits": [["Assembler (LV)", 2, {"UMV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              "Wrap of UXV Circuits": [["Assembler (LV)", 2, {"UXV Circuit": 16, "Programmed Circuit (16)": 0, "[FLUID] Molten Soldering Alloy": 72}]],
              # Electric Pistons
              "Electric Piston (LV)": [["Crafting", 0, {"Steel Plate": 3, "Steel Rod": 2, "1x Tin Cable": 2, "Electric Motor (LV)": 1, "Small Steel Gear": 1}],
                                       ["Assembler (LV)", 2, {"Steel Plate": 3, "Steel Rod": 2, "1x Tin Cable": 2, "Electric Motor (LV)": 1, "Small Steel Gear": 1}],
                                       ["Component Assembly Line (LV)", 2, {"Steel Plate": 16, "Long Steel Rod": 48, "16x Tin Cable": 2, "Electric Motor (LV)": 48, "Steel Gear": 12}, {"Electric Piston (LV)": 64}]],
              "Electric Piston (MV)": [["Crafting", 0, {"Aluminium Plate": 3, "Aluminium Rod": 2, "1x Copper Cable": 2, "Electric Motor (MV)": 1, "Small Aluminium Gear": 1}],
                                       ["Assembler (LV)", 2, {"Aluminium Plate": 3, "Aluminium Rod": 2, "1x Copper Cable": 2, "Electric Motor (MV)": 1, "Small Aluminium Gear": 1}],
                                       ["Component Assembly Line (LV)", 2, {"Aluminium Plate": 16, "Long Aluminium Rod": 48, "16x Copper Cable": 2, "Electric Motor (MV)": 48, "Aluminium Gear": 12}, {"Electric Piston (MV)": 64}]],
              "Electric Piston (HV)": [["Crafting", 0, {"Stainless Steel Plate": 3, "Stainless Steel Rod": 2, "1x Copper Cable": 2, "Electric Motor (HV)": 1, "Small Stainless Steel Gear": 1}],
                                       ["Assembler (LV)", 2, {"Stainless Steel Plate": 3, "Stainless Steel Rod": 2, "1x Copper Cable": 2, "Electric Motor (HV)": 1, "Small Stainless Steel Gear": 1}],
                                       ["Component Assembly Line (MV)", 3, {"Stainless Steel Plate": 16, "Long Stainless Steel Rod": 48, "16x Copper Cable": 2, "Electric Motor (HV)": 48, "Stainless Steel Gear": 12}, {"Electric Piston (HV)": 64}]],
              "Electric Piston (EV)": [["Crafting", 0, {"Titanium Plate": 3, "Titanium Rod": 2, "1x Aluminium Cable": 2, "Electric Motor (EV)": 1, "Small Titanium Gear": 1}],
                                       ["Assembler (LV)", 2, {"Titanium Plate": 3, "Titanium Rod": 2, "1x Aluminium Cable": 2, "Electric Motor (EV)": 1, "Small Titanium Gear": 1}],
                                       ["Component Assembly Line (HV)", 4, {"Titanium Plate": 16, "Long Titanium Rod": 48, "16x Aluminium Cable": 2, "Electric Motor (EV)": 48, "Titanium Gear": 12}, {"Electric Piston (EV)": 64}]],
              "Electric Piston (IV)": [["Crafting", 0, {"Tungstensteel Plate": 3, "Tungstensteel Rod": 2, "1x Tungsten Cable": 2, "Electric Motor (IV)": 1, "Small Tungstensteel Gear": 1}],
                                       ["Assembler (LV)", 2, {"Tungstensteel Plate": 3, "Tungstensteel Rod": 2, "1x Tungsten Cable": 2, "Electric Motor (IV)": 1, "Small Tungstensteel Gear": 1}],
                                       ["Component Assembly Line (EV)", 5, {"Tungstensteel Plate": 16, "Long Tungstensteel Rod": 48, "16x Tungsten Cable": 2, "Electric Motor (IV)": 48, "Tungstensteel Gear": 12}, {"Electric Piston (IV)": 64}]],
              "Electric Piston (LuV)": [["Assemblyline Process (IV)", 6, {"Electric Motor (LuV)": 1, "HSS-S Plate": 6, "HSS-S Ring": 4, "HSS-S Round": 32, "HSS-S Rod": 4, "HSS-S Gear": 1, "Small HSS-S Gear": 2, "1x Yttrium Barium Cuprate Cable": 4, "[FLUID] Molten Indalloy 140": 144, "[FLUID] Lubricant": 250}],
                                        ["Component Assembly Line (IV)", 6, {"Electric Motor (LuV)": 48, "Dense HSS-S Plate": 32, "16x Yttrium Barium Cuprate Cable": 12, "Programmable Circuit (2)": 0, "[FLUID] Molten Indalloy 140": 6912, "[FLUID] Lubricant": 12000, "[FLUID] Molten HSS-S": 86784}, {"Electric Piston (LuV)": 64}]],
              "Electric Piston (ZPM)": [["Assemblyline Process (LuV)", 7, {"Electric Motor (ZPM)": 1, "Naquadah Plate": 6, "Naquadah Ring": 4, "Naquadah Round": 32, "Naquadah Rod": 4, "Naquadah Gear": 1, "Small Naquadah Gear": 2, "4x Vanadium-Gallium Cable": 4, "[FLUID] Molten Indalloy 140": 288, "[FLUID] Lubricant": 750}],
                                        ["Component Assembly Line (LuV)", 7, {"Electric Motor (ZPM)": 48, "Dense Naquadah Plate": 32, "16x Vanadium-Gallium Cable": 48, "Programmable Circuit (2)": 0, "[FLUID] Molten Indalloy 140": 13824, "[FLUID] Lubricant": 36000, "[FLUID] Molten Naquadah": 86784}, {"Electric Piston (ZPM)": 64}]],
              "Electric Piston (UV)": [["Assemblyline Process (ZPM)", 8, {"Electric Motor (UV)": 1, "Neutronium Plate": 6, "Neutronium Ring": 4, "Neutronium Round": 32, "Neutronium Rod": 4, "Neutronium Gear": 1, "Small Neutronium Gear": 2, "4x Naquadah Alloy Cable": 4, "[FLUID] Molten Naquadria": 1296, "[FLUID] Molten Indalloy 140": 1296, "[FLUID] Lubricant": 2000}],
                                       ["Component Assembly Line (ZPM)", 8, {"Electric Motor (UV)": 48, "Dense Neutronium Plate": 32, "16x Naquadah Alloy Cable": 48, "Programmable Circuit (2)": 0, "[FLUID] Molten Indalloy 140": 62208, "[FLUID] Lubricant": 96000, "[FLUID] Molten Neutronium": 86784, "[FLUID] Molten Naquadria": 62208}, {"Electric Piston (UV)": 64}]],
              "Electric Piston (UHV)": [["Assemblyline Process (UV)", 9, {"Electric Motor (UHV)": 1, "Cosmic Neutronium Plate": 6, "Cosmic Neutronium Ring": 8, "Cosmic Neutronium Round": 64, "Cosmic Neutronium Rod": 8, "Cosmic Neutronium Gear": 2, "Small Cosmic Neutronium Gear": 4, "4x Bedrockium Cable": 4, "[FLUID] Molten Naquadria": 2592, "[FLUID] Molten Indalloy 140": 2592, "[FLUID] Lubricant": 4000}],
                                        ["Component Assembly Line (UV)", 9, {"Electric Motor (UHV)": 48, "Dense Cosmic Neutronium Plate": 32, "16x Bedrockium Cable": 48, "Programmable Circuit (2)": 0, "[FLUID] Molten Indalloy 140": 124400, "[FLUID] Lubricant": 192000, "[FLUID] Molten Cosmic Neutronium": 173600, "[FLUID] Molten Naquadria": 124400}, {"Electric Piston (UHV)": 64}]],
              "Electric Piston (UEV)": [["Assemblyline Process (UHV)", 10, {"Electric Motor (UEV)": 1, "Infinity Plate": 6, "Infinity Ring": 8, "Infinity Round": 64, "Infinity Rod": 8, "Infinity Gear": 2, "Small Infinity Gear": 4, "4x Draconium Cable": 4, "[FLUID] Molten Naquadria": 2592, "[FLUID] Molten Indalloy 140": 2592, "[FLUID] Lubricant": 4000}],
                                        ["Component Assembly Line (UHV)", 10, {"Electric Motor (UEV)": 48, "Dense Infinity Plate": 32, "16x Draconium Cable": 48, "Programmable Circuit (2)": 0, "[FLUID] Molten Indalloy 140": 124400, "[FLUID] Lubricant": 192000, "[FLUID] Molten Infinity": 173600, "[FLUID] Molten Quantium": 124400}, {"Electric Piston (UEV)": 64}]],
              "Electric Piston (UIV)": [["Assemblyline Process (UEV)", 11, {"Electric Motor (UIV)": 1, "Transcendent Metal Plate": 6, "Transcendent Metal Ring": 8, "Transcendent Metal Round": 64, "Transcendent Metal Rod": 8, "Transcendent Metal Gear": 2, "Small Transcendent Metal Gear": 4, "4x Nether Star Cable": 4, "[FLUID] Molten Celestial Tungsten": 576, "[FLUID] Mutated Living Solder": 2592, "[FLUID] Dimensionally Shifted Superfluid": 4000}],
                                        ["Component Assembly Line (UEV)", 11, {"Electric Motor (UIV)": 48, "Dense Transcendent Metal Plate": 32, "16x Nether Star Cable": 48, "Programmable Circuit (2)": 0, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Dimensionally Shifted Superfluid": 192000, "[FLUID] Molten Transcendent Metal": 173600, "[FLUID] Molten Celestial Tungsten": 27648}, {"Electric Piston (UIV)": 64}]],
              "Electric Piston (UMV)": [["Assemblyline Process (UIV)", 12, {"Electric Motor (UMV)": 1, "SpaceTime Plate": 6, "SpaceTime Ring": 8, "SpaceTime Round": 64, "SpaceTime Rod": 8, "SpaceTime Gear": 2, "Small SpaceTime Gear": 4, "4x Quantium Cable": 4, "[FLDID] Molten Hypogen": 576, "[FLUID] Molten Celestial Tungsten": 576, "[FLUID] Mutated Living Solder": 2592, "[FLUID] Dimensionally Shifted Superfluid": 4000}],
                                        ["Component Assembly Line (UIV)", 12, {"Electric Motor (UMV)": 48, "Dense SpaceTime Plate": 32, "16x Quantium Cable": 48, "Programmable Circuit (2)": 0, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Dimensionally Shifted Superfluid": 192000, "[FLUID] Molten SpaceTime": 173600, "[FLUID] Molten Hypogen": 27648, "[FLUID] Molten Celestial Tungsten": 27648}, {"Electric Piston (UMV)": 64}]],
              "Electric Piston (UXV)": [["Assemblyline Process (UMV)", 13, {"Electric Motor (UXV)": 1, "Magnetohydrodynamically Constrained Star Matter Plate": 6, "Magnetohydrodynamically Constrained Star Matter Ring": 8, "Magnetohydrodynamically Constrained Star Matter Round": 64, "Magnetohydrodynamically Constrained Star Matter Rod": 8, "Magnetohydrodynamically Constrained Star Matter Gear": 2, "Magmatter Gear": 2, "Small Magnetohydrodynamically Constrained Star Matter Gear": 4, "Small Magmatter Gear": 4, "4x SpaceTime Wire": 8, "Neutronium Nanites": 4, "[FLDID] Molten Magnetohydrodynamically Constrained Star Matter": 576, "[FLUID] Molten SpaceTime": 576, "[FLUID] Mutated Universium": 576, "[FLUID] Dimensionally Shifted Superfluid": 8000}],
                                        ["Component Assembly Line (UMV)", 13, {"Electric Motor (UXV)": 48, "Wrap of UHV Circuits": 84, "Gold Nanites": 12, "Programmable Circuit (2)": 0, "[FLUID] Dimensionally Shifted Superfluid": 384000, "[FLUID] Molten Magnetohydrodynamically Constrained Star Matter": 242700, "[FLUID] Molten Eternity": 215000, "[FLUID] Molten SpaceTime": 138200, "[FLUID] Molten Magmatter": 82944, "[FLUID] Molten Universium": 27648}, {"Electric Piston (UXV)": 64}]],
              # Field Generators
              "Field Generator (LV)": [["Crafting", 0, {"Red Steel Plate": 4, "HV Circuit": 4, "Enderpearl Plate": 1}],
                                       ["Assembler (LV)", 2, {"HV Circuit": 4, "Enderpearl Plate": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Red Steel": 288}],
                                       ["Component Assembly Line (LV)", 2, {"Wrap of HV Circuits": 12, "Enderpearl Plate": 48, "[FLUID] Molten Red Steel": 13824}, {"Field Generator (LV)": 64}]],
              "Field Generator (MV)": [["Crafting", 0, {"Tungstensteel Plate": 4, "EV Circuit": 4, "Endereye Plate": 1}],
                                       ["Assembler (MV)", 3, {"EV Circuit": 4, "Endereye Plate": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tungstensteel": 288}],
                                       ["Component Assembly Line (LV)", 2, {"Wrap of EV Circuits": 12, "Endereye Plate": 48, "[FLUID] Molten Tungstensteel": 13824}, {"Field Generator (MV)": 64}]],
              "Field Generator (HV)": [["Crafting", 0, {"Double Niobium-Titanium Plate": 4, "IV Circuit": 4, "Quantum Eye": 1}],
                                       ["Assembler (HV)", 4, {"IV Circuit": 4, "Quantum Eye": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Niobium-Titanium": 576}],
                                       ["Component Assembly Line (MV)", 3, {"Wrap of IV Circuits": 12, "Quantum Eye": 48, "[FLUID] Molten Niobium-Titanium": 27648}, {"Field Generator (HV)": 64}]],
              "Field Generator (EV)": [["Crafting", 0, {"Double HSS-G Plate": 4, "LuV Circuit": 4, "Nether Star": 1}],
                                       ["Assembler (EV)", 5, {"LuV Circuit": 4, "Nether Star": 1, "Programmed Circuit (13)": 0, "[FLUID] Molten HSS-G": 576}],
                                       ["Component Assembly Line (HV)", 4, {"Wrap of LuV Circuits": 12, "Nether Star": 48, "[FLUID] Molten HSS-G": 27648}, {"Field Generator (EV)": 64}]],
              "Field Generator (IV)": [["Crafting", 0, {"Triple HSS-S Plate": 4, "ZPM Circuit": 4, "Quantum Star": 1}],
                                       ["Assembler (IV)", 6, {"ZPM Circuit": 4, "Quantum Star": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten HSS-S": 576}],
                                       ["Component Assembly Line (EV)", 5, {"Wrap of ZPM Circuits": 12, "Quantum Star": 48, "[FLUID] Molten HSS-S": 27648}, {"Field Generator (IV)": 64}]],
              "Field Generator (LuV)": [["Assemblyline Process (IV)", 6, {"HSS-S Frame Box": 1, "HSS-S Plate": 6, "Quantum Star": 2, "Emitter (LuV)": 4, "ZPM Circuit": 4, "Fine Ruridit Wire": 256, "1x Yttrium Barium Cuprate Cable": 8, "[FLUID] Molten Indalloy 140": 576}],
                                        ["Component Assembly Line (IV)", 6, {"HSS-S Frame Box": 48, "Dense HSS-S Plate": 32, "Quantum Star": 96, "Emitter (LuV)": 192, "Wrap of ZPM Circuits": 12, "16x Yttrium Barium Cuprate Cable": 24, "[FLUID] Molten Indalloy 140": 27648, "[FLUID] Molten Ruridit": 221200}, {"Field Generator (LuV)": 64}]],
              "Field Generator (ZPM)": [["Assemblyline Process (LuV)", 7, {"Naquadah Alloy Frame Box": 1, "Naquadah Alloy Plate": 6, "Quantum Star": 2, "Emitter (ZPM)": 4, "UV Circuit": 4, "Fine Europium Wire": 256, "4x Vanadium-Gallium Cable": 8, "[FLUID] Molten Indalloy 140": 1152}],
                                        ["Component Assembly Line (LuV)", 7, {"Naquadah Alloy Frame Box": 48, "Dense Naquadah Alloy Plate": 32, "Quantum Star": 96, "Emitter (ZPM)": 192, "Wrap of UV Circuits": 12, "[FLUID] Molten Indalloy 140": 55296, "[FLUID] Molten Europium": 221200, "[FLUID] Molten Vanadium-Gallium": 110600}, {"Field Generator (ZPM)": 64}]],
              "Field Generator (UV)": [["Assemblyline Process (ZPM)", 8, {"Neutronium Frame Box": 1, "Neutronium Plate": 6, "Gravi Star": 2, "Emitter (UV)": 4, "UHV Circuit": 4, "Fine Americium Wire": 384, "4x Naquadah Alloy Cable": 8, "[FLUID] Molten Indalloy 140": 2304, "[FLUID] Molten Naquadria": 1296}],
                                       ["Component Assembly Line (ZPM)", 8, {"Neutronium Frame Box": 48, "Dense Neutronium Plate": 32, "Gravi Star": 96, "Emitter (UV)": 192, "Wrap of UHV Circuits": 12, "[FLUID] Molten Indalloy 140": 110600, "[FLUID] Molten Americium": 331800, "[FLUID] Molten Naquadah Alloy": 110600, "[FLUID] Molten Naquadria": 62208}, {"Field Generator (UV)": 64}]],
              "Field Generator (UHV)": [["Assemblyline Process (UV)", 9, {"Cosmic Neutronium Frame Box": 1, "Cosmic Neutronium Plate": 6, "Gravi Star": 2, "Emitter (UHV)": 4, "UEV Circuit": 4, "Fine Neutronium Wire": 512, "4x Bedrockium Cable": 8, "[FLUID] Molten Indalloy 140": 2592, "[FLUID] Molten Naquadria": 2592}],
                                        ["Component Assembly Line (UV)", 9, {"Cosmic Neutronium Frame Box": 48, "Dense Cosmic Neutronium Plate": 32, "Gravi Star": 192, "Emitter (UHV)": 192, "Wrap of UEV Circuits": 12, "[FLUID] Molten Indalloy 140": 124400, "[FLUID] Molten Neutronium": 442400, "[FLUID] Molten Bedrockium": 124400, "[FLUID] Molten Naquadria": 110600}, {"Field Generator (UHV)": 64}]],
              "Field Generator (UEV)": [["Assemblyline Process (UHV)", 10, {"Infinity Frame Box": 1, "Infinity Plate": 6, "Gravi Star": 8, "Emitter (UEV)": 4, "UIV Circuit": 4, "Fine Tritanium Wire": 512, "4x Draconium Cable": 8, "[FLUID] Mutated Living Solder": 2592, "[FLUID] Molten Quantium": 2592}],
                                        ["Component Assembly Line (UHV)", 10, {"Infinity Frame Box": 48, "Dense Infinity Plate": 32, "Gravi Star": 384, "Emitter (UEV)": 192, "Wrap of UIV Circuits": 12, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Molten Tritanium": 442400, "[FLUID] Molten Quantium": 124400, "[FLUID] Molten Draconium": 110600}, {"Field Generator (UEV)": 64}]],
              "Field Generator (UIV)": [["Assemblyline Process (UEV)", 11, {"Infinity Frame Box": 1, "Transcendent Metal Plate": 6, "Nuclear Star": 1, "Emitter (UIV)": 4, "UMV Circuit": 4, "Fine Proto-Halkonite Wire": 512, "4x Nether Star Cable": 8, "[FLUID] Mutated Living Solder": 2592, "[FLUID] Molten Celestial Tungsten": 576}],
                                        ["Component Assembly Line (UEV)", 11, {"Infinity Frame Box": 48, "Dense Transcendent Metal Plate": 32, "Nuclear Star": 48, "Emitter (UIV)": 192, "Wrap of UMV Circuits": 12, "16x Nether Star Cable": 96, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Molten Quantium": 124400, "[FLUID] Dimensionally Shifted Superfluid": 110600, "[FLUID] Molten Proto-Halkonite Steel Base": 442400, "[FLUID] Molten Infinity": 442400, "[FLUID] Molten Celestial Tungsten": 27648}, {"Field Generator (UIV)": 64}],
                                        ["Component Assembly Line (UEV)", 11, {"Infinity Frame Box": 48, "Dense Transcendent Metal Plate": 32, "Nuclear Star": 48, "Emitter (UIV)": 192, "Wrap of UMV Circuits": 12, "16x Nether Star Cable": 96, "[FLUID] Mutated Living Solder": 124400, "[FLUID] Molten Quantium": 124400, "[FLUID] Dimensionally Shifted Superfluid": 110600, "[FLUID] Molten Proto-Halkonite Steel Base": 221200, "[FLUID] Molten Creon": 221200, "[FLUID] Molten Mellion": 221200, "[FLUID] Molten Celestial Tungsten": 27648}, {"Field Generator (UIV)": 64}]],
              #UMV
              #UXV
              # Stargate in name
              "[FLUID] Stargate Crystal Slurry": [["Transcendent Plasma Mixer (MAX)", 15, {"Programmed Circuit (24)": 0, "[FLUID] Molten Infinity": 1000, "[FLUID] Neutronium Plasma": 1000, "[FLUID] Flerovium Plasma": 1000, "[FLUID] Chromatic Glass Plasma": 1000, "[FLUID] Hydrogen Plasma": 1000, "[FLUID] Ichorium Plasma": 1000, "[FLUID] Six-Phased Copper Plasma": 1000, "[FLUID] Awakened Draconium Plasma": 1000, "[FLUID] Dragonblood Plasma": 1000, "[FLUID] Rhugnor Plasma": 1000, "[FLUID] Draconium Plasma": 1000, "[FLUID] Creon Plasma": 1000, "[FLUID] Tritanium Plasma": 1000, "[FLUID] Cosmic Neutronium Plasma": 1000, "[FLUID] Bedrockium Plasma": 1000, "[FLUID] Excited Dimensionally Transcendent Crude Catalyst": 1000, "[FLUID] Excited Dimensionally Transcendent Prosaic Catalyst": 1000, "[FLUID] Excited Dimensionally Transcendent Resplendent Catalyst": 1000, "[FLUID] Excited Dimensionally Transcendent Exotic Catalyst": 1000, "[FLUID] Excited Dimensionally Transcendent Stellar Catalyst": 1000},{"[FLUID] Stargate Crystal Slurry": 1000}]],
              #IC2 Stargate Power Unit has no recipe
              "OpenComputers Stargate Interface": [["Extreme Crafting", 6, {"Block of Magmatter": 18, "Dark Matter": 12, "Compact Fusion Coil MK-II Finaltype": 10, "Magmatter Nanites": 6, "Giga Chad Token": 2, "Cloud Computation Client Hatch": 4, "Singularity Crafting Storage": 4, "Stargate Ring Block": 1}]],
              "RF Stargate Power Unit": [["Extreme Crafting", 6, {"Block of Magmatter": 18, "Dark Matter": 12, "Compact Fusion Coil MK-II Finaltype": 10, "Mega Ultimate Battery": 4, "Ridiculously Large Capacitor": 4, "Stargate Ring Block": 1, "Magmatter Nanites": 6, "Giga Chad Token": 2}]],
              "Stargate Chevron Upgrade": [["Extreme Crafting", 6, {"Stargate Chevron": 4, "Field Generator (UXV)": 4, "Sensor (UXV)": 2, "Emitter (UXV)": 2, "Electric Piston (UXV)": 6, "Stargate Frame Part": 13}]],
              "Stargate Controller Crystal": [["Blast Furnace (Volc Eternal / EBF Hypogen) (MAX)", 15, {"Stargate-Crystal Dust": 64, "[FLUID] Molten Magnetohydrodynamically Constrained Star Matter": 128000000}],
                                              ["Helioflux Melthing Core (Eternal) (MAX)", 15, {"Stargate-Crystal Dust": 64, "[FLUID] Molten Magnetohydrodynamically Constrained Star Matter": 128000000}]],
              "Stargate Core Crystal": [["Blast Furnace (Volc Eternal / EBF Hypogen) (MAX)", 15, {"Stargate-Crystal Dust": 64, "[FLUID] Stargate Crystal Slurry": 128000000}],
                                        ["Helioflux Melthing Core (Eternal) (MAX)", 15, {"Stargate-Crystal Dust": 64, "[FLUID] Stargate Crystal Slurry": 128000000}]],
              "Stargate Iris Blade": [["Extreme Crafting", 6, {"Compact Fusion Coil MK-II Finaltype": 1, "Mega Ultimate Battery": 1, "Electric Piston (UXV)": 4, "Superdense Magmatter Plate": 19, "Superdense White Dwarf Matter Plate": 26}]],
              "Stargate Iris Upgrade": [["Extreme Crafting", 6, {"Superdense Magmatter Plate": 1, "Magmatter Nanites": 12, "Dark Matter": 12, "Stargate Iris Blade": 24}]],
              "Stargate Base": [["Extreme Crafting", 6, {"Transdimensional Alignment Matrix": 4, "Field Generator (UXV)": 16, "Emitter (UXV)": 8, "Magmatter Nanites": 4, "Central Graviton Flow Modulator": 8, "Superdense Magmatter Plate": 4, "Stargate-Radiation-Containment-Plate": 8, "Mining Drone MK-XIII": 2, "Mega Ultimate Battery": 4, "Artificial Universe ME Storage Cell": 1, "Astral Array Fabricator": 6, "Eye of Harmony": 4, "Space Assembler Module MK-III": 2, "Stargate Chevron Block": 8, "Stargate Core Crystal": 8, "ME Fluid Artificial Universe Storage Cell": 1}]],
              "Stargate Controller": [["Extreme Crafting", 6, {"Block of Magmatter": 15, "Dark Matter": 4, "Keyboard": 8, "Stargate Frame Part": 8, "Sensor (UXV)": 2, "Emitter (UXV)": 2, "Stargate Controller Crystal": 1, "Stargate-Radiation-Containment-Plate": 6, "Mega Ultimate Battery": 1, "OpenComputers Stargate Interface": 1, "ME Fluid Artificial Universe Storage Cell": 1}]],
              "Stargate Ring Block": [["Extreme Crafting", 6, {"Block of Magmatter": 18, "Dark Matter": 9, "Stargate Frame Part": 21, "Stargate Chevron": 3, "Stargate-Radiation-Containment-Plate": 11, "Field Generator (UXV)": 9}]],
              "Stargate Chevron Block": [["Extreme Crafting", 6, {"Block of Magmatter": 16, "Dark Matter": 12, "Stargate Chevron Upgrade": 4, "Stargate Ring Block": 1, "Central Graviton Flow Modulator": 4, "Field Generator (UXV)": 4}]],
              #Stargate Crystal Slurry Capsule is useless
              #Stargate ... Dimensional Duplicity/Harmonic Breakthrough/Split Origin/Polychrome Contest are all useless
              "Stargate Chevron": [["Assemblyline Process (UXV)", 14, {"Reinforced Spatial Structure Casing": 64, "Reinforced Temporal Structure Casing": 64, "Spatially Transcendent Gravitational Lens Block": 64, "Block of Magmatter": 64, "Magmatter Frame Box": 16, "Superdense Magmatter Plate": 8, "Superdense Magnetohydrodynamically Constrained Star Matter Plate": 8, "Magnetohydrodynamically Constrained Star Matter Frame Box": 16, "Exquisite Ruby": 64, "Exquisite Jasper": 64, "Exquisite Opal": 64, "Exquisite Sapphire": 64, "Electric Motor (UXV)": 64, "Electric Piston (UXV)": 64, "Field Generator (UXV)": 16, "UXV Circuit": 32, "[FLUID] Degenerate Quark Gluon Plasma": 1024000, "[FLUID] Lossless Photon Transfer Medium": 256000, "[FLUID] Molten Magmatter": 1180000, "[FLUID] Excited Dimensionally Transcendent Stellar Catalyst": 512000}]],
              #Stargate Core Crystal of the Ancients is useless
              "Stargate-Crystal Dust": [["Mixer (UXV)", 14, {"Hyper-Stable Self-Healing Adhesive": 64, "Superconductor Rare-Earth Composite": 64, "Black Body Naquadria Supersolid": 64, "Timepiece": 64, "Z Boson": 64, "ETA Meson": 64, "Lambda": 64, "Omega": 64, "Graviton Shard": 4, "[FLUID] Subatomically Perfect Water (Grade 8)": 1000000000}],
                                        ["Multiblock Mixer (UXV)", 14, {"Hyper-Stable Self-Healing Adhesive": 64, "Superconductor Rare-Earth Composite": 64, "Black Body Naquadria Supersolid": 64, "Timepiece": 64, "Z Boson": 64, "ETA Meson": 64, "Lambda": 64, "Omega": 64, "Graviton Shard": 4, "[FLUID] Subatomically Perfect Water (Grade 8)": 1000000000}]],
              #Stargate-Crystal Dust of the Ancients is used for the crystal but that is useless
              "Stargate Frame Part": [["Assemblyline Process (UXV)", 14, {"Long Infinity Rod": 64, "Long Mellion Rod": 64, "Long Universium Rod": 64, "Long Eternity Rod": 64, "Long Creon Rod": 64, "Long SpaceTime Rod": 64, "Long Superconductor Base UMV Rod": 64, "Long Shirabon Rod": 64, "Long Hypogen Rod": 64, "Long Six-Phased Copper Rod": 64, "Long Magnetohydrodynamically Constrained Star Matter Rod": 64, "Long Proto-Halkonite Steel Rod": 64, "Long White Dwarf Matter Rod": 64, "Long Magmatter Rod": 64, "Long Black Dwarf Matter Rod": 64, "Long Transcendent Metal Rod": 64, "[FLUID] Degenerate Quark Gluon Plasma": 1024000, "[FLUID] Lossless Photon Transfer Medium": 256000, "[FLUID] Molten Universium": 147500, "[FLUID] Excited Dimensionally Transcendent Stellar Catalyst": 512000}]],
              "Stargate-Radiation-Containment-Plate": [["Assemblyline Process (UXV)", 14, {"Transcendentally Amplified Magnetic Containment Casing": 64, "Gallifreyan Stabilisation Field Generator": 64, "Harmonic Phonon Transmission Conduit": 32, "Block of Magmatter": 64, "Superdense Magmatter Plate": 8, "Superdense Universium Plate": 8, "Superdense Eternity Plate": 8, "Superdense SpaceTime Plate": 8, "UXV Circuit": 16, "Sensor (UXV)": 16, "Emitter (UXV)": 16, "Chronic Singularity": 64, "Universium Nanites": 16, "Black Dwarf Matter Nanites": 16, "White Dwarf Matter Nanites": 16, "Six-Phased Copper Nanites": 16, "[FLUID] Degenerate Quark Gluon Plasma": 1024000, "[FLUID] Lossless Photon Transfer Medium": 256000, "[FLUID] Molten Superconductor Base UMV": 589800, "[FLUID] Excited Dimensionally Transcendent Stellar Catalyst": 512000}]],
              #Stargate Crystal Slurry Cell is useless
              # Chisel Buses
              "Chisel Bus I": [["Assembler (MV)", 3, {"Programmed Circuit (17)": 0, "Super Bus (I) (LV)": 1, "Sensor (LV)": 1, "Robot Arm (LV)": 2, "Aluminium Bolt": 16, "Chest": 1, "[FLUID] Molten Silicon Carbide": 288}]],
              "Chisel Bus II": [["Assembler (HV)", 4, {"Programmed Circuit (17)": 0, "Super Bus (I) (MV)": 1, "Sensor (MV)": 1, "Robot Arm (MV)": 2, "Black Metal Bolt": 16, "Chest": 1, "[FLUID] Molten Blood Steel": 288}]],
              "Chisel Bus III": [["Assembler (EV)", 5, {"Programmed Circuit (17)": 0, "Super Bus (I) (HV)": 1, "Sensor (HV)": 1, "Robot Arm (HV)": 2, "Titanium Bolt": 16, "Chest": 1, "[FLUID] Molten Tantalum Carbide": 288}]],
              # ME Input Buses
              "Advanced Stocking Input Bus (ME)": [["Assemblyline Process (LuV)", 7, {"Input Bus (LuV)": 1, "ME Interface": 1, "Conveyor Module (IV)": 1, "Acceleration Card": 4, "[FLUID] Molten Indalloy 140": 288, "[FLUID] Lubricant": 500}]],
              "Crafting Input Buffer (ME)": [["Space Elevator (UHV)", 10, {"Crafting Input Bus (ME)": 1, "Quadruple Input Hatch (UEV)": 1, "16384k ME Storage Component": 8, "16384k ME Fluid Storage Component": 8, "ME Controller": 1, "ME Dual Interface": 1, "Pattern Capacity Card": 3, "[FLUID] Mutated Living Solder": 2304, "[FLUID] Degassed Decontainment-Free Water (Grade 7)": 4000}]],
              "Crafting Input Bus (ME)": [["Assemblyline Process (LuV)", 7, {"Stocking Input Bus (ME)": 1, "4096k ME Storage Component": 1, "ME Controller": 1, "ME Interface": 1, "Pattern Capacity Card": 4, "[FLUID] Molten Indalloy 140": 1152}]],
              "Crafting Input Proxy (ME)": [["Space Assembler MK-II (UIV)", 12, {"Crafting Input Buffer (ME)": 1, "64 Core Co-Processing Unit": 1, "16384k ME Storage Component": 8, "16384k ME Fluid Storage Component": 8, "Wireless Connector": 2, "Sensor (UEV)": 1, "Energised Tesseract": 1, "[FLUID] Mutated Living Solder": 2304, "[FLUID] Dimensionally Shifted Superfluid": 4000}]],
              "Stocking Input Bus (ME)": [["Assembler (HV)", 4, {"Input Bus (HV)": 1, "ME Interface": 1, "Acceleration Card": 4, "Programmed Circuit (1)": 0}]],
              # ME Storage Components
              "1k ME Storage Component": [["Crafting", 0, {"ULV Circuit": 4, "Charged Certus Quartz Dust": 4, "Item Processor Tier I": 1}],
                                          ["Circuit Assembler (LV)", 2, {"ULV Circuit": 2, "Charged Certus Quartz Dust": 2, "Item Processor Tier I": 1, "Coated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                          ["Circuit Assembler (LV)", 2, {"ULV Circuit": 2, "Charged Certus Quartz Dust": 2, "Item Processor Tier I": 1, "Coated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                          ["Circuit Assembler (LV)", 2, {"ULV Circuit": 2, "Charged Certus Quartz Dust": 2, "Item Processor Tier I": 1, "Coated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "4k ME Storage Component": [["Crafting", 0, {"LV Circuit": 4, "1k ME Storage Component": 4, "Item Processor Tier I": 1}],
                                          ["Circuit Assembler (LV) [CLEANROOM]", 2, {"LV Circuit": 4, "ULV Circuit": 16, "Item Processor Tier I": 1, "Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                          ["Circuit Assembler (LV) [CLEANROOM]", 2, {"LV Circuit": 4, "ULV Circuit": 16, "Item Processor Tier I": 1, "Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                          ["Circuit Assembler (LV) [CLEANROOM]", 2, {"LV Circuit": 4, "ULV Circuit": 16, "Item Processor Tier I": 1, "Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "16k ME Storage Component": [["Crafting", 0, {"MV Circuit": 4, "4k ME Storage Component": 4, "Item Processor Tier II": 1}],
                                           ["Circuit Assembler (MV) [CLEANROOM]", 3, {"MV Circuit": 4, "LV Circuit": 16, "Item Processor Tier II": 1, "Good Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                           ["Circuit Assembler (MV) [CLEANROOM]", 3, {"MV Circuit": 4, "LV Circuit": 16, "Item Processor Tier II": 1, "Good Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                           ["Circuit Assembler (MV) [CLEANROOM]", 3, {"MV Circuit": 4, "LV Circuit": 16, "Item Processor Tier II": 1, "Good Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "64k ME Storage Component": [["Crafting", 0, {"HV Circuit": 4, "16k ME Storage Component": 4, "Item Processor Tier II": 1}],
                                           ["Circuit Assembler (HV) [CLEANROOM]", 4, {"HV Circuit": 4, "MV Circuit": 16, "Item Processor Tier II": 1, "Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                           ["Circuit Assembler (HV) [CLEANROOM]", 4, {"HV Circuit": 4, "MV Circuit": 16, "Item Processor Tier II": 1, "Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                           ["Circuit Assembler (HV) [CLEANROOM]", 4, {"HV Circuit": 4, "MV Circuit": 16, "Item Processor Tier II": 1, "Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "256k ME Storage Component": [["Crafting", 0, {"EV Circuit": 4, "64k ME Storage Component": 4, "Item Processor Tier III": 1}],
                                            ["Circuit Assembler (EV) [CLEANROOM]", 5, {"EV Circuit": 4, "HV Circuit": 16, "Item Processor Tier III": 1, "More Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                            ["Circuit Assembler (EV) [CLEANROOM]", 5, {"EV Circuit": 4, "HV Circuit": 16, "Item Processor Tier III": 1, "More Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                            ["Circuit Assembler (EV) [CLEANROOM]", 5, {"EV Circuit": 4, "HV Circuit": 16, "Item Processor Tier III": 1, "More Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "1024k ME Storage Component": [["Crafting", 0, {"IV Circuit": 4, "256k ME Storage Component": 4, "Item Processor Tier III": 1}],
                                             ["Circuit Assembler (IV) [CLEANROOM]", 6, {"IV Circuit": 4, "EV Circuit": 16, "Item Processor Tier III": 1, "Elite Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                             ["Circuit Assembler (IV) [CLEANROOM]", 6, {"IV Circuit": 4, "EV Circuit": 16, "Item Processor Tier III": 1, "Elite Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                             ["Circuit Assembler (IV) [CLEANROOM]", 6, {"IV Circuit": 4, "EV Circuit": 16, "Item Processor Tier III": 1, "Elite Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "4096k ME Storage Component": [["Crafting", 0, {"LuV Circuit": 4, "1024k ME Storage Component": 4, "Item Processor Tier IV": 1}],
                                             ["Circuit Assembler (LuV) [CLEANROOM]", 7, {"LuV Circuit": 4, "IV Circuit": 16, "Item Processor Tier IV": 1, "Extreme Wetware Lifesupport Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                             ["Circuit Assembler (LuV) [CLEANROOM]", 7, {"LuV Circuit": 4, "IV Circuit": 16, "Item Processor Tier IV": 1, "Extreme Wetware Lifesupport Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                             ["Circuit Assembler (LuV) [CLEANROOM]", 7, {"LuV Circuit": 4, "IV Circuit": 16, "Item Processor Tier IV": 1, "Extreme Wetware Lifesupport Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "16384k ME Storage Component": [["Crafting", 0, {"UV Circuit": 4, "4096k ME Storage Component": 4, "Item Processor Tier IV": 1}],
                                             ["Circuit Assembler (UV) [CLEANROOM]", 8, {"UV Circuit": 4, "LuV Circuit": 16, "Item Processor Tier IV": 1, "Ultra Bio Mutated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                             ["Circuit Assembler (UV) [CLEANROOM]", 8, {"UV Circuit": 4, "LuV Circuit": 16, "Item Processor Tier IV": 1, "Ultra Bio Mutated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                             ["Circuit Assembler (UV) [CLEANROOM]", 8, {"UV Circuit": 4, "LuV Circuit": 16, "Item Processor Tier IV": 1, "Ultra Bio Mutated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              # ME Fluid Storage Components
              "1k ME Fluid Storage Component": [["Crafting", 0, {"ULV Circuit": 4, "Charged Certus Quartz Dust": 4, "Fluid Processor Tier I": 1}],
                                                ["Circuit Assembler (LV)", 2, {"Electric Pump (LV)": 1, "ULV Circuit": 2, "Charged Certus Quartz Dust": 2, "Fluid Processor Tier I": 1, "Coated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                                ["Circuit Assembler (LV)", 2, {"Electric Pump (LV)": 1, "ULV Circuit": 2, "Charged Certus Quartz Dust": 2, "Fluid Processor Tier I": 1, "Coated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                                ["Circuit Assembler (LV)", 2, {"Electric Pump (LV)": 1, "ULV Circuit": 2, "Charged Certus Quartz Dust": 2, "Fluid Processor Tier I": 1, "Coated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "4k ME Fluid Storage Component": [["Crafting", 0, {"LV Circuit": 4, "1k ME Fluid Storage Component": 4, "Fluid Processor Tier I": 1}],
                                                ["Circuit Assembler (LV) [CLEANROOM]", 2, {"Electric Pump (LV)": 2, "LV Circuit": 4, "ULV Circuit": 16, "Fluid Processor Tier I": 1, "Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                                ["Circuit Assembler (LV) [CLEANROOM]", 2, {"Electric Pump (LV)": 2, "LV Circuit": 4, "ULV Circuit": 16, "Fluid Processor Tier I": 1, "Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                                ["Circuit Assembler (LV) [CLEANROOM]", 2, {"Electric Pump (LV)": 2, "LV Circuit": 4, "ULV Circuit": 16, "Fluid Processor Tier I": 1, "Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "16k ME Fluid Storage Component": [["Crafting", 0, {"MV Circuit": 4, "4k ME Fluid Storage Component": 4, "Fluid Processor Tier II": 1}],
                                                 ["Circuit Assembler (MV) [CLEANROOM]", 3, {"Electric Pump (MV)": 1, "MV Circuit": 4, "LV Circuit": 16, "Fluid Processor Tier II": 2, "Good Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                                 ["Circuit Assembler (MV) [CLEANROOM]", 3, {"Electric Pump (MV)": 1, "MV Circuit": 4, "LV Circuit": 16, "Fluid Processor Tier II": 2, "Good Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                                 ["Circuit Assembler (MV) [CLEANROOM]", 3, {"Electric Pump (MV)": 1, "MV Circuit": 4, "LV Circuit": 16, "Fluid Processor Tier II": 2, "Good Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "64k ME Fluid Storage Component": [["Crafting", 0, {"HV Circuit": 4, "16k ME Fluid Storage Component": 4, "Fluid Processor Tier II": 1}],
                                                 ["Circuit Assembler (HV) [CLEANROOM]", 4, {"Electric Pump (MV)": 2, "HV Circuit": 4, "MV Circuit": 16, "Fluid Processor Tier II": 4, "Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                                 ["Circuit Assembler (HV) [CLEANROOM]", 4, {"Electric Pump (MV)": 2, "HV Circuit": 4, "MV Circuit": 16, "Fluid Processor Tier II": 4, "Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                                 ["Circuit Assembler (HV) [CLEANROOM]", 4, {"Electric Pump (MV)": 2, "HV Circuit": 4, "MV Circuit": 16, "Fluid Processor Tier II": 4, "Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "256k ME Fluid Storage Component": [["Crafting", 0, {"EV Circuit": 4, "64k ME Fluid Storage Component": 4, "Fluid Processor Tier II": 1}],
                                                  ["Circuit Assembler (EV) [CLEANROOM]", 5, {"Electric Pump (HV)": 1, "EV Circuit": 4, "HV Circuit": 16, "Fluid Processor Tier II": 1, "More Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                                  ["Circuit Assembler (EV) [CLEANROOM]", 5, {"Electric Pump (HV)": 1, "EV Circuit": 4, "HV Circuit": 16, "Fluid Processor Tier II": 1, "More Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                                  ["Circuit Assembler (EV) [CLEANROOM]", 5, {"Electric Pump (HV)": 1, "EV Circuit": 4, "HV Circuit": 16, "Fluid Processor Tier II": 1, "More Advanced Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "1024k ME Fluid Storage Component": [["Crafting", 0, {"IV Circuit": 4, "256k ME Fluid Storage Component": 4, "Fluid Processor Tier II": 1}],
                                                   ["Circuit Assembler (IV) [CLEANROOM]", 6, {"Electric Pump (HV)": 2, "IV Circuit": 4, "EV Circuit": 16, "Fluid Processor Tier II": 2, "Elite Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                                   ["Circuit Assembler (IV) [CLEANROOM]", 6, {"Electric Pump (HV)": 2, "IV Circuit": 4, "EV Circuit": 16, "Fluid Processor Tier II": 2, "Elite Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                                   ["Circuit Assembler (IV) [CLEANROOM]", 6, {"Electric Pump (HV)": 2, "IV Circuit": 4, "EV Circuit": 16, "Fluid Processor Tier II": 2, "Elite Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "4096k ME Fluid Storage Component": [["Crafting", 0, {"LuV Circuit": 4, "1024k ME Fluid Storage Component": 4, "Fluid Processor Tier II": 1}],
                                                   ["Circuit Assembler (LuV) [CLEANROOM]", 7, {"Electric Pump (EV)": 1, "LuV Circuit": 4, "IV Circuit": 16, "Fluid Processor Tier II": 4, "Extreme Wetware Lifesupport Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                                   ["Circuit Assembler (LuV) [CLEANROOM]", 7, {"Electric Pump (EV)": 1, "LuV Circuit": 4, "IV Circuit": 16, "Fluid Processor Tier II": 4, "Extreme Wetware Lifesupport Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                                   ["Circuit Assembler (LuV) [CLEANROOM]", 7, {"Electric Pump (EV)": 1, "LuV Circuit": 4, "IV Circuit": 16, "Fluid Processor Tier II": 4, "Extreme Wetware Lifesupport Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              "16384k ME Fluid Storage Component": [["Crafting", 0, {"UV Circuit": 4, "4096k ME Fluid Storage Component": 4, "Fluid Processor Tier IV": 1}],
                                                   ["Circuit Assembler (UV) [CLEANROOM]", 8, {"Electric Pump (EV)": 1, "UV Circuit": 4, "LuV Circuit": 16, "Fluid Processor Tier II": 8, "Ultra Bio Mutated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Lead": 288}],
                                                   ["Circuit Assembler (UV) [CLEANROOM]", 8, {"Electric Pump (EV)": 1, "UV Circuit": 4, "LuV Circuit": 16, "Fluid Processor Tier II": 8, "Ultra Bio Mutated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Soldering Alloy": 72}],
                                                   ["Circuit Assembler (UV) [CLEANROOM]", 8, {"Electric Pump (EV)": 1, "UV Circuit": 4, "LuV Circuit": 16, "Fluid Processor Tier II": 8, "Ultra Bio Mutated Circuit Board": 1, "Programmed Circuit (1)": 0, "[FLUID] Molten Tin": 144}]],
              # AE2 Processors
              "Logic Processor": [["Assembler (LV)", 2, {"Printed Logic Circuit": 1, "Printed Silicon": 1, "[FLUID] Molten Redstone": 144}]],
              "Engineering Processor": [["Assembler (LV)", 2, {"Printed Logic Circuit": 1, "Printed Silicon": 1, "[FLUID] Molten Redstone": 144}]],
              "Calculation Processor": [["Assembler (LV)", 2, {"Printed Logic Circuit": 1, "Printed Silicon": 1, "[FLUID] Molten Redstone": 144}]],
              # Weird Input Buses
              "Focus Input Bus": [["Crafting", 0, {"Dense Mu-Metal Plate": 4, "Conveyor Belt": 2, "Robot Arm (HV)": 2, "Chest": 1}]],
              "Void Bus": [["Assembler (LV)", 2, {"Output Bus (LV)": 1, "Trash Can": 1}]],
              "Nanite Containment Bus": [["Assemblyline Process (UHV)", 10, {"Input Bus (UHV)": 1, "Quantum Chest IV": 1, "Field Generator (UHV)": 1, "Nanite Control Module": 4, "Dense Enriched Naquadah Alloy Plate": 4, "Superdense Cosmic Neutronium Plate": 4, "[FLUID] Mutated Living Solder": 2304}]],
              "Linked Input Bus": [["Assembler (IV)", 6, {"Input Bus (IV)": 1, "Emitter (IV)": 1, "Sensor (IV)": 1, "Dense Enderium Plate": 1, "Programmed Circuit (12)": 0, "[FLUID] Molten Polybenzimidazole": 144}]],
              # Charging/Discharging Buses
              "Charging Bus (MV)": [["Crafting", 0, {"Medium Voltage Battery Buffer": 1, "MV Machine Hull": 1}]],
              "Charging Bus (EV)": [["Crafting", 0, {"Extreme Voltage Battery Buffer": 1, "EV Machine Hull": 1}]],
              "Discharging Bus (MV)": [["Crafting", 0, {"MV Machine Hull": 1, "Medium Voltage Battery Buffer": 1}]],
              "Discharging Bus (EV)": [["Crafting", 0, {"EV Machine Hull": 1, "Extreme Voltage Battery Buffer": 1}]],
              # Super Bus (I)
              "Super Bus (I) (LV)": [["Assembler (LV)", 2, {"Programmed Circuit (17)": 1, "Input Bus (EV)": 1, "Electric Motor (LV)": 2, "Conveyor Module (LV)": 5, "Aluminium Bolt": 16, "LV Circuit": 2, "[FLUID] Molten Silicon Carbide": 1152}]],
              "Super Bus (I) (MV)": [["Assembler (MV)", 3, {"Programmed Circuit (17)": 1, "Input Bus (IV)": 1, "Electric Motor (MV)": 2, "Conveyor Module (MV)": 5, "Black Metal Bolt": 16, "MV Circuit": 2, "[FLUID] Molten Blood Steel": 1152}]],
              "Super Bus (I) (HV)": [["Assembler (HV)", 4, {"Programmed Circuit (17)": 1, "Input Bus (LuV)": 1, "Electric Motor (HV)": 2, "Conveyor Module (HV)": 5, "Titanium Bolt": 16, "HV Circuit": 2, "[FLUID] Molten Tantalum Carbide": 1152}]],
              # Coils
              "Cupronickel Coil Block": [["Assembler (LV)", 2, {"2x Cupronickel Wire": 8, "Alumino Silicate Wool": 12, "Programmed Circuit (3)": 0, "[FLUID] Molten Tin": 288}],
                                         ["Assembler (LV)", 2, {"2x Cupronickel Wire": 8, "Mica Insulator Foil": 8, "Programmed Circuit (3)": 0, "[FLUID] Molten Tin": 144}]],
              "Kanthal Coil Block": [["Assembler (MV)", 3, {"2x Kanthal Wire": 8, "Mica Insulator Foil": 12, "Programmed Circuit (3)": 0, "[FLUID] Molten Cupronickel": 144}]],
              "Nichrome Coil Block": [["Assembler (HV)", 4, {"2x Nichrome Wire": 8, "Mica Insulator Foil": 16, "Programmed Circuit (3)": 0, "[FLUID] Molten Kanthal": 144}]],
              "TPV-Alloy Coil Block": [["Assembler (EV)", 5, {"2x TPV-Alloy Wire": 8, "Mica Insulator Foil": 20, "Programmed Circuit (3)": 0, "[FLUID] Molten Nichrome": 144}]],
              "HSS-G Coil Block": [["Assembler (IV)", 6, {"2x HSS-G Wire": 8, "Mica Insulation Foil": 24, "Programmed Circuit (3)": 0, "[FLUID] Molten TPV-Alloy": 144}]],
              "HSS-S Coil Block": [["Assembler (IV)", 6, {"2x HSS-S Wire": 8, "Mica Insulation Foil": 28, "Programmed Circuit (3)": 0, "[FLUID] Molten HSS-G": 144}]],
              "Naquadah Coil Block": [["Assembler (LuV)", 7, {"2x Naquadah Wire": 8, "Mica Insulation Foil": 32, "Programmed Circuit (3)": 0, "[FLUID] Molten HSS-S": 144}]],
              "Naquadah Alloy Coil Block": [["Assembler (LuV)", 7, {"2x Naquadah Alloy Wire": 8, "Mica Insulation Foil": 36, "Programmed Circuit (3)": 0, "[FLUID] Molten Naquadah": 144}]],
              "Trinium Coil Block": [["Assembler (ZPM)", 8, {"2x Trinium Wire": 8, "Naquarite Universal Insulator Foil": 8, "Programmed Circuit (3)": 0, "[FLUID] Molten Naquadah Alloy": 144}]],
              "Electrum Flux Coil Block": [["Assembler (UV)", 9, {"2x Fluxed Electrum Wire": 8, "Naquarite Universal Insulator Foil": 12, "Programmed Circuit (3)": 0, "[FLUID] Molten Trinium": 144}]],
              "Awakened Draconium Coil Block": [["Assembler (UHV)", 10, {"2x Awakened Draconium Wire": 8, "Naquarite Universal Insulator Foil": 16, "Programmed Circuit (3)": 0, "[FLUID] Molten Fluxed Electrum": 144}]],
              "Infinity Coil Block": [["Assemblyline Process (UEV)", 11, {"UHV Circuit": 1, "2x Infinity Wire": 8, "Infinity Screw": 8, "Naquarite Universal Insulator Foil": 24, "[FLUID] Molten Awakened Draconium": 576}]],
              "Hypogen Coil Block": [["Assemblyline Process (UIV)", 12, {"UEV Circuit": 1, "2x Hypogen Wire": 8, "Hypogen Screw": 8, "Naquarite Universal Insulator Foil": 32, "[FLUID] Molten Infinity": 576}]],
              "Eternal Coil Block": [["Assemblyline Process (UMV)", 13, {"UIV Circuit": 1, "2x SpaceTime Wire": 8, "SpaceTime Screw": 8, "Eternal Singularity": 1, "Naquarite Universal Insulator Foil": 64, "[FLUID] Molten Hypogen": 576}]],
              # Fusion Computers
              "Fusion Control Computer Mark I": [["Assemblyline Process (LuV)", 7, {"Fusion Coil Block": 1, "ZPM Circuit": 4, "Dense Naquadah Alloy Plate": 4, "Dense Netherite Plate": 1, "Field Generator (LuV)": 2, "UHPIC Wafer": 32, "1x Superconductor LuV Wire": 32, "[FLUID] Molten Indalloy 140": 2880, "[FLUID] Molten Vanadium-Gallium": 1152}]],
              "Fusion Control Computer Mark II": [["Assemblyline Process (LuV)", 7, {"Fusion Coil Block": 1, "UV Circuit": 4, "Superdense Europium Plate": 1, "Field Generator (ZPM)": 2, "PPIC Wafer": 48, "2x Superconductor ZPM Wire": 32, "[FLUID] Molten Indalloy 140": 2880, "[FLUID] Molten Niobium-Titanium": 1152}]],
              "Fusion Control Computer Mark III": [["Assemblyline Process (ZPM)", 8, {"Fusion Coil Block": 1, "UHV Circuit": 4, "Superdense Americium Plate": 1, "Field Generator (UV)": 2, "QPIC Wafer": 48, "4x Superconductor UV Wire": 32, "[FLUID] Molten Indalloy 140": 2880, "[FLUID] Molten Fluxed Electrum": 1152}]],
              "FusionTech MK IV": [["Assemblyline Process (UHV)", 10, {"Advanced Fusion Coil Block": 1, "UEV Circuit": 4, "Superdense Neutronium Plate": 1, "Field Generator (UHV)": 2, "QPIC Wafer": 64, "4x Superconductor UHV Wire": 32, "[FLUID] UU-Matter": 50000, "[FLUID] Molten Cinobite A243": 9216, "[FLUID] Molten Octiron": 9216, "[FLUID] Molten Astral Titanium": 9216}]],
              "FusionTech MK V": [["Assemblyline Process (UEV)", 11, {"Advanced Fusion Coil II": 1, "UIV Circuit": 4, "Dense Metastable Oganesson Plate": 4, "Field Generator (UEV)": 2, "Pico Wafer": 64, "4x Superconductor UEV Wire": 32, "[FLUID] Molten Curium": 9216, "[FLUID] Molten Chromatic Glass": 9216, "[FLUID] Molten Abyssal Alloy": 9216, "[FLUID] Molten Dragonblood": 9216}]],
              # Compact Fusion Computers
              "Compact Fusion Computer MK-I Prototype": [["Assembler (LuV)", 7, {"Fusion Control Computer Mark I": 48, "Hi-Computation Station MK-I": 8, "MAR-Ce-M200 Steel Plate": 32, "LuV Circuit": 8, "HPIC Wafer": 16, "Field Generator (LuV)": 4, "Long MAR-M200 Steel Rod": 8, "[FLUID] Molten Adamantium Alloy": 9216}]],
              "Compact Fusion Computer MK-II": [["Assembler (ZPM)", 8, {"Fusion Control Computer Mark II": 48, "Hi-Computation Station MK-II": 8, "ZPM Circuit": 4, "UHPIC Wafer": 32, "ZPM Voltage Coil": 16, "Iridium Neutron Reflector": 4, "Field Generator (ZPM)": 8, "Small Artherium-Sn Gear": 32, "[FLUID] Molten MAR-Ce-M200 Steel": 2304, "[FLUID] Molten High Durability Compound Steel": 1152, "Molten Artherium-Sn": 288}]],
              "Compact Fusion Computer MK-III": [["Assembler (ZPM)", 8, {"Fusion Control Computer Mark III": 48, "Hi-Computation Station MK-III": 8, "UV Circuit": 4, "NPIC Wafer": 64, "Ultimate Voltage Coil": 16, "Advanced Radiation Proof Plate": 8, "Field Generator (UV)": 8, "Small High Durability Compound Steel Gear": 64, "[FLUID] Molten Tanmolyium Beta-C": 2304, "[FLUID] Molten Dalisenite": 1152, "Molten Americium": 288}]],
              "Compact Fusion Computer MK-IV Prototype": [["Assembler (UV)", 9, {"FusionTech MK IV": 48, "Hi-Computation Station MK-IV Prototype": 8, "UHV Circuit": 4, "PPIC Wafer": 64, "Highly Ultimate Voltage Coil": 16, "Dense Titansteel Plate": 8, "Field Generator (UHV)": 8, "Small Enriched Naquadah Alloy Gear": 64, "[FLUID] Molten Radox Polymer": 1296, "[FLUID] Molten Dalisenite": 1152, "Molten Botmium": 288}]],
              "Compact Fusion Computer MK-V": [["Assembler (UHV)", 10, {"FusionTech MK V": 48, "Hi-Computation Station MK-V Finaltype": 8, "UEV Circuit": 4, "QPIC Wafer": 64, "Highly Ultimate Voltage Coil": 64, "Dense Hypogen Plate": 8, "Field Generator (UEV)": 8, "Small Metastable Oganesson Gear": 64, "[FLUID] Molten Tairitsu": 2304, "[FLUID] Molten Octiron": 1152, "Molten Rhugnor": 288}]],
              # Fusion Coils
              "Compact Fusion Coil": [["Precise Assembler (LuV)", 7, {"Fusion Coil Block": 3, "Quartz Crystal Resonator": 2, "Hi-Computation Station MK-III": 1, "[FLUID] Molten Artherium-Sn": 576, "[FLUID] Molten Tanmolyium Beta-C": 144}]],
              "Advanced Compact Fusion Coil": [["Precise Assembler (ZPM)", 8, {"Fusion Coil Block": 3, "Radiation Proof Plate": 2, "Quantum Star": 4, "Hi-Computation Station MK-IV Prototype": 1, "[FLUID] Molten Dalisenite": 576, "[FLUID] Molten Hikarium": 144}]],
              "Compact Fusion Coil MK-II Prototype": [["Precise Assembler (UV)", 9, {"Advanced Fusion Coil": 3, "Energy Core [HV]": 1, "Hi-Computation Station MK-V Finaltype": 1, "[FLUID] Molten Energy Crystal": 1152, "[FLUID] Molten Laurenium": 144}]],
              "Compact Fusion Coil MK-II Finaltype": [["Precise Assembler (UHV)", 10, {"Advanced Fusion Coil II": 3, "UEV Circuit": 1, "Energy Core [IV]": 1, "Hi-Computation Station MK-V Finaltype": 4, "[FLUID] Molten Black Titanium": 1152, "[FLUID] Molten Metastable Oganesson": 576}]],
              "Fusion Coil Block": [["Crafting", 0, {"LuV Circuit": 4, "Iridium Neutron Reflector": 2, "Field Generator (MV)": 2, "Superconducting Coil Block": 1}],
                                    ["Assembler (LV)", 2, {"LuV Circuit": 4, "Iridium Neutron Reflector": 2, "Field Generator (MV)": 2, "Superconducting Coil Block": 1}]],
              "Advanced Fusion Coil": [["Assemblyline Process (UHV)", 10, {"Lapotronic Energy Orb Cluster": 16, "LuV Circuit": 16, "UV Circuit": 8, "Neutronium Plate": 8, "Emitter (UHV)": 1, "Sensor (UHV)": 1, "Fusion Coil Block": 1, "[FLUID] UU-Matter": 8000, "[FLUID] Molten Cinobite A243": 2304, "[FLUID] Molten Octiron": 2304, "[FLUID] Molten Astral Titanium": 2304}]],
              "Advanced Fusion Coil II": [["Assemblyline Process (UEV)", 11, {"Energy Module": 16, "ZPM Circuit": 16, "UHV Circuit": 8, "Rhugnor Plate": 8, "Emitter (UEV)": 1, "Sensor (UEV)": 1, "Advanced Compact Fusion Coil": 1, "[FLUID] Molten Neptunium": 2304, "[FLUID] Molten Chromatic Glass": 2304, "[FLUID] Molten Abyssal Alloy": 2304, "[FLUID] Molten Dragonblood": 2304}]],
              "Water Tank Siding": [["Crafting", 0, {"Iron Rod": 2, "Wood Planks": 5, "Sticky Resin": 1}],
                                    ["Crafting", 0, {"Wrought Iron Rod": 2, "Wood Planks": 5, "Sticky Resin": 1}],
                                    ["Crafting", 0, {"Pig Iron Rod": 2, "Wood Planks": 5, "Sticky Resin": 1, "{Hammer Use}": 1}],
                                    ["Crafting", 0, {"Steel Rod": 2, "Wood Planks": 5, "Congealed Green Slime": 1, "{Hammer Use}": 1}, {"Water Tank Siding": 2}],
                                    ["Crafting", 0, {"Steel Rod": 2, "Wood Planks": 5, "Congealed Blue Slime": 1, "{Hammer Use}": 1}, {"Water Tank Siding": 2}],
                                    ["Crafting", 0, {"Stainless Steel Rod": 2, "Wood Planks": 5, "Congealed Purple Slime": 1, "{Hammer Use}": 1}, {"Water Tank Siding": 4}],
                                    ["Assembler (LV)", 2, {"Iron Rod": 1, "Wood Frame Box": 2, "[FLUID] Refined Glue": 36}],
                                    ["Assembler (LV)", 2, {"Wrought Iron Rod": 2, "Wood Frame Box": 2, "[FLUID] Refined Glue": 36}],
                                    ["Assembler (LV)", 2, {"Steel Bolt": 4, "Wood Frame Box": 4, "[FLUID] Refined Glue": 72, "{Hammer Use}": 1}, {"Water Tank Siding": 3}],
                                    ["Assembler (LV)", 2, {"Steel Bolt": 2, "Wood Frame Box": 1, "[FLUID] Molten Polyethylene": 72, "{Hammer Use}": 1}, {"Water Tank Siding": 3}],
                                    ["Assembler (LV)", 2, {"Magnetic Iron Rod": 1, "Wood Frame Box": 2, "[FLUID] Refined Glue": 36}],
                                    ["Assembler (MV)", 3, {"Stainless Steel Bolt": 4, "Wood Frame Box": 4, "[FLUID] Molten Polyethylene": 72, "{Hammer Use}": 1}, {"Water Tank Siding": 9}]],
              "Iron Rod": [["Crafting", 0, {"Iron Ingot": 1, "{File Use}": 1}],
                           ["Lathe (LV)", 2, {"Iron Ingot": 1}, {"Iron Rod": 1, "Small Pile of Iron Dust": 2}],
                           ["Fluid Solidifier (MV)", 3, {"[FLUID] Molten Iron": 72, "Mold (Rod)": 0}],
                           ["Extruder (MV)", 3, {"Iron Ingot": 1, "Extruder Shape (Rod)": 0}, {"Iron Rod": 2}],
                           ["Extruder (MV)", 3, {"Magnetic Iron Ingot": 1, "Extruder Shape (Rod)": 0}, {"Iron Rod": 2}],
                           ["Extruder (MV)", 3, {"Pig Iron Ingot": 1, "Extruder Shape (Rod)": 0}, {"Iron Rod": 2}]],
              "Furnace": [["Crafting", 0, {"Cobblestone": 6, "Flint": 3}],
                          ["Assembler (LV)", 2, {"Cobblestone": 8, "Programmed Circuit (8)": 0}]],
              "Iron Plate": [["Crafting", 0, {"Iron Ingot": 2, "{Hammer Use}": 1}],
                             ["Alloy Smelter (LV)", 2, {"Iron Ingot": 2, "Mold (Plate)": 0}],
                             ["Alloy Smelter (LV)", 2, {"Magnetic Iron Ingot": 2, "Mold (Plate)": 0}],
                             ["Alloy Smelter (LV)", 2, {"Pig Iron Ingot": 2, "Mold (Plate)": 0}],
                             ["Forge Hammer (LV)", 2, {"Iron Ingot": 3}, {"Iron Plate": 2}],
                             ["Bending Machine (LV)", 2, {"Iron Ingot": 1}],
                             ["Fluid Solidifier (LV)", 2, {"[FLUID] Molten Iron": 1, "Mold (Plate)": 0}],
                             ["Extruder (MV)", 3, {"Iron Ingot": 1, "Extruder Shape (Plate)": 0}],
                             ["Extruder (MV)", 3, {"Magnetic Iron Ingot": 1, "Extruder Shape (Plate)": 0}],
                             ["Extruder (MV)", 3, {"Pig Iron Ingot": 1, "Extruder Shape (Plate)": 0}]],
              "Bucket of Concrete": [["Crafting", 0, {"Bucket": 1, "Water Bucket": 1, "Stone Dust": 1, "Quartz Sand": 1, "Clay Dust": 1, "Calcite Dust": 2}, {"Bucket of Concrete": 1, "Bucket": 1}],
                                     ["Fluid Canner (LV)", 2, {"[FLUID] Concrete": 1000, "Bucket": 1}]]
}
# !FAILSAFE: If no output, replace with [item]: 1.
for i in recipeList:
    for i2 in recipeList[i]:
        if(len(i2) == 3):
            i2.append({i: 1})

recipeStr = ""
for i in recipeList:
    recipeStr += ''' else if(i == "'''+i+'''") {
            for (let i2 = 0; i2 < initialCost[i]; i2++) {
                '''

    if(len(recipeList[i]) == 1):
        recipeStr += 'machine = "'+recipeList[i][0][0]+'";'
        #recipeStr += 'if('+str(recipeList[i][0][1])+' > tier) {machine = "Skip"; assig(secondaryCost, i, 1);} else {'
        for i2 in recipeList[i][0][2]:
            recipeStr += 'assig(secondaryCost, "'+i2+'", '+str(recipeList[i][0][2][i2])+'/'+str(recipeList[i][0][3][i])+');'
    else:
        # why the hell is this part here
        tmp = []  # Removes tiers from the recipe
        for i2 in recipeList[i]:
            tmp.append([i2[0], i2[2], i2[3]])
        recipeChoices[i] = tmp
        # actual multi-recipe logic
        for recipeIndex in range(len(recipeList[i])):
            recipeStr += 'if(selectionsR["'+str(i)+'"] == "'+str(recipeIndex+1)+'") {'
            recipeStr += 'machine = "'+recipeList[i][recipeIndex][0]+'";'
            #recipeStr += 'if('+str(recipeList[i][recipeIndex][1])+' > tier) {machine = "Skip"; assig(secondaryCost, i, 1);} else {'
            for i2 in recipeList[i][recipeIndex][2]:
                recipeStr += 'assig(secondaryCost, "'+i2+'", '+str(recipeList[i][recipeIndex][2][i2])+'/'+str(recipeList[i][recipeIndex][3][i])+');'
            recipeStr += "} else "
        recipeStr += '{ assig(secondaryCost, i, initialCost[i]); machine = "Skip"; }'

    # '''}
    recipeStr += '''
            }
        }'''

for i in recipeChoices:
    recipeSelected[i] = 1

##### RECIPE CHOICES #####

recipeSelections = ""
for item in recipeChoices:
    recipeSelections += '<tr><td class="center">'+item+': </td>'
    for recipeI in range(len(recipeChoices[item])):
        disable = ""
        if(recipeSelected[item] == recipeI+1):
            disable = "disabled"
        recipeSelections += f'''<td class="center"><button class="{item}" id="{item}.{recipeI+1}" onClick="selectR('{item}','{recipeI+1}')" {disable}>{recipeChoices[item][recipeI][0]}: '''
        for i3 in recipeChoices[item][recipeI][1]:                                      # i3 = Ingridient, i2[1][i3] = Ingridient Amount
            recipeSelections += str(recipeChoices[item][recipeI][1][i3])+"x "+i3+" + "
        recipeSelections = recipeSelections[:-3]                                # Remove additional " + "
        recipeSelections += " -> "                                              # Add arrow to separate ingridients and results
        for i3 in recipeChoices[item][recipeI][2]:                                      # i3 = Result, i2[2][i3] = Result Amount
            recipeSelections += str(recipeChoices[item][recipeI][2][i3])+"x "+i3+" + "
        recipeSelections = recipeSelections[:-3]                                # Remove additional " + "
        recipeSelections += "</button></td>"

# Create dictionary for index.html to use
recipeSelDict = "{"
for item in recipeSelected:
    recipeSelDict += '"'+str(item)+'": "'+str(recipeSelected[i])+'",'
recipeSelDict = recipeSelDict[:-1]

##### MULTIBLOCKS ######

# -- Multiblock names and statuses --
# !TODO: Check if every multiblock exists
# !TODO: Add Large Boiler version selector (images already there)
# !TODO: XL Turbo SC Steam Turbine????? (image added)
multiblocks = ['Coke Oven', 'Water Tank', 'Bricked Blast Furnace', 'Railcraft Boiler', 'Railcraft Tank', 'Water Pump', 'Charcoal Pile Igniter', 'Steam Oven', 'Steam Hearth', 'Steam Grinder', 'Steam Squasher', 'Steam Purifier', 'Steam Separator', 'Steam Blender', 'Steam Presser', 'Steam Fuser', 'Electric Blast Furnace', 'Electric Air Filter', 'Pyrolyse Oven', 'Advanced Coke Oven', 'Fluid Drilling Rig', 'ExxonMobil Chemical Plant', 'Large Boiler', 'Algae Farm', 'Concrete Backfiller', 'Cleanroom', 'Vacuum Freezer', 'Oil Cracking Unit', 'Large Chemical Reactor', 'Distillation Tower', 'Multi Smelter', 'Large Steam Turbine', 'XL Turbo Steam Turbine', 'Large Sifter', 'Implosion Compressor', 'Laminated Application and Thermal Enclosure eXpert (LATEX)', 'Dissection Apparatus', 'TurboCan Pro', 'Bacterial Vat', 'TFFT', 'Big Barrel Brewery', 'Solar Factory', 'Microwave Grinder', 'Mega Electric Blast Furnace', 'Mega Vacuum Freezer', 'Mega Distillation Tower', 'Mega Oil Cracker', 'Industrial Coke Oven', 'Extreme Entity Crusher', 'Ore Drilling Plant', 'Industrial Precision Lathe', 'Industrial Material Press', 'Large Electric Compressor', 'Large Thermal Refinery', 'Ore Washing Plant', 'Industrial 3D Copying Machine', 'Large Fluid Extractor', 'Industrial Centrifuge', 'Industrial Maceration Stack', 'Dissolution Tank', 'Large Gas Turbine', 'Solid-Oxide Fuel Cell', 'Large Semifluid Burner', 'Large Combustion Engine', 'Large Heat Exchanger', 'Lapotronic Supercapacitor', 'Tesla Tower', 'Assembly Line', 'Advanced Assembly Line', 'Industrial Electrolyzer', 'Industrial Mixing Machine', 'Precise Auto-Assembler MT-3662', 'Magnetic Flux Exhibitor', 'Density^2', 'Industrial Wire Factory', 'Industrial Extrusion Machine', 'Alloy Blast Smelter', 'Volcanus', 'Industrial Cutting Factory', 'Boldarnator', 'Hyper-Intensity Laser Engraver', 'Fluid Shaper', 'Mass Solidifier', 'Zyngen', 'Dangote Distillus', 'Industrial Sledgehammer', 'Tree Growth Simulator', 'Zhuhai Fishing Port', 'Cryogenic Freezer', 'Amazon Warehousing Depot', 'Thermic Heating Device', 'Thermal Boiler', 'YOTTank', 'Drone Centre', 'Digester', 'Rocketdyne F-1A Engine', 'Decay Warehouse', 'Solar Tower', 'Extreme Combustion Engine', 'Liquid Fluoride Thorium Reactor', 'Reactor Fuel Processing Plant', 'Nuclear Salt Processing Plant', 'Thorium High Temperature Reactor', 'High Temperature Gas-Cooled Reactor', 'Planetary Gas Siphon', 'Deep Earth Heating Pump', 'Extreme Industrial Greenhouse', 'Large Molecular Assembler', 'Fusion Reactor', 'Compact Fusion Reactor', 'Large Plasma Turbine', 'XL Turbo Gas Turbine', 'Neutron Activator', 'Circuit Assembly Line', 'Extreme Heat Exchanger', 'Industrial Autoclave', 'IsaMill Grinding Machine', 'Flotation Cell Regulator', 'Mega Chemical Reactor', 'Universal Chemical Fuel Engine', 'Cyclotron', 'High Current Industrial Arc Furnace', 'Utupu-Tanuri', 'Whakawhiti Wera XL', 'Molecular Transformer', 'Ender Quarry', 'Water Purification Plant', 'Clarifier Purification Unit', 'Ozonation Purification Unit', 'Sparge Tower', 'Active Transformer', 'Data Bank', 'Large Naquadah Reactor', 'XL Turbo Plasma Turbine', 'Large Scale Auto-Assembler v1.01', 'Void Miner', 'Hot Isostatic Pressurization Unit', 'Spinmatron-2737', 'Flocculation Purification Unit', 'pH Neutralization Purification Unit', 'Energy Infuser', 'Source Chamber', 'Target Chamber', 'Linear Accelerator', 'Synchrotron', 'Industrial Apicultural Acclimatiser and Drone Domestication Station', 'Quantum Computer', 'Research Station', 'Network Switch With QoS', 'Component Assembly Line', 'PCB Factory', 'Space Elevator', 'Nano Forge', 'Matter Fabrication CPU', 'Elemental Duplicator', 'Neutronium Compressor', 'Extreme Temperature Fluctuation Purification Unit', 'High Energy Laser Purification Unit', 'Mega Alloy Blast Smelter', 'Matter Manipulator Quantum Uplink', 'Integrated Ore Factory', 'Electric Implosion Compressor', 'Draconic Evolution Fusion Crafter', 'Naquadah Fuel Refinery', 'Miniature Wormhole Generator', 'Absolute Baryonic Perfection Purification Unit', 'Residual Decontaminant Degasser Purification Unit', 'Nanochip Assembly Complex', 'Exo-Foundry', 'Quantum Force Transformer', 'Dimensionally Transcendent Plasma Forge', 'Dyson Swarm Ground Unit', 'Transcendent Plasma Mixer', 'Forge of the Gods', 'Semi-Stable Antimatter Stabilization Sequencer', 'Shielded Lagrangian Annihilation Matrix', 'Pseudostable Black Hole Containment Field', 'Draconic Reactor', 'Eye of Harmony', 'Stargate']
multiblockTiers = {'Coke Oven': 'Stone', 'Water Tank': 'Stone', 'Bricked Blast Furnace': 'Stone', 'Railcraft Boiler': 'Stone', 'Railcraft Tank': 'Stone', 'Water Pump': 'Steam', 'Charcoal Pile Igniter': 'Steam', 'Steam Oven': 'Steam', 'Steam Hearth': 'Steam', 'Steam Grinder': 'Steam', 'Steam Squasher': 'Steam', 'Steam Purifier': 'Steam', 'Steam Separator': 'Steam', 'Steam Blender': 'Steam', 'Steam Presser': 'Steam', 'Steam Fuser': 'Steam', 'Electric Blast Furnace': 'LV', 'Electric Air Filter': 'LV', 'Pyrolyse Oven': 'MV', 'Advanced Coke Oven': 'MV', 'Fluid Drilling Rig': 'MV', 'ExxonMobil Chemical Plant': 'MV', 'Large Boiler': 'MV', 'Algae Farm': 'MV', 'Concrete Backfiller': 'MV', 'Cleanroom': 'HV', 'Vacuum Freezer': 'HV', 'Oil Cracking Unit': 'HV', 'Large Chemical Reactor': 'HV', 'Distillation Tower': 'HV', 'Multi Smelter': 'HV', 'Large Steam Turbine': 'HV', 'XL Turbo Steam Turbine': 'HV', 'Large Sifter': 'HV', 'Implosion Compressor': 'HV', 'Laminated Application and Thermal Enclosure eXpert (LATEX)': 'HV', 'Dissection Apparatus': 'HV', 'TurboCan Pro': 'HV', 'Bacterial Vat': 'HV', 'TFFT': 'HV', 'Big Barrel Brewery': 'HV', 'Solar Factory': 'HV', 'Microwave Grinder': 'HV', 'Mega Electric Blast Furnace': 'HV', 'Mega Vacuum Freezer': 'HV', 'Mega Distillation Tower': 'HV', 'Mega Oil Cracker': 'HV', 'Industrial Coke Oven': 'EV', 'Extreme Entity Crusher': 'EV', 'Ore Drilling Plant': 'EV', 'Industrial Precision Lathe': 'EV', 'Industrial Material Press': 'EV', 'Large Electric Compressor': 'EV', 'Large Thermal Refinery': 'EV', 'Ore Washing Plant': 'EV', 'Industrial 3D Copying Machine': 'EV', 'Large Fluid Extractor': 'EV', 'Industrial Centrifuge': 'EV', 'Industrial Maceration Stack': 'EV', 'Dissolution Tank': 'EV', 'Large Gas Turbine': 'EV', 'Solid-Oxide Fuel Cell': 'EV', 'Large Semifluid Burner': 'EV', 'Large Combustion Engine': 'EV', 'Large Heat Exchanger': 'EV', 'Lapotronic Supercapacitor': 'EV', 'Tesla Tower': 'EV', 'Assembly Line': 'IV', 'Advanced Assembly Line': 'IV', 'Industrial Electrolyzer': 'IV', 'Industrial Mixing Machine': 'IV', 'Precise Auto-Assembler MT-3662': 'IV', 'Magnetic Flux Exhibitor': 'IV', 'Density^2': 'IV', 'Industrial Wire Factory': 'IV', 'Industrial Extrusion Machine': 'IV', 'Alloy Blast Smelter': 'IV', 'Volcanus': 'IV', 'Industrial Cutting Factory': 'IV', 'Boldarnator': 'IV', 'Hyper-Intensity Laser Engraver': 'IV', 'Fluid Shaper': 'IV', 'Mass Solidifier': 'IV', 'Zyngen': 'IV', 'Dangote Distillus': 'IV', 'Industrial Sledgehammer': 'IV', 'Tree Growth Simulator': 'IV', 'Zhuhai Fishing Port': 'IV', 'Cryogenic Freezer': 'IV', 'Amazon Warehousing Depot': 'IV', 'Thermic Heating Device': 'IV', 'Thermal Boiler': 'IV', 'YOTTank': 'IV', 'Drone Centre': 'IV', 'Digester': 'IV', 'Rocketdyne F-1A Engine': 'IV', 'Decay Warehouse': 'IV', 'Solar Tower': 'IV', 'Extreme Combustion Engine': 'IV', 'Liquid Fluoride Thorium Reactor': 'IV', 'Reactor Fuel Processing Plant': 'IV', 'Nuclear Salt Processing Plant': 'IV', 'Thorium High Temperature Reactor': 'IV', 'High Temperature Gas-Cooled Reactor': 'IV', 'Planetary Gas Siphon': 'IV', 'Deep Earth Heating Pump': 'IV', 'Extreme Industrial Greenhouse': 'IV', 'Large Molecular Assembler': 'IV', 'Fusion Reactor': 'LuV', 'Compact Fusion Reactor': 'LuV', 'Large Plasma Turbine': 'LuV', 'XL Turbo Gas Turbine': 'LuV', 'Neutron Activator': 'LuV', 'Circuit Assembly Line': 'LuV', 'Extreme Heat Exchanger': 'LuV', 'Industrial Autoclave': 'LuV', 'IsaMill Grinding Machine': 'LuV', 'Flotation Cell Regulator': 'LuV', 'Mega Chemical Reactor': 'LuV', 'Universal Chemical Fuel Engine': 'LuV', 'Cyclotron': 'LuV', 'High Current Industrial Arc Furnace': 'LuV', 'Utupu-Tanuri': 'LuV', 'Whakawhiti Wera XL': 'LuV', 'Molecular Transformer': 'LuV', 'Ender Quarry': 'LuV', 'Water Purification Plant': 'LuV', 'Clarifier Purification Unit': 'LuV', 'Ozonation Purification Unit': 'LuV', 'Sparge Tower': 'LuV', 'Active Transformer': 'ZPM', 'Data Bank': 'ZPM', 'Large Naquadah Reactor': 'ZPM', 'XL Turbo Plasma Turbine': 'ZPM', 'Large Scale Auto-Assembler v1.01': 'ZPM', 'Void Miner': 'ZPM', 'Hot Isostatic Pressurization Unit': 'ZPM', 'Spinmatron-2737': 'ZPM', 'Flocculation Purification Unit': 'ZPM', 'pH Neutralization Purification Unit': 'ZPM', 'Energy Infuser': 'ZPM', 'Source Chamber': 'ZPM', 'Target Chamber': 'ZPM', 'Linear Accelerator': 'ZPM', 'Synchrotron': 'ZPM', 'Industrial Apicultural Acclimatiser and Drone Domestication Station': 'UV', 'Quantum Computer': 'UV', 'Research Station': 'UV', 'Network Switch With QoS': 'UV', 'Component Assembly Line': 'UV', 'PCB Factory': 'UV', 'Space Elevator': 'UV', 'Nano Forge': 'UV', 'Matter Fabrication CPU': 'UV', 'Elemental Duplicator': 'UV', 'Neutronium Compressor': 'UV', 'Extreme Temperature Fluctuation Purification Unit': 'UV', 'High Energy Laser Purification Unit': 'UV', 'Mega Alloy Blast Smelter': 'UV', 'Matter Manipulator Quantum Uplink': 'UV', 'Integrated Ore Factory': 'UHV', 'Electric Implosion Compressor': 'UHV', 'Draconic Evolution Fusion Crafter': 'UHV', 'Naquadah Fuel Refinery': 'UHV', 'Miniature Wormhole Generator': 'UHV', 'Absolute Baryonic Perfection Purification Unit': 'UEV', 'Residual Decontaminant Degasser Purification Unit': 'UEV', 'Nanochip Assembly Complex': 'UEV', 'Exo-Foundry': 'UEV', 'Quantum Force Transformer': 'UEV', 'Dimensionally Transcendent Plasma Forge': 'UEV', 'Dyson Swarm Ground Unit': 'UIV', 'Transcendent Plasma Mixer': 'UIV', 'Forge of the Gods': 'UIV', 'Semi-Stable Antimatter Stabilization Sequencer': 'UIV', 'Shielded Lagrangian Annihilation Matrix': 'UIV', 'Pseudostable Black Hole Containment Field': 'UIV', 'Draconic Reactor': 'UIV', 'Eye of Harmony': 'UMV', 'Stargate': 'UXV'}
multiblockStatus = {'Coke Oven': 4, 'Water Tank': 4, 'Bricked Blast Furnace': 4, 'Railcraft Boiler': 2, 'Railcraft Tank': 1, 'Water Pump': 2, 'Charcoal Pile Igniter': 1, 'Steam Oven': 2, 'Steam Hearth': 0, 'Steam Grinder': 2, 'Steam Squasher': 2, 'Steam Purifier': 2, 'Steam Separator': 2, 'Steam Blender': 2, 'Steam Presser': 2, 'Steam Fuser': 2, 'Electric Blast Furnace': 2, 'Electric Air Filter': 1, 'Pyrolyse Oven': 1, 'Advanced Coke Oven': 2, 'Fluid Drilling Rig': 2, 'ExxonMobil Chemical Plant': 1, 'Large Boiler': 1, 'Algae Farm': 1, 'Concrete Backfiller': 1, 'Large Chemical Reactor': 2, 'Distillation Tower':1, 'Cleanroom': 1, 'Vacuum Freezer': 1, 'Oil Cracking Unit': 1, 'Multi Smelter': 0, 'Large Steam Turbine': 1, 'XL Turbo Steam Turbine': 0, 'Large Sifter': 0, 'Implosion Compressor': 0, 'Laminated Application and Thermal Enclosure eXpert (LATEX)': 0, 'Big Barrel Brewery': 2, 'Mega Distillation Tower': 1, 'Assembly Line': 1, "Industrial Wire Factory": 2, "Zhuhai Fishing Port": 1, "Liquid Fluoride Thorium Reactor": 1, 'Fusion Reactor': 2, 'Compact Fusion Reactor': 2, "Active Transformer": 2, 'Research Station': 1, "Draconic Evolution Fusion Crafter": 1, "Dimensionally Transcendent Plasma Forge": 1, "Transcendent Plasma Mixer": 2, 'Stargate': 2}
multiblockStatusStr = {}

# -- Multiblock integer status -> string status --
for i in multiblockStatus:
    if(multiblockStatus[i] == 0):
        multiblockStatusStr[i] = "Not implemented"
    elif(multiblockStatus[i] == 1):
        multiblockStatusStr[i] = "Has image"
    elif(multiblockStatus[i] == 2):
        multiblockStatusStr[i] = "Implemented, not full breakdown"
    elif(multiblockStatus[i] == 3):
        multiblockStatusStr[i] = "Implemented, mostly full breakdown"
    elif(multiblockStatus[i] == 4):
        multiblockStatusStr[i] = "Fully implemented"
    else:
        multiblockStatusStr[i] = "Unknown status"

# -- Mark all multiblocks without status as not implemented --
for i in multiblocks:
    try:
        multiblockStatusStr[i]
    except Exception:
        multiblockStatusStr[i] = "Not implemented"

# -- Create multiblock list --
options = ""
for i in multiblocks:
    options += '<option value="'+i+'">'+i+' ('+multiblockStatusStr[i]+')</option>'

# -- Multiblock list TWO --
multiblockSelectionList = ""
tmp = []
tmp2 = False
for i in multiblocks:
    if(tmp2):
        tmp[-1].append(i)
        tmp2 = False
    else:
        tmp.append([i])
        tmp2 = True
for i in tmp:
    try: i[1]
    except: break
    display = ["", ""]
    if(multiblockTiers[i[0]] != "Steam"):
        display[0] = "none"
    if(multiblockTiers[i[1]] != "Steam"):
        display[1] = "none"
    multiblockSelectionList += f"""<tr>
        <td colspan="50%" width="100%" height="100%">
            <img class="MST{multiblockTiers[i[0]]}" style='display: {display[0]};' src="https://raw.githubusercontent.com/Chitak985/gtnh-multiblocks/refs/heads/main/screenshots/{i[0]}.png" width="50%" height="250px">
            <img class="MST{multiblockTiers[i[1]]}" style='display: {display[1]};' src="https://raw.githubusercontent.com/Chitak985/gtnh-multiblocks/refs/heads/main/screenshots/{i[1]}.png" width="50%" height="250px">
        </td>
    </tr>
    <tr>
    	<td colspan="100%">
        	<table width="100%">
        	    <tr>
        	        <td class="MST{multiblockTiers[i[0]]}" style='display: {display[0]};'><div style="text-align: center;"><strong>{i[0]}</strong></div><button style="margin: 2% 42%;">Select</button></td>
        	        <td class="MST{multiblockTiers[i[1]]}" style='display: {display[1]};'><div style="text-align: center;"><strong>{i[1]}</strong></div><button style="margin: 2% 42%;">Select</button></td>
        	    </tr>
        	</table>
        </td>
    </tr>"""

# -- Data --
# Use -1 if unknown (applies to all data)
# Use 0 in MaxIO or IOPorts if the multiblock has no IO

def appendIOStr(ioPortSet):
    warnings = []
    ioStr = ""
    for i2 in ioPortSet:
        if(i2 == "M"):
            ioStr += '''<tr><td class="center"></td><td class="center">1x Maintenance Hatch</td></tr>'''
        elif(type(i2) == type([])):
            if(i2[0] == "IB(S)"):
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'inputB\\\')">-</button></td><td class="center"><span id="inputB">'''+str(i2[1])+'''</span>x \'+inputBuses+\'</td><td class="center"><button onclick="MinputB()">+</button></td></tr>'''
            elif(i2[0] == "IB"):
                warnings.append("steamBusDisallowed")
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'inputB\\\')">-</button></td><td class="center"><span id="inputB">'''+str(i2[1])+'''</span>x \'+inputBuses+\'</td><td class="center"><button onclick="MinputB()">+</button></td></tr>'''
            elif(i2[0] == "OB(S)"):
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'outputB\\\')">-</button></td><td class="center"><span id="outputB">'''+str(i2[1])+'''</span>x \'+outputBuses+\'</td><td class="center"><button onclick="MoutputB()">+</button></td></tr>'''
            elif(i2[0] == "OB"):
                warnings.append("steamBusDisallowed")
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'outputB\\\')">-</button></td><td class="center"><span id="outputB">'''+str(i2[1])+'''</span>x \'+outputBuses+\'</td><td class="center"><button onclick="MoutputB()">+</button></td></tr>'''
            elif(i2[0] == "S"):
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'steam\\\')">-</button></td><td class="center"><span id="steam">'''+str(i2[1])+'''</span>x Steam Hatch</td><td class="center"><button onclick="Msteam()">+</button></td></tr>'''
            elif(i2[0] == "EH"):
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'energy\\\')">-</button></td><td class="center"><span id="energy">'''+str(i2[1])+'''</span>x Energy Hatch</td><td class="center"><button onclick="Menergy()">+</button></td></tr>'''
            elif(i2[0] == "DH"):
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'dynamo\\\')">-</button></td><td class="center"><span id="dynamo">'''+str(i2[1])+'''</span>x Dynamo Hatch</td><td class="center"><button onclick="Mdynamo()">+</button></td></tr>'''
            elif(i2[0] == "IH"):
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'Ihatch\\\')">-</button></td><td class="center"><span id="Ihatch">'''+str(i2[1])+'''</span>x Input Hatch (ULV)</td><td class="center"><button onclick="MIhatch()">+</button></td></tr>'''
            elif(i2[0] == "OH"):
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'Ohatch\\\')">-</button></td><td class="center"><span id="Ohatch">'''+str(i2[1])+'''</span>x Output Hatch (ULV)</td><td class="center"><button onclick="MOhatch()">+</button></td></tr>'''
            elif(i2[0] == "C"):
                ioStr += '''<tr><td class="center"><button onclick="Lclass(\\\'Chousing\\\')">-</button></td><td class="center"><span id="Chousing">'''+str(i2[1])+'''</span>x Catalyst Housing</td><td class="center"><button onclick="MChousing()">+</button></td></tr>'''
            elif(i2[0] == "M"):
                ioStr += '''<tr><td class="center"></td><td class="center"><span id="MufllerHatch">'''+str(i2[1])+'''</span>x Muffler Hatch (LV)</td><td class="center"></td></tr>'''

    ioStr += "\';"
    return (ioStr, warnings)

def appendHatchStr(ioPortSet, oneHatchOnly=False, io=None):
    ioStr = ""
    tmp = ""
    for i2 in ioPortSet:
        if(type(i2) == type([])):
            if(i2[0] == "IB(S)" or i2[0] == "IB"):
                ioStr += '''var inputB = document.getElementById("inputB");
'''
                tmp += "+Number(inputB.innerHTML)"
                if(oneHatchOnly and io == "IB"):
                    break

            elif(i2[0] == "OB(S)" or i2[0] == "OB"):
                ioStr += '''var outputB = document.getElementById("outputB");
'''
                tmp += "+Number(outputB.innerHTML)"
                if(oneHatchOnly and io == "OB"):
                    break
            elif(i2[0] == "S"):
                ioStr += '''var steam = document.getElementById("steam");
'''
                tmp += "+Number(steam.innerHTML)"
            elif(i2[0] == "EH"):
                ioStr += '''var energy = document.getElementById("energy");
'''
                tmp += "+Number(energy.innerHTML)"
            elif(i2[0] == "DH"):
                ioStr += '''var dynamo = document.getElementById("dynamo");
'''
                tmp += "+Number(dynamo.innerHTML)"
            elif(i2[0] == "IH"):
                ioStr += '''var Ihatch = document.getElementById("Ihatch");
'''
                tmp += "+Number(Ihatch.innerHTML)"
            elif(i2[0] == "OH"):
                ioStr += '''var Ohatch = document.getElementById("Ohatch");
'''
                tmp += "+Number(Ohatch.innerHTML)"
            elif(i2[0] == "C"):
                ioStr += '''var Chousing = document.getElementById("Chousing");
'''
                tmp += "+Number(Chousing.innerHTML)"
            elif(i2[0] == "M"):
                pass

            if(oneHatchOnly and io == i2[0]):
                break

    return (ioStr, tmp)

def appendIOCostStr(ioPortSet):
    ioStr = ""
    for i2 in ioPortSet:
        if(type(i2) == type([])):
            if(i2[0] == "IB(S)" or i2[0] == "IB"):
                ioStr += '''var inputB = document.getElementById("inputB");
                            initialCost[inputBuses] = Number(inputB.innerHTML);
'''
            elif(i2[0] == "OB(S)" or i2[0] == "OB"):
                ioStr += '''var outputB = document.getElementById("outputB");
                            initialCost[outputBuses] = Number(outputB.innerHTML);
'''
            elif(i2[0] == "S"):
                ioStr += '''var steam = document.getElementById("steam");
                            initialCost["Steam Hatch"] = Number(steam.innerHTML);
'''
            elif(i2[0] == "EH"):
                ioStr += '''var energy = document.getElementById("energy");
		                    initialCost[numberToTier(tierEnergyHatch)+" Energy Hatch"] = Number(energy.innerHTML);
'''
            elif(i2[0] == "DH"):
                ioStr += '''var dynamo = document.getElementById("dynamo");
		                    initialCost[numbetToTier(tierDynamoHatch)+" Dynamo Hatch"] = Number(dynamo.innerHTML);
'''
            elif(i2[0] == "IH"):
                ioStr += '''var Ihatch = document.getElementById("Ihatch");
	                    	initialCost["Input Hatch (ULV)"] = Number(Ihatch.innerHTML);
'''
            elif(i2[0] == "OH"):
                ioStr += '''var Ohatch = document.getElementById("Ohatch");
		                    initialCost["Output Hatch (ULV)"] = Number(Ohatch.innerHTML);
'''
            elif(i2[0] == "C"):
                ioStr += '''var Chousing = document.getElementById("Chousing");
	                    	initialCost["Catalyst Housing"] = Number(Chousing.innerHTML);
'''
            elif(i2[0] == "M"):
                pass

    return ioStr

# Validators
# function here is only for debug messages
def validateEntryMAIN(tmp, dataName="[UNKNOWN]", function=None):
    if(type(tmp) == type(0)):  # Does not exist
        if(tmp == 0):  # Is not supposed to have an entry
            pass
        elif(tmp == -1):  # Not implemented yet
            pass
        else:
            # Problem, unknown entry status
            if(function is None):
                print("[ERROR] Invalid data in "+dataName+" for "+str(i)+": "+str(multiblockMaxIO[i]))
            else:
                print("[ERROR]["+function+"] Invalid data in "+dataName+" for "+str(i)+": "+str(multiblockMaxIO[i]))
    elif("MAIN" in tmp):  # Exists
        return True
    else:  # Unknown data
        print("[ERROR]["+function+"] Invalid data in multiblockMaxIO for "+str(i)+": "+str(multiblockMaxIO[i]))
    return False
def validateEntry(tmp, dataName="[UNKNOWN]", function=None):
    if(type(tmp) == type(0)):  # Does not exist
        if(tmp == 0):  # Is not supposed to have an entry
            pass
        elif(tmp == -1):  # Not implemented yet
            pass
        else:
            # Problem, unknown entry status
            if(function is None):
                print("[ERROR] Invalid data in "+dataName+" for "+str(i)+": "+str(multiblockMaxIO[i]))
            else:
                print("[ERROR]["+function+"] Invalid data in "+dataName+" for "+str(i)+": "+str(multiblockMaxIO[i]))
    else:  # Exists
        return True
    return False

# .has but with IO
def hasIO(multi, io, io2="[Impossible IO Abbreviation Here]"):
    for i2 in multi["MAIN"]:
        if(type(i2) == type([])):
            if(i2[0] == io or i2[0] == io2):
                return True
    return False

# !TODO: Replace abbr with automatic IO abbriviation getting (low priority)
# io here is only used for debug messages and JS-side variables, such as "CHousing" and "energy"
# abbr2 is only for "IB(S)" and "OB(S)"
# appendHatchStr inside the function does not take abbr2 because it already has handling for that
def getIOSelectedStr(io, abbr, abbr2="[Insert Impossible IO Abbreviation Here]"):
    mainStr = ""
    for i in multiblockIOPorts:
        if(not validateEntryMAIN(multiblockIOPorts[i], "IOPorts", io)): continue
        if(not validateEntryMAIN(multiblockMaxIO[i], "MaxIO", io)): continue
        if(allowedProceduralIO(i)): continue
        if(not hasIO(multiblockIOPorts[i], abbr, abbr2)): continue
        mainStr += ''' else if(document.getElementById("titleText").innerHTML == "'''+i+'''") {
            var casing = document.getElementById("casing");
            '''
        tmp2, tmp = appendHatchStr(multiblockIOPorts[i]["MAIN"], type(multiblockMaxIO[i]["MAIN"]) != type(0), abbr)
        mainStr += tmp2+'''if((0'''+tmp+''') < maxIO) {
                '''+io+'''.innerHTML = String(Number('''+io+'''.innerHTML) + 1);
                casing.innerHTML = String(Number(casing.innerHTML) - 1);
            }
        }'''
    return mainStr

# Bad multiblocks go here (i hate multiple casing types)
allowedProceduralIO = lambda i: i == "Water Pump" or i == "Compact Fusion Reactor"
# Each multiblock must have a casing number and name or -1
# If the first element is a dict, the casing data is considered multi-tier
# If the first element of the first tier/base tier is a list, the casing data is considered multi-casing
# The per-tier, per-type data is in format [baseAmount, "name"]
# Breakdown of the compact fusion reactor: (comments are on the far left)
"""
[
    {},                                                                       # Enables multiple tiers

    [                                                                         # Tier 1 START
        [1662, "LuV Machine Casing"],                                         # Casing0    |
        [93, "Rhodium-Plated Palladium Reinforced Borosilicate Glass Block"]  # Casing1    |
    ],                                                                        # Tier 1 -END-

    [                                                                         # Tier 2 START
        [1662, "Fusion Machine Casing"],                                      # Casing0    |
        [93, "Iridium Reinforced Borosilicate Glass Block"]                   # Casing1    |
    ],                                                                        # Tier 2 -END-

    [                                                                         # Tier 3 START
        [1662, "Fusion Machine Casing MK II"],                                # Casing0    |
        [93, "Osmium Reinforced Borosilicate Glass Block"]                    # Casing1    |
    ],                                                                        # Tier 3 -END-

    [                                                                         # Tier 4 START
        [1662, "Fusion Machine Casing MK III"],                               # Casing0    |
        [93, "Neutronium Reinforced Borosilicate Glass Block"]                # Casing1    |
    ],                                                                        # Tier 4 -END-

    [                                                                         # Tier 5 START
        [1662, "Fusion Machine Casing MK IV"],                                # Casing0    |
        [93, "Cosmic Neutronium Reinforced Borosilicate Glass Block"]         # Casing1    |
    ]                                                                         # Tier 5 -END-
]
"""
# Total IO-replacable casing - minimum hatches (include maint and energy hatches)
multiblockCasing= {'Coke Oven': 0, 'Water Tank': 0,
                   'Bricked Blast Furnace': 0, 'Railcraft Boiler': 0,
                   'Railcraft Tank': -1, 'Water Pump': [9, "Primitive Wooden Casing"],
                   'Charcoal Pile Igniter': 0, 'Steam Oven': 0,
                   'Steam Hearth': -1, 'Steam Grinder': [22, "Bronze Plated Bricks"],
                   'Steam Squasher': [30, "Bronze Plated Bricks"], 'Steam Purifier': [59, "Bronze Plated Bricks"],
                   'Steam Separator': [65, "Bronze Plated Bricks"], 'Steam Blender': [100, "Bronze Plated Bricks"],
                   'Steam Presser': [39, "Bronze Plated Bricks"], 'Steam Fuser': [26, "Bronze Plated Bricks"],
                   'Electric Blast Furnace': [14, "Heat Proof Machine Casing"], 'Electric Air Filter': -1,
                   'Pyrolyse Oven': -1, 'Advanced Coke Oven': 0,
                   'Fluid Drilling Rig': [{}, [5,"Solid Steel Machine Casing"], [5,"Clean Stainless Steel Machine Casing"], [5,"Stable Titanium Machine Casing"],[5,"Robust Tungstensteel Machine Casing"], [5,"Mining Neutronium Casing"]], 'ExxonMobil Chemical Plant': -1,
                   'Large Boiler': -1, 'Algae Farm': -1,
                   'Concrete Backfiller': -1, 'Cleanroom': -1,
                   'Vacuum Freezer': -1, 'Oil Cracking Unit': -1,
                   'Large Chemical Reactor': [22, "Chemically Inert Machine Casing"], 'Distillation Tower': -1,
                   'Multi Smelter': -1, 'Large Steam Turbine': -1,
                   'XL Turbo Steam Turbine': -1, 'Large Sifter': [54, "Industrial Sieve Casing"],
                   'Implosion Compressor': -1, 'Laminated Application and Thermal Enclosure eXpert (LATEX)': -1,
                   'Dissection Apparatus': -1, 'TurboCan Pro': -1,
                   'Bacterial Vat': -1, 'TFFT': -1, 'Big Barrel Brewery': [23, "Reinforced Wooden Casing"],
                   'Solar Factory': -1, 'Microwave Grinder': -1,
                   'Mega Electric Blast Furnace': -1, 'Mega Vacuum Freezer': -1,
                   'Mega Distillation Tower': -1, 'Mega Oil Cracker': -1,
                   'Industrial Coke Oven': -1, 'Extreme Entity Crusher': -1,
                   'Ore Drilling Plant': -1, 'Industrial Precision Lathe': -1,
                   'Industrial Material Press': -1, 'Large Electric Compressor': -1,
                   'Large Thermal Refinery': -1, 'Ore Washing Plant': -1,
                   'Industrial 3D Copying Machine': -1, 'Large Fluid Extractor': -1,
                   'Industrial Centrifuge': -1, 'Industrial Maceration Stack': -1,
                   'Dissolution Tank': -1, 'Large Gas Turbine': -1,
                   'Solid-Oxide Fuel Cell': -1, 'Large Semifluid Burner': -1,
                   'Large Combustion Engine': -1, 'Large Heat Exchanger': -1,
                   'Lapotronic Supercapacitor': -1, 'Tesla Tower': -1,
                   'Assembly Line': -1, 'Advanced Assembly Line': -1,
                   'Industrial Electrolyzer': -1, 'Industrial Mixing Machine': -1,
                   'Precise Auto-Assembler MT-3662': -1, 'Magnetic Flux Exhibitor': -1,
                   'Density^2': -1, 'Industrial Wire Factory': [38, "Wire Factory Casing"],
                   'Industrial Extrusion Machine': -1, 'Alloy Blast Smelter': -1,
                   'Volcanus': -1, 'Industrial Cutting Factory': -1,
                   'Boldarnator': -1, 'Hyper-Intensity Laser Engraver': -1,
                   'Fluid Shaper': -1, 'Mass Solidifier': -1,
                   'Zyngen': -1, 'Dangote Distillus': -1,
                   'Industrial Sledgehammer': -1, 'Tree Growth Simulator': -1,
                   'Zhuhai Fishing Port': -1, 'Cryogenic Freezer': -1,
                   'Amazon Warehousing Depot': -1, 'Thermic Heating Device': -1,
                   'Thermal Boiler': -1, 'YOTTank': -1,
                   'Drone Centre': -1, 'Digester': -1,
                   'Rocketdyne F-1A Engine': -1, 'Decay Warehouse': -1,
                   'Solar Tower': -1, 'Extreme Combustion Engine': -1,
                   'Liquid Fluoride Thorium Reactor': -1, 'Reactor Fuel Processing Plant': -1,
                   'Nuclear Salt Processing Plant': -1, 'Thorium High Temperature Reactor': -1,
                   'High Temperature Gas-Cooled Reactor': -1, 'Planetary Gas Siphon': -1,
                   'Deep Earth Heating Pump': -1, 'Extreme Industrial Greenhouse': -1,
                   'Large Molecular Assembler': -1, 'Fusion Reactor': [{},[1662, "LuV Machine Casing"],[1662, "Fusion Machine Casing"],[1662, "Fusion Machine Casing MK II"],[1662, "Fusion Machine Casing MK III"],[1662, "Fusion Machine Casing MK IV"]],
                   'Compact Fusion Reactor': [{}, [[1662, "LuV Machine Casing"], [93, "Rhodium-Plated Palladium Reinforced Borosilicate Glass Block"]], [[1662, "Fusion Machine Casing"], [93, "Iridium Reinforced Borosilicate Glass Block"]], [[1662, "Fusion Machine Casing MK II"], [93, "Osmium Reinforced Borosilicate Glass Block"]], [[1662, "Fusion Machine Casing MK III"], [93, "Neutronium Reinforced Borosilicate Glass Block"]], [[1662, "Fusion Machine Casing MK IV"], [93, "Cosmic Neutronium Reinforced Borosilicate Glass Block"]]], 'Large Plasma Turbine': -1,
                   'XL Turbo Gas Turbine': -1, 'Neutron Activator': -1,
                   'Circuit Assembly Line': -1, 'Extreme Heat Exchanger': -1,
                   'Industrial Autoclave': -1, 'IsaMill Grinding Machine': -1,
                   'Flotation Cell Regulator': -1, 'Mega Chemical Reactor': -1,
                   'Universal Chemical Fuel Engine': -1, 'Cyclotron': -1,
                   'High Current Industrial Arc Furnace': -1, 'Utupu-Tanuri': -1,
                   'Whakawhiti Wera XL': -1, 'Molecular Transformer': -1,
                   'Ender Quarry': -1, 'Water Purification Plant': -1,
                   'Clarifier Purification Unit': -1, 'Ozonation Purification Unit': -1,
                   'Sparge Tower': -1, 'Active Transformer': -1,
                   'Data Bank': -1, 'Large Naquadah Reactor': -1,
                   'XL Turbo Plasma Turbine': -1, 'Large Scale Auto-Assembler v1.01': -1,
                   'Void Miner': -1, 'Hot Isostatic Pressurization Unit': -1,
                   'Spinmatron-2737': -1, 'Flocculation Purification Unit': -1,
                   'pH Neutralization Purification Unit': -1, 'Energy Infuser': -1,
                   'Source Chamber': -1, 'Target Chamber': -1,
                   'Linear Accelerator': -1, 'Synchrotron': -1,
                   'Industrial Apicultural Acclimatiser and Drone Domestication Station': -1,
                   'Quantum Computer': -1, 'Research Station': -1,
                   'Network Switch With QoS': -1, 'Component Assembly Line': -1,
                   'PCB Factory': -1, 'Space Elevator': -1,
                   'Nano Forge': -1, 'Matter Fabrication CPU': -1,
                   'Elemental Duplicator': -1, 'Neutronium Compressor': -1,
                   'Extreme Temperature Fluctuation Purification Unit': -1, 'High Energy Laser Purification Unit': -1,
                   'Mega Alloy Blast Smelter': -1, 'Matter Manipulator Quantum Uplink': -1,
                   'Integrated Ore Factory': -1, 'Electric Implosion Compressor': -1,
                   'Draconic Evolution Fusion Crafter': -1, 'Naquadah Fuel Refinery': -1,
                   'Miniature Wormhole Generator': -1, 'Absolute Baryonic Perfection Purification Unit': -1,
                   'Residual Decontaminant Degasser Purification Unit': -1, 'Nanochip Assembly Complex': -1,
                   'Exo-Foundry': -1, 'Quantum Force Transformer': -1,
                   'Dimensionally Transcendent Plasma Forge': -1, 'Dyson Swarm Ground Unit': -1,
                   'Transcendent Plasma Mixer': -1, 'Forge of the Gods': -1,
                   'Semi-Stable Antimatter Stabilization Sequencer': -1, 'Shielded Lagrangian Annihilation Matrix': -1,
                   'Pseudostable Black Hole Containment Field': -1, 'Draconic Reactor': -1,
                   'Eye of Harmony': -1, 'Stargate': 0}
# Use a dict if you want to specify numbers per IO type
# Use "*" as a key in the specific IO dict to assign a number to everything that's left
# Every IO group is a dict. If it is not, then it is counted as non-existing.
# The "MAIN" key of the IO group dict is the main IO group.
# Every key that isn't "MAIN" is a display name for that IO group. For example, "Top" would become "Top IO #1", "Top IO #2", etc.
# If you have "MAIN" in MaxIO and other IO groups in IOPorts, "MAIN" will be used for all of the groups at the same time.
# Apparently i need to specify total hatches - 1 (maint)
multiblockMaxIO = {'Coke Oven': 0, 'Water Tank': 0,
                   'Bricked Blast Furnace': 0, 'Railcraft Boiler': 0,
                   'Railcraft Tank': -1, 'Water Pump': {"MAIN": 2},
                   'Charcoal Pile Igniter': 0, 'Steam Oven': 0,
                   'Steam Hearth': -1, 'Steam Grinder': {"MAIN": 11},
                   'Steam Squasher': {"MAIN": 8}, 'Steam Purifier': {"MAIN": 8},
                   'Steam Separator': {"MAIN": 9}, 'Steam Blender': {"MAIN": 15},
                   'Steam Presser': {"MAIN": 7}, 'Steam Fuser': {"MAIN": 4},
                   'Electric Blast Furnace': {"Top": 9, "Bottom": 8}, 'Electric Air Filter': -1,
                   'Pyrolyse Oven': -1, 'Advanced Coke Oven': 0,
                   'Fluid Drilling Rig': {"MAIN": 7}, 'ExxonMobil Chemical Plant': -1,
                   'Large Boiler': -1, 'Algae Farm': -1,
                   'Concrete Backfiller': -1, 'Cleanroom': -1,
                   'Vacuum Freezer': -1, 'Oil Cracking Unit': -1,
                   'Large Chemical Reactor': {"MAIN": 16}, 'Distillation Tower': -1,
                   'Multi Smelter': -1, 'Large Steam Turbine': -1,
                   'XL Turbo Steam Turbine': -1, 'Large Sifter': {"MAIN": 20},
                   'Implosion Compressor': -1, 'Laminated Application and Thermal Enclosure eXpert (LATEX)': -1,
                   'Dissection Apparatus': -1, 'TurboCan Pro': -1,
                   'Bacterial Vat': -1, 'TFFT': -1, 'Big Barrel Brewery': {"MAIN": 10},
                   'Solar Factory': -1, 'Microwave Grinder': -1,
                   'Mega Electric Blast Furnace': -1, 'Mega Vacuum Freezer': -1,
                   'Mega Distillation Tower': -1, 'Mega Oil Cracker': -1,
                   'Industrial Coke Oven': -1, 'Extreme Entity Crusher': -1,
                   'Ore Drilling Plant': -1, 'Industrial Precision Lathe': -1,
                   'Industrial Material Press': -1, 'Large Electric Compressor': -1,
                   'Large Thermal Refinery': -1, 'Ore Washing Plant': -1,
                   'Industrial 3D Copying Machine': -1, 'Large Fluid Extractor': -1,
                   'Industrial Centrifuge': -1, 'Industrial Maceration Stack': -1,
                   'Dissolution Tank': -1, 'Large Gas Turbine': -1,
                   'Solid-Oxide Fuel Cell': -1, 'Large Semifluid Burner': -1,
                   'Large Combustion Engine': -1, 'Large Heat Exchanger': -1,
                   'Lapotronic Supercapacitor': -1, 'Tesla Tower': -1,
                   'Assembly Line': -1, 'Advanced Assembly Line': -1,
                   'Industrial Electrolyzer': -1, 'Industrial Mixing Machine': -1,
                   'Precise Auto-Assembler MT-3662': -1, 'Magnetic Flux Exhibitor': -1,
                   'Density^2': -1, 'Industrial Wire Factory': {"MAIN": 27},
                   'Industrial Extrusion Machine': -1, 'Alloy Blast Smelter': -1,
                   'Volcanus': -1, 'Industrial Cutting Factory': -1,
                   'Boldarnator': -1, 'Hyper-Intensity Laser Engraver': -1,
                   'Fluid Shaper': -1, 'Mass Solidifier': -1,
                   'Zyngen': -1, 'Dangote Distillus': -1,
                   'Industrial Sledgehammer': -1, 'Tree Growth Simulator': -1,
                   'Zhuhai Fishing Port': -1, 'Cryogenic Freezer': -1,
                   'Amazon Warehousing Depot': -1, 'Thermic Heating Device': -1,
                   'Thermal Boiler': -1, 'YOTTank': -1,
                   'Drone Centre': -1, 'Digester': -1,
                   'Rocketdyne F-1A Engine': -1, 'Decay Warehouse': -1,
                   'Solar Tower': -1, 'Extreme Combustion Engine': -1,
                   'Liquid Fluoride Thorium Reactor': -1, 'Reactor Fuel Processing Plant': -1,
                   'Nuclear Salt Processing Plant': -1, 'Thorium High Temperature Reactor': -1,
                   'High Temperature Gas-Cooled Reactor': -1, 'Planetary Gas Siphon': -1,
                   'Deep Earth Heating Pump': -1, 'Extreme Industrial Greenhouse': -1,
                   'Large Molecular Assembler': -1, 'Fusion Reactor': {"MAIN": {"Energy Hatch": [1,16], "Input Hatch": [1,16], "Output Hatch": [1,16]}},
                   'Compact Fusion Reactor': {"MAIN": {"Energy Hatch": [1,32], "Input Hatch": [1,16], "Output Hatch": [1,16]}}, 'Large Plasma Turbine': -1,
                   'XL Turbo Gas Turbine': -1, 'Neutron Activator': -1,
                   'Circuit Assembly Line': -1, 'Extreme Heat Exchanger': -1,
                   'Industrial Autoclave': -1, 'IsaMill Grinding Machine': -1,
                   'Flotation Cell Regulator': -1, 'Mega Chemical Reactor': -1,
                   'Universal Chemical Fuel Engine': -1, 'Cyclotron': -1,
                   'High Current Industrial Arc Furnace': -1, 'Utupu-Tanuri': -1,
                   'Whakawhiti Wera XL': -1, 'Molecular Transformer': -1,
                   'Ender Quarry': -1, 'Water Purification Plant': -1,
                   'Clarifier Purification Unit': -1, 'Ozonation Purification Unit': -1,
                   'Sparge Tower': -1, 'Active Transformer': {"MAIN": 20},
                   'Data Bank': -1, 'Large Naquadah Reactor': -1,
                   'XL Turbo Plasma Turbine': -1, 'Large Scale Auto-Assembler v1.01': -1,
                   'Void Miner': -1, 'Hot Isostatic Pressurization Unit': -1,
                   'Spinmatron-2737': -1, 'Flocculation Purification Unit': -1,
                   'pH Neutralization Purification Unit': -1, 'Energy Infuser': -1,
                   'Source Chamber': {"MAIN": 5}, 'Target Chamber': -1,
                   'Linear Accelerator': -1, 'Synchrotron': -1,
                   'Industrial Apicultural Acclimatiser and Drone Domestication Station': -1,
                   'Quantum Computer': -1, 'Research Station': -1,
                   'Network Switch With QoS': -1, 'Component Assembly Line': -1,
                   'PCB Factory': -1, 'Space Elevator': -1,
                   'Nano Forge': -1, 'Matter Fabrication CPU': -1,
                   'Elemental Duplicator': -1, 'Neutronium Compressor': -1,
                   'Extreme Temperature Fluctuation Purification Unit': -1, 'High Energy Laser Purification Unit': -1,
                   'Mega Alloy Blast Smelter': -1, 'Matter Manipulator Quantum Uplink': -1,
                   'Integrated Ore Factory': -1, 'Electric Implosion Compressor': -1,
                   'Draconic Evolution Fusion Crafter': -1, 'Naquadah Fuel Refinery': -1,
                   'Miniature Wormhole Generator': -1, 'Absolute Baryonic Perfection Purification Unit': -1,
                   'Residual Decontaminant Degasser Purification Unit': -1, 'Nanochip Assembly Complex': -1,
                   'Exo-Foundry': -1, 'Quantum Force Transformer': -1,
                   'Dimensionally Transcendent Plasma Forge': {"MAIN": {"Input Hatch": [0,7], "Output Hatch": [0,2], "Energy Hatch": [1,2], "Input Bus": [0,6], "Output Bus": [0,6]}}, 'Dyson Swarm Ground Unit': -1,
                   'Transcendent Plasma Mixer': {"MAIN": 36}, 'Forge of the Gods': -1,
                   'Semi-Stable Antimatter Stabilization Sequencer': -1, 'Shielded Lagrangian Annihilation Matrix': -1,
                   'Pseudostable Black Hole Containment Field': -1, 'Draconic Reactor': -1,
                   'Eye of Harmony': -1, 'Stargate': 0}
# If you want to add a maint hatch, do "M".
# To add a muffler hatch, do ["M",1]. Note that this is different from the maint hatch.
# Add "NONE" at the end of the list to exclude the port from IO calculations.
# Available hatches:
    # M - Muffler
    # IB - Input Bus
    # IB(S) - Input Bus (Steam)
    # OB - Output Bus
    # OB(S) - Output Bus (Steam)
    # EH - Energy Hatch
    # IH - Input Hatch
    # OH - Output Hatch
    # S - Steam Hatch
# Every IO group is a dict. If it is not, then it is counted as non-existing.
# The "MAIN" key of the IO group dict is the main IO group.
# Every key that isn't "MAIN" is a display name for that IO group. For example, "Top" would become "Top IO #1", "Top IO #2", etc.
multiblockIOPorts={'Coke Oven': 0, 'Water Tank': 0,
                   'Bricked Blast Furnace': 0, 'Railcraft Boiler': 0,
                   'Railcraft Tank': 0, 'Water Pump': {"MAIN": [["S",1,1],["OH",1,1]]},
                   'Charcoal Pile Igniter': 0, 'Steam Oven': 0,
                   'Steam Hearth': {"MAIN": [["S",1],["IB(S)",1],["OB(S)",1]]}, 'Steam Grinder': {"MAIN": [["IB(S)",1],["OB(S)",1],["S",1]]},
                   'Steam Squasher': {"MAIN": [["IB(S)",1],["OB(S)",1],["S",1]]}, 'Steam Purifier': {"MAIN": [["IB(S)",1],["OB(S)",1],["S",1],["IH",1]]},
                   'Steam Separator': {"MAIN": [["IB(S)",1],["OB(S)",1],["S",1],["OH",1]]}, 'Steam Blender': {"MAIN": [["IB(S)",1],["OB(S)",1],["S",1],["OH",1],["IH",1]]},
                   'Steam Presser': {"MAIN": [["IB(S)",1],["OB(S)",1],["S",1]]}, 'Steam Fuser': {"MAIN": [["IB(S)",1],["OB(S)",1],["S",1]]},
                   'Electric Blast Furnace': {"Top": [["OH",0],["M",1,1]], "Bottom": ["M",["IB",0],["OB",0],["IH",0],["OH",0],["EH",1]]}, 'Electric Air Filter': {"MAIN": ["M",["M",1,8],["EH",1],["IB",0],["OB",0]]},
                   'Pyrolyse Oven': {"MAIN": ["M",["M",1,1],["IB",0],["OB",0],["IH",0],["OH",0],["EH",1]]}, 'Advanced Coke Oven': 0,
                   'Fluid Drilling Rig': {"MAIN": ["M",["IB",0],["OH",1],["EH",1,1]]}, 'ExxonMobil Chemical Plant': {"MAIN": ["M",["C",0],["EH",1],["IB",0],["OB",0],["IH",0],["OH",0]]},
                   'Large Boiler': {"MAIN": ["M",["M",1,1],["IB",1,1],["IH",1,2],["OH",1,1]]}, 'Algae Farm': {"MAIN": [["IB",0],["IH",1],["OB",1]]},
                   'Concrete Backfiller': {"MAIN": ["M",["EH",1],["IB",0],["IH",1],["OB",0]]}, 'Cleanroom': -1,
                   'Vacuum Freezer': {"MAIN": ["M",["IB",0],["OB",0],["IH",0],["OH",0],["EH",1]]}, 'Oil Cracking Unit': {"MAIN": ["M",["EH",1],["IB",0],["IH",2,2],["OH",1,1]]},
                   'Large Chemical Reactor': {"MAIN": ["M",["EH",1],["IB",0],["OB",0],["IH",0],["OH",0]]}, 'Distillation Tower': {"MAIN": ["M",["IB",0],["OB",0],["IH",0],["OH",2],["EH",1]]},
                   'Multi Smelter': {"MAIN": ["M",["M",1,1],["IB",1],["OB",1],["EH",1]]}, 'Large Steam Turbine': {"MAIN": ["M",["IH",1],["OH",0],["DH",1,1]]},
                   'XL Turbo Steam Turbine': {"MAIN": ["M",["IB",1],["IH",1],["OH",1],["DH",1]]}, 'Large Sifter': {"MAIN": ["M",["M",1,1],["EH",1],["IB",0],["OB",0],["IH",0],["OH",0]]},
                   'Implosion Compressor': {"MAIN": ["M",["M",1,1],["EH",1],["IB",1],["OB",1]]}, 'Laminated Application and Thermal Enclosure eXpert (LATEX)': {"MAIN": ["M",["EH",1],["IB",0],["OB",0],["IH",0]]},
                   'Dissection Apparatus': {"MAIN": ["M",["EH",1],["IB",1],["OB",1]]}, 'TurboCan Pro': {"MAIN": ["M",["EH",1],["IB",0],["OB",0],["IH",0],["OH",0]]},
                   'Bacterial Vat': -1, 'TFFT': -1, 'Big Barrel Brewery': {"MAIN": ["M",["EH",1],["IB",0],["OB",0],["IH",0],["OH",0]]},
                   'Solar Factory': {"MAIN": ["M",["EH",1],["IB",0],["IH",0],["OB",0]]}, 'Microwave Grinder': {"MAIN": ["M",["EH",1],["OB",0]]},
                   'Mega Electric Blast Furnace': -1, 'Mega Vacuum Freezer': -1,
                   'Mega Distillation Tower': -1, 'Mega Oil Cracker': -1,
                   'Industrial Coke Oven': -1, 'Extreme Entity Crusher': -1,
                   'Ore Drilling Plant': -1, 'Industrial Precision Lathe': -1,
                   'Industrial Material Press': -1, 'Large Electric Compressor': -1,
                   'Large Thermal Refinery': -1, 'Ore Washing Plant': -1,
                   'Industrial 3D Copying Machine': -1, 'Large Fluid Extractor': -1,
                   'Industrial Centrifuge': -1, 'Industrial Maceration Stack': -1,
                   'Dissolution Tank': -1, 'Large Gas Turbine': -1,
                   'Solid-Oxide Fuel Cell': -1, 'Large Semifluid Burner': -1,
                   'Large Combustion Engine': -1, 'Large Heat Exchanger': -1,
                   'Lapotronic Supercapacitor': -1, 'Tesla Tower': -1,
                   'Assembly Line': -1, 'Advanced Assembly Line': -1,
                   'Industrial Electrolyzer': -1, 'Industrial Mixing Machine': -1,
                   'Precise Auto-Assembler MT-3662': -1, 'Magnetic Flux Exhibitor': -1,
                   'Density^2': -1, 'Industrial Wire Factory': {"MAIN": ["M",["M",1,1],["IB",1],["OB",1],["EH",1]]},
                   'Industrial Extrusion Machine': -1, 'Alloy Blast Smelter': -1,
                   'Volcanus': -1, 'Industrial Cutting Factory': -1,
                   'Boldarnator': -1, 'Hyper-Intensity Laser Engraver': -1,
                   'Fluid Shaper': -1, 'Mass Solidifier': -1,
                   'Zyngen': -1, 'Dangote Distillus': -1,
                   'Industrial Sledgehammer': -1, 'Tree Growth Simulator': -1,
                   'Zhuhai Fishing Port': -1, 'Cryogenic Freezer': -1,
                   'Amazon Warehousing Depot': -1, 'Thermic Heating Device': -1,
                   'Thermal Boiler': -1, 'YOTTank': -1,
                   'Drone Centre': -1, 'Digester': -1,
                   'Rocketdyne F-1A Engine': -1, 'Decay Warehouse': -1,
                   'Solar Tower': -1, 'Extreme Combustion Engine': -1,
                   'Liquid Fluoride Thorium Reactor': -1, 'Reactor Fuel Processing Plant': -1,
                   'Nuclear Salt Processing Plant': -1, 'Thorium High Temperature Reactor': -1,
                   'High Temperature Gas-Cooled Reactor': -1, 'Planetary Gas Siphon': -1,
                   'Deep Earth Heating Pump': -1, 'Extreme Industrial Greenhouse': -1,
                   'Large Molecular Assembler': -1, 'Fusion Reactor': {"MAIN": [["EH",1],["IH",1],["OH",1]]},
                   'Compact Fusion Reactor': {"MAIN": [["EH",1],["IH",1],["OH",1]]}, 'Large Plasma Turbine': -1,
                   'XL Turbo Gas Turbine': -1, 'Neutron Activator': -1,
                   'Circuit Assembly Line': -1, 'Extreme Heat Exchanger': -1,
                   'Industrial Autoclave': -1, 'IsaMill Grinding Machine': -1,
                   'Flotation Cell Regulator': -1, 'Mega Chemical Reactor': -1,
                   'Universal Chemical Fuel Engine': -1, 'Cyclotron': -1,
                   'High Current Industrial Arc Furnace': -1, 'Utupu-Tanuri': -1,
                   'Whakawhiti Wera XL': -1, 'Molecular Transformer': -1,
                   'Ender Quarry': -1, 'Water Purification Plant': -1,
                   'Clarifier Purification Unit': -1, 'Ozonation Purification Unit': -1,
                   'Sparge Tower': -1, 'Active Transformer': {"MAIN": [["EH",1],["DH",1]]},
                   'Data Bank': -1, 'Large Naquadah Reactor': -1,
                   'XL Turbo Plasma Turbine': -1, 'Large Scale Auto-Assembler v1.01': -1,
                   'Void Miner': -1, 'Hot Isostatic Pressurization Unit': -1,
                   'Spinmatron-2737': -1, 'Flocculation Purification Unit': -1,
                   'pH Neutralization Purification Unit': -1, 'Energy Infuser': -1,
                   'Source Chamber': {"MAIN": ["M",["EH",1,1],["IB",1,1],["IH",1,1],["OB",1,1]]}, 'Target Chamber': -1,
                   'Linear Accelerator': -1, 'Synchrotron': -1,
                   'Industrial Apicultural Acclimatiser and Drone Domestication Station': -1,
                   'Quantum Computer': -1, 'Research Station': -1,
                   'Network Switch With QoS': -1, 'Component Assembly Line': -1,
                   'PCB Factory': -1, 'Space Elevator': -1,
                   'Nano Forge': -1, 'Matter Fabrication CPU': -1,
                   'Elemental Duplicator': -1, 'Neutronium Compressor': -1,
                   'Extreme Temperature Fluctuation Purification Unit': -1, 'High Energy Laser Purification Unit': -1,
                   'Mega Alloy Blast Smelter': -1, 'Matter Manipulator Quantum Uplink': -1,
                   'Integrated Ore Factory': {"MAIN": ["M",["M",1],["IB",1],["OB",1],["IH",1],["EH",1]]}, 'Electric Implosion Compressor': {"MAIN": ["M",["IB",0],["OB",0],["IH",0],["OH",0],["EH",1]]},
                   'Draconic Evolution Fusion Crafter': {"MAIN": ["M",["IB",0],["OB",0],["IH",0],["OH",0],["EH",1]]}, 'Naquadah Fuel Refinery': {"MAIN": [["IB",1],["OH",1],["IH",1],["EH",1]]},
                   'Miniature Wormhole Generator': -1, 'Absolute Baryonic Perfection Purification Unit': -1,
                   'Residual Decontaminant Degasser Purification Unit': -1, 'Nanochip Assembly Complex': -1,
                   'Exo-Foundry': -1, 'Quantum Force Transformer': -1,
                   'Dimensionally Transcendent Plasma Forge': {"MAIN": ["M",["IB",0],["OB",0],["IH",0],["OH",0],["EH",1]]}, 'Dyson Swarm Ground Unit': {"MAIN": ["M",["IB",1],["IH",1],["EH",1],["ORC"]]},
                   'Transcendent Plasma Mixer': {"MAIN": ["M",["IB",0],["IH",0],["OH",0]]}, 'Forge of the Gods': -1,
                   'Semi-Stable Antimatter Stabilization Sequencer': -1, 'Shielded Lagrangian Annihilation Matrix': -1,
                   'Pseudostable Black Hole Containment Field': -1, 'Draconic Reactor': -1,
                   'Eye of Harmony': -1, 'Stargate': 0}
# -1 if not implemented, list of dicts if multiple tiers, dict if one tier
# Do not include the maintenance hatches!
multiblockCost =  {'Coke Oven': {"Coke Oven Brick (Block)": 26}, 'Water Tank': {"Water Tank Siding": 26},
                   'Bricked Blast Furnace': {"Bricked Blast Furnace": 1, "Firebricks": 32}, 'Railcraft Boiler': 0,
                   'Railcraft Tank': -1, 'Water Pump': [{"Water Pump": 1, "Bronze Frame Box": 10},{"Water Pump": 1, "Steel Frame Box": 10}],
                   'Charcoal Pile Igniter': -1, 'Steam Oven': {"Steam Oven": 8},
                   'Steam Hearth': -1, 'Steam Grinder': [{"Steam Grinder": 1}, {"Steam Grinder": 1}],
                   'Steam Squasher': [{"Steam Squasher": 1}, {"Steam Squasher": 1}], 'Steam Purifier': [{"Steam Purifier": 1, "Bronze Pipe Casing": 12, "Bronze Gear Box Casing": 8, "Glass": 24}, {"Steam Purifier": 1, "Steel Pipe Casing": 12, "Steel Gear Box Casing": 8, "Glass": 24}],
                   'Steam Separator': [{"Steam Separator": 1, "Bronze Pipe Casing": 4, "Bronze Gear Box Casing": 8, "Bronze Firebox Casing": 3}, {"Steam Separator": 1, "Steel Pipe Casing": 4, "Steel Gear Box Casing": 8, "Steel Firebox Casing": 3}], 'Steam Blender': [{"Steam Blender": 1, "Bronze Pipe Casing": 2, "Bronze Gear Box Casing": 2, "Block of Iron": 8}, {"Steam Blender": 1, "Steel Pipe Casing": 2, "Steel Gear Box Casing": 2, "Block of Iron": 8}],
                   'Steam Presser': [{"Steam Presser": 1, "Bronze Pipe Casing": 2, "Block of Iron": 2}, {"Steam Presser": 1, "Steel Pipe Casing": 2, "Block of Steel": 2}], 'Steam Fuser': [{"Steam Fuser": 1, "Bronze Pipe Casing": 2, Item("GLASS"): 4}, {"Steam Fuser": 1, "Steel Pipe Casing": 2, Item("GLASS"): 4}],
                   'Electric Blast Furnace': {"Electric Blast Furnace": 1, "Cupronickel Coil Block": 16}, 'Electric Air Filter': -1,
                   'Pyrolyse Oven': {"Pyrolyse Oven": 1, "Cupronickel Coil Block": 9}, 'Advanced Coke Oven': {"Advanced Coke Oven Brick (Block)": 34},
                   'Fluid Drilling Rig': [{"Fluid Drilling Rig": 1, "Solid Steel Machine Casing": 3, "Steel Frame Box": 15}, {"Fluid Drilling Rig II": 1, "Clean Stainless Steel Casing": 3, "Stainless Steel Frame Box": 15}, {"Fluid Drilling Rig III": 1, "Stable Titanium Machine Casing": 3, "Titanium Frame Box": 15}, {"Fluid Drilling Rig IV": 1, "Robust Tungstensteel Machine Casing": 3, "Tungstenteel Frame Box": 15}, {"Infinite Fluid Drilling Rig": 1, "Mining Neutronium Casing": 3, "Neutronium Frame Box": 15}], 'ExxonMobil Chemical Plant': -1,
                   'Large Boiler': -1, 'Algae Farm': {"Algae Farm": 1, "Sterile Farm Casing": 64},
                   'Concrete Backfiller': -1, 'Cleanroom': -1,
                   'Vacuum Freezer': {"Vacuum Freezer": 1}, 'Oil Cracking Unit': -1,
                   'Large Chemical Reactor': {"Large Chemical Reactor": 1, "PTFE Pipe Casing": 1, "Cupronickel Coil Block": 1}, 'Distillation Tower': -1,
                   'Multi Smelter': {"Multi Smelter": 1, "Cupronickel Coil Block": 8}, 'Large Steam Turbine': -1,
                   'XL Turbo Steam Turbine': -1, 'Large Sifter': {"Large Sifter Control Block": 1, "Large Sieve Grate": 18},
                   'Implosion Compressor': -1, 'Laminated Application and Thermal Enclosure eXpert (LATEX)': -1,
                   'Dissection Apparatus': -1, 'TurboCan Pro': {"TurboCan Pro": 1, "Steel Pipe Casing": 24},
                   'Bacterial Vat': -1, 'TFFT': -1, 'Big Barrel Brewery': {"Big Barrel Brewery": 1, "Steel Frame Box": 4, Item("GLASS"): 6},
                   'Solar Factory': [{"Solar Factory": 1, "Damascus Steel Frame Box": 20}, {"Solar Factory": 1, "Tungsten Steel Frame Box": 75}, {"Solar Factory": 1, "Tungsten Steel Frame Box": 24,"Black Plutonium Item Pipe": 6}], 'Microwave Grinder': {"Microwave Grinder": 1},
                   'Mega Electric Blast Furnace': -1, 'Mega Vacuum Freezer': -1,
                   'Mega Distillation Tower': -1, 'Mega Oil Cracker': -1,
                   'Industrial Coke Oven': -1, 'Extreme Entity Crusher': -1,
                   'Ore Drilling Plant': -1, 'Industrial Precision Lathe': -1,
                   'Industrial Material Press': -1, 'Large Electric Compressor': -1,
                   'Large Thermal Refinery': -1, 'Ore Washing Plant': -1,
                   'Industrial 3D Copying Machine': -1, 'Large Fluid Extractor': -1,
                   'Industrial Centrifuge': -1, 'Industrial Maceration Stack': -1,
                   'Dissolution Tank': -1, 'Large Gas Turbine': -1,
                   'Solid-Oxide Fuel Cell': -1, 'Large Semifluid Burner': -1,
                   'Large Combustion Engine': -1, 'Large Heat Exchanger': -1,
                   'Lapotronic Supercapacitor': -1, 'Tesla Tower': -1,
                   'Assembly Line': -1, 'Advanced Assembly Line': -1,
                   'Industrial Electrolyzer': -1, 'Industrial Mixing Machine': -1,
                   'Precise Auto-Assembler MT-3662': -1, 'Magnetic Flux Exhibitor': -1,
                   'Density^2': -1, 'Industrial Wire Factory': {"Industrial Wire Factory": 1},
                   'Industrial Extrusion Machine': -1, 'Alloy Blast Smelter': -1,
                   'Volcanus': -1, 'Industrial Cutting Factory': -1,
                   'Boldarnator': -1, 'Hyper-Intensity Laser Engraver': -1,
                   'Fluid Shaper': -1, 'Mass Solidifier': -1,
                   'Zyngen': -1, 'Dangote Distillus': -1,
                   'Industrial Sledgehammer': -1, 'Tree Growth Simulator': -1,
                   'Zhuhai Fishing Port': -1, 'Cryogenic Freezer': -1,
                   'Amazon Warehousing Depot': -1, 'Thermic Heating Device': -1,
                   'Thermal Boiler': -1, 'YOTTank': -1,
                   'Drone Centre': -1, 'Digester': -1,
                   'Rocketdyne F-1A Engine': -1, 'Decay Warehouse': -1,
                   'Solar Tower': -1, 'Extreme Combustion Engine': -1,
                   'Liquid Fluoride Thorium Reactor': -1, 'Reactor Fuel Processing Plant': -1,
                   'Nuclear Salt Processing Plant': -1, 'Thorium High Temperature Reactor': -1,
                   'High Temperature Gas-Cooled Reactor': -1, 'Planetary Gas Siphon': -1,
                   'Deep Earth Heating Pump': -1, 'Extreme Industrial Greenhouse': -1,
                   'Large Molecular Assembler': -1, 'Fusion Reactor': [{"Fusion Control Computer Mark I": 1, "Drone DownLink Module": 1, "Superconducting Coil Block": 32},{"Fusion Control Computer Mark II": 1, "Drone DownLink Module": 1, "Fusion Coil Block": 32},{"Fusion Control Computer Mark III": 1, "Drone DownLink Module": 1, "Fusion Coil Block": 32},{"FusionTech MK IV": 1, "Drone DownLink Module": 1, "Advanced Fusion Coil": 32},{"FusionTech MK V": 1, "Drone DownLink Module": 1, "Advanced Fusion Coil II": 32}],
                   'Compact Fusion Reactor': [{"Compact Fusion Computer MK-I Prototype": 1, "Drone DownLink Module": 2, "Ameliorated Superconduct Coil": 560, "Naquadah Alloy Frame Box": 128},{"Compact Fusion Computer MK-II": 1, "Drone DownLink Module": 2, "Compact Fusion Coil": 560, "Duranium Frame Box": 128},{"Compact Fusion Computer MK-III": 1, "Drone DownLink Module": 2, "Advanced Compact Fusion Coil": 560, "Neutronium Frame Box": 128},{"Compact Fusion Computer MK-IV Prototype": 1, "Drone DownLink Module": 2, "Compact Fusion Coil MK-II Prototype": 560, "Infinity Catalyst Frame Box": 128},{"Compact Fusion Computer MK-V": 1, "Drone DownLink Module": 2, "Compact Fusion Coil MK-II Finaltype": 560, "Infinity Frame Box": 128}], 'Large Plasma Turbine': -1,
                   'XL Turbo Gas Turbine': -1, 'Neutron Activator': -1,
                   'Circuit Assembly Line': -1, 'Extreme Heat Exchanger': -1,
                   'Industrial Autoclave': -1, 'IsaMill Grinding Machine': -1,
                   'Flotation Cell Regulator': -1, 'Mega Chemical Reactor': -1,
                   'Universal Chemical Fuel Engine': -1, 'Cyclotron': -1,
                   'High Current Industrial Arc Furnace': -1, 'Utupu-Tanuri': -1,
                   'Whakawhiti Wera XL': -1, 'Molecular Transformer': -1,
                   'Ender Quarry': -1, 'Water Purification Plant': -1,
                   'Clarifier Purification Unit': -1, 'Ozonation Purification Unit': -1,
                   'Sparge Tower': -1, 'Active Transformer': {"Active Transformer": 1, "Superconducting Coil Block": 1},
                   'Data Bank': -1, 'Large Naquadah Reactor': -1,
                   'XL Turbo Plasma Turbine': -1, 'Large Scale Auto-Assembler v1.01': -1,
                   'Void Miner': -1, 'Hot Isostatic Pressurization Unit': -1,
                   'Spinmatron-2737': -1, 'Flocculation Purification Unit': -1,
                   'pH Neutralization Purification Unit': -1, 'Energy Infuser': -1,
                   'Source Chamber': {"Source Chamber": 1, "Shielded Accelerator Casing": 56, "Shielded Accelerator Glass": 52, "Electrode Casing": 16, "LuV Beamline Output Hatch": 1}, 'Target Chamber': -1,
                   'Linear Accelerator': -1, 'Synchrotron': -1,
                   'Industrial Apicultural Acclimatiser and Drone Domestication Station': -1,
                   'Quantum Computer': -1, 'Research Station': -1,
                   'Network Switch With QoS': -1, 'Component Assembly Line': -1,
                   'PCB Factory': -1, 'Space Elevator': -1,
                   'Nano Forge': -1, 'Matter Fabrication CPU': -1,
                   'Elemental Duplicator': -1, 'Neutronium Compressor': -1,
                   'Extreme Temperature Fluctuation Purification Unit': -1, 'High Energy Laser Purification Unit': -1,
                   'Mega Alloy Blast Smelter': -1, 'Matter Manipulator Quantum Uplink': -1,
                   'Integrated Ore Factory': -1, 'Electric Implosion Compressor': -1,
                   'Draconic Evolution Fusion Crafter': -1, 'Naquadah Fuel Refinery': -1,
                   'Miniature Wormhole Generator': -1, 'Absolute Baryonic Perfection Purification Unit': -1,
                   'Residual Decontaminant Degasser Purification Unit': -1, 'Nanochip Assembly Complex': -1,
                   'Exo-Foundry': -1, 'Quantum Force Transformer': -1,
                   'Dimensionally Transcendent Plasma Forge': [{"Dimensionally Transcendent Plasma Forge": 1, "Dimensionally Transcendent Casing": 2121, "Dimensional Bridge": 120, "Awakened Draconium Coil": 2112},{"Dimensionally Transcendent Plasma Forge": 1, "Dimensionally Transcendent Casing": 2121, "Dimensional Bridge": 120, "Hypogen Coil": 2112},{"Dimensionally Transcendent Plasma Forge": 1, "Dimensionally Transcendent Casing": 2121, "Dimensional Bridge": 120, "Infinity Coil": 2112},{"Dimensionally Transcendent Plasma Forge": 1, "Dimensionally Transcendent Casing": 2121, "Dimensional Bridge": 120, "Eternal Coil": 2112}], 'Dyson Swarm Ground Unit': -1,
                   'Transcendent Plasma Mixer': {"Transcendent Plasma Mixer": 1, "Dimensional Bridge": 16, "Dimensionally Transcendent Casing": 48}, 'Forge of the Gods': -1,
                   'Semi-Stable Antimatter Stabilization Sequencer': {"Semi-Stable Antimatter Stabilization Sequencer": 1, "Magnetic Flux Casing": 2274, "Protomatter Activation Coil": 126, "Antimatter Hatch": 16}, 'Shielded Lagrangian Annihilation Matrix': {"Shielded Lagrangian Annihilation Matrix": 1, "Transcendentally Reinforced Borosilicate Glass": 1008, "Antimatter Annihilation Matrix": 600, "Naquadria Frame Box": 292, "Advanced Filter Casing": 209, "Protomatter Activation Coil": 32},
                   'Pseudostable Black Hole Containment Field': {"Pseudostable Black Hole Containment Field": 1, "Extreme Density Space-Bending Casing": 3670, "Naquadah Alloy Frame Box": 144, "Hawking Radiation Realignment Focus": 64}, 'Draconic Reactor': {"Reactor Stabilizer": 4, "Draconic Reactor Core": 1, "Reactor Energy Injector": 1},
                   'Eye of Harmony': -1, 'Stargate': {"Stargate Base": 1, "Stargate Controller": 1, "RF Stargate Power Unit": 1, "Stargate Ring Block": 8, "Stargate Chevron Block": 7}}

ioStr = ""
for i in multiblockIOPorts:
    if(multiblockIOPorts[i] != -1 and multiblockCasing[i] != -1 and multiblockIOPorts[i] != 0 and multiblockCasing[i] != 0 and type(multiblockMaxIO[i]) is not type(0)):
        if("MAIN" in multiblockIOPorts[i] and "MAIN" in multiblockMaxIO[i]):
            # Skips if maxIO is a dict
            # -----
            # Stops if not implemented (any of the three being -1 will trigger this)
            # Stops if no casing (casing always uses a list)
            # Stops if maximum IO is 0 (doesn't use IO) or -1 (not implemented)
            # Stops if no IO (IO always uses a list)
            if(type(multiblockMaxIO[i]["MAIN"]) is not type({})):
                if(type(multiblockCasing[i]) is not type([]) or multiblockMaxIO[i]["MAIN"] < 1 or type(multiblockIOPorts[i]["MAIN"]) is not type([])):
                    continue

            warnings = []

            print('[LOG][ioCalculations] Processing IO ports for multiblock "'+str(i)+'"')
            ioStr += ''' else if(multiblockName == "'''+i+'''") {
            '''

            # Still doing this part manually
            if(i == "Fusion Reactor"):
                ioStr += '''if(wallshareMaxIHModifier == -16) {  // Special sceario where the fusion reactor will have all of its possible input hatches wallshared
                inputHatchCount = 0;
            }
            '''

            # multiblockCasing = ALL the casings
            # multiblockCasing[i] = Casing for current multiblock
            # multiblockCasing[i][0] =
            #   1. Is multi-tier ( {} )
            #   2. List of casing types
            #   3. Amount of the casing
            # multiblockCasing[i][1] =
            #   1. First tier of the casing
            #   2. INVALID
            #   3. Name of the casing
            # multiblockCasing[i][2+] =
            #   1. Second+ tier of the casing
            #   2. INVALID
            #   3. INVALID
            # multiblockCasing[i][1][0] =
            #   1. First type of the first tier
            #   2. Amount of the first tier casing
            # multiblockCasing[i][1][1] =
            #   1. Second type of the first tier
            #   2. Number of the first tier casing
            if(type(multiblockCasing[i][0]) is type({})):
                ioStr += '''
                if(false) {

                }'''  # if i want else if i will get else if
                if(type(multiblockCasing[i][1][0]) is type([])):
                    # Multi-tier and multi-type     (n casing, n tiers)
                    for i2 in range(len(multiblockCasing[i]))[1:]:  # Iterate through all tiers
                        print("[LOG][ioCalculations] Processing multi-type tier "+str(i2)+' for multiblock "'+str(i)+'"')
                        ioStr += ''' else if(tier == '''+str(i2)+''') {
                    table.innerHTML += \''''
                        for i3 in range(len(multiblockCasing[i][i2])):  # Iterate through all casing types
                            ioStr += '''<tr><td class="center"></td><td class="center"><span id="casing'''+str(i3)+'''">\'+String('''+str(multiblockCasing[i][i2][i3][0])+'''+wallshareCasingModifier)+\'</span>x '''+str(multiblockCasing[i][i2][i3][1])+'''</td><td class="center"></td></tr>'''
                        tmp = appendIOStr(multiblockIOPorts[i]["MAIN"])
                        ioStr += tmp[0]+'''
                }'''
                        warnings.extend(tmp[1])
                else:
                    # Multi-tier but not multi-type (one casing, n tiers)
                    for i2 in range(len(multiblockCasing[i]))[1:]:  # Iterate through all tiers
                        print("[LOG][ioCalculations] Processing non multi-type tier "+str(i2)+' for multiblock "'+str(i)+'"')
                        ioStr += ''' else if(tier == '''+str(i2)+''') {
                    table.innerHTML += \'<tr><td class="center"></td><td class="center"><span id="casing">\'+String('''+str(multiblockCasing[i][i2][0])+'''+wallshareCasingModifier)+\'</span>x '''+str(multiblockCasing[i][i2][1])+'''</td><td class="center"></td></tr>'''
                        tmp = appendIOStr(multiblockIOPorts[i]["MAIN"])
                        ioStr += tmp[0]+'''
                }'''
                        warnings.extend(tmp[1])
            elif(type(multiblockCasing[i][0]) is type([])):
                # Not multi-tier but multi-type     (n casings, one tier)
                ioStr += "table.innerHTML += \'"
                for i2 in range(len(multiblockCasing[i])):  # Iterate through all casing types
                    ioStr += '''<tr><td class="center"></td><td class="center"><span id="casing'''+str(i2)+'''">\'+String('''+str(multiblockCasing[i][i2][0])+'''+wallshareCasingModifier)+\'</span>x '''+str(multiblockCasing[i][i2][1])+'''</td><td class="center"></td></tr>'''
                tmp = appendIOStr(multiblockIOPorts[i]["MAIN"])
                ioStr += tmp[0]
                warnings.extend(tmp[1])
            else:
                # Not multi-tier and not multi-type (one casing, one tier)
                ioStr += '''table.innerHTML += \'<tr><td class="center"></td><td class="center"><span id="casing">\'+String('''+str(multiblockCasing[i][0])+'''+wallshareCasingModifier)+\'</span>x '''+str(multiblockCasing[i][1])+'''</td><td class="center"></td></tr>'''
                tmp = appendIOStr(multiblockIOPorts[i]["MAIN"])
                ioStr += tmp[0]
                warnings.extend(tmp[1])

            if("steamBusDisallowed" in warnings):
                ioStr += '''
            if(inputBuses == "Input Bus (Steam)" && outputBuses == "Output Bus (Steam)") {
                warning = "WARNING! You are using the Steam-tier input and output buses, which only work with Steam-tier machines. If you build this in-game, the multiblock will not form.";
            } else if(inputBuses == "Input Bus (Steam)") {
                warning = "WARNING! You are using the Steam-tier input bus, which only works with Steam-tier machines. If you build this in-game, the multiblock will not form.";
            } else if(outputBuses == "Output Bus (Steam)") {
                warning = "WARNING! You are using the Steam-tier output bus, which only works with Steam-tier machines. If you build this in-game, the multiblock will not form.";
            }'''
            ioStr += '''
        }'''
        else:
            if("MAIN" in multiblockIOPorts[i]):
                print("[ERROR][ioCalculations] Invalid data in multiblockMaxIO for "+str(i)+": "+str(multiblockMaxIO[i]))
            elif("MAIN" in multiblockMaxIO[i]):
                print("[ERROR][ioCalculations] Invalid data in multiblockIOPorts for "+str(i)+": "+str(multiblockIOPorts[i]))
            else:
                print("[ERROR][ioCalculations] Invalid data in multiblockMaxIO and multiblockIOPorts for "+str(i)+": "+str(multiblockMaxIO[i])+", "+str(multiblockIOPorts[i]))

multiblockCostStr = ""
for i in multiblockCost:
    multiblockCostStr += '''else if(e == "'''+i+'''") {
        '''
    if(type(multiblockCost[i]) == type([])):
        for i2 in range(len(multiblockCost[i])):
            if(i2 > 0):
                multiblockCostStr += "else "
            multiblockCostStr += '''if(tier == '''+str(i2+1)+''') {
            return '''+str(multiblockCost[i][i2])+''';}'''
    elif(type(multiblockCost[i]) == type({})):
        multiblockCostStr += "return "+str(multiblockCost[i])+";"
    multiblockCostStr += '''
    } '''

# -- Max IO --
maxIOStr = ""
for i in multiblockMaxIO:
    if(type(multiblockMaxIO[i]) == type(0)):
        if(multiblockMaxIO[i] == 0):
            pass
        elif(multiblockMaxIO[i] == -1):
            pass
        else:
            print("[ERROR][maxIOCalculations] Invalid data in multiblockMaxIO for "+str(i)+": "+str(multiblockMaxIO[i]))
    elif("MAIN" in multiblockMaxIO[i]):
        maxIOStr += """ else if(document.getElementById('titleText').innerHTML == '"""+str(i)+"""') {
            return """+str(multiblockMaxIO[i]["MAIN"])+""";
    	}"""
    else:
        print("[ERROR][maxIOCalculations] Invalid data in multiblockMaxIO for "+str(i)+": "+str(multiblockMaxIO[i]))

# -- Min IO --
minIOStr = """if(false){
            console.log("wtf");
        }"""
for i in multiblockIOPorts:
    if(multiblockIOPorts[i] != -1 and multiblockCasing[i] != -1 and multiblockIOPorts[i] != 0 and multiblockCasing[i] != 0 and type(multiblockMaxIO[i]) is not type(0)):
        if("MAIN" in multiblockIOPorts[i] and "MAIN" in multiblockMaxIO[i]):
            minIOStr += """ else if(multiName == '"""+str(i)+"""') {
            if(false){
                console.log("wtf");
            }"""
            for i2 in multiblockIOPorts[i]["MAIN"]:
                if(type(i2) == type([])):
                    if(i2[0] == "IB" or i2[0] == "IB(S)"):
                        minIOStr += """ else if(hatchName == "inputB") {
                return """+str(i2[1])+""";
            }"""
                    elif(i2[0] == "OB" or i2[0] == "OB(S)"):
                        minIOStr += """ else if(hatchName == "outputB") {
                return """+str(i2[1])+""";
            }"""
                    elif(i2[0] == "IH"):
                        minIOStr += """ else if(hatchName == "Ihatch") {
                return """+str(i2[1])+""";
            }"""
                    elif(i2[0] == "OH"):
                        minIOStr += """ else if(hatchName == "Ohatch") {
                return """+str(i2[1])+""";
            }"""
                    elif(i2[0] == "S"):
                        minIOStr += """ else if(hatchName == "steam") {
                return """+str(i2[1])+""";
            }"""
                    elif(i2[0] == "EH"):
                        minIOStr += """ else if(hatchName == "energy") {
                return """+str(i2[1])+""";
            }"""
                    elif(i2[0] == "DH"):
                        minIOStr += """ else if(hatchName == "dynamo") {
                return """+str(i2[1])+""";
            }"""
                    elif(i2[0] == "C"):
                        minIOStr += """ else if(hatchName == "Chousing") {
                return """+str(i2[1])+""";
            }"""

            minIOStr += """
        }"""
        else:
            print("[ERROR][minIOCalculations] Invalid data in multiblockIOPorts for "+str(i)+": "+str(multiblockMaxIO[i]))
            minIOStr += """ else if(document.getElementById('titleText').innerHTML == '"""+str(i)+"""') {
            return 1;
        }"""
    else:
        minIOStr += """ else if(document.getElementById('titleText').innerHTML == '"""+str(i)+"""') {
            return 1;
        }"""

# IO Cost Calculations
ioCostCalculationsStr = ""
for i in multiblockIOPorts:
    if(multiblockIOPorts[i] != -1 and multiblockCasing[i] != -1 and multiblockIOPorts[i] != 0 and multiblockCasing[i] != 0 and type(multiblockMaxIO[i]) is not type(0)):
        if("MAIN" in multiblockIOPorts[i] and "MAIN" in multiblockMaxIO[i]):
            # Skips if maxIO is a dict
            # -----
            # Stops if not implemented (any of the three being -1 will trigger this)
            # Stops if no casing (casing always uses a list)
            # Stops if maximum IO is 0 (doesn't use IO) or -1 (not implemented)
            # Stops if no IO (IO always uses a list)
            if(type(multiblockMaxIO[i]["MAIN"]) is not type({})):
                if(type(multiblockCasing[i]) is not type([]) or multiblockMaxIO[i]["MAIN"] < 1 or type(multiblockIOPorts[i]["MAIN"]) is not type([])):
                    continue

            ioCostCalculationsStr += ''' else if(document.getElementById("titleText").innerHTML == "'''+i+'''") {
            '''

            # multiblockCasing = ALL the casings
            # multiblockCasing[i] = Casing for current multiblock
            # multiblockCasing[i][0] =
            #   1. Is multi-tier ( {} )
            #   2. List of casing types
            #   3. Amount of the casing
            # multiblockCasing[i][1] =
            #   1. First tier of the casing
            #   2. INVALID
            #   3. Name of the casing
            # multiblockCasing[i][2+] =
            #   1. Second+ tier of the casing
            #   2. INVALID
            #   3. INVALID
            # multiblockCasing[i][1][0] =
            #   1. First type of the first tier
            #   2. Amount of the first tier casing
            # multiblockCasing[i][1][1] =
            #   1. Second type of the first tier
            #   2. Number of the first tier casing
            if(type(multiblockCasing[i][0]) is type({})):
                if(type(multiblockCasing[i][1][0]) is type([])):
                    ioCostCalculationsStr += '''
                if(false) {

                }'''
                    # Multi-tier and multi-type     (n casing, n tiers)
                    for i2 in range(len(multiblockCasing[i]))[1:]:  # Iterate through all tiers
                        ioCostCalculationsStr += ''' else if(tierSelected == '''+str(i2)+''') {
                        '''
                        for i3 in range(len(multiblockCasing[i][i2])):  # Iterate through all casing types
                            ioCostCalculationsStr += '''var casing'''+str(i3)+''' = document.getElementById("casing'''+str(i3)+'''");
                            initialCost["'''+str(multiblockCasing[i][i2][i3][1])+'''"] = Number(casing'''+str(i3)+'''.innerHTML);
                            '''
                        ioCostCalculationsStr += '''
                '''+appendIOCostStr(multiblockIOPorts[i]["MAIN"])+'''
                }'''
                else:
                    # Multi-tier but not multi-type (one casing, n tiers)
                    ioCostCalculationsStr += '''var casing = document.getElementById("casing");
            '''
                    ioCostCalculationsStr += '''
                if(false) {

                }'''
                    for i2 in range(len(multiblockCasing[i]))[1:]:  # Iterate through all tiers
                        ioCostCalculationsStr += ''' else if(tierSelected == '''+str(i2)+''') {
                initialCost["'''+str(multiblockCasing[i][i2][1])+'''"] = Number(casing.innerHTML);
            '''+appendIOCostStr(multiblockIOPorts[i]["MAIN"])+'''
                }'''  # !TODO
            elif(type(multiblockCasing[i][0]) is type([])):
                # Not multi-tier but multi-type     (n casings, one tier)
                for i2 in range(len(multiblockCasing[i])):  # Iterate through all casing types
                    ioCostCalculationsStr += '''
            var casing'''+str(i2)+''' = document.getElementById("casing'''+str(i2)+'''");
            initialCost["'''+str(multiblockCasing[i][i2][1])+'''"] = Number(casing'''+str(i2)+'''.innerHTML);
            '''+appendIOCostStr(multiblockIOPorts[i]["MAIN"])
            else:
                # Not multi-tier and not multi-type (one casing, one tier)
                ioCostCalculationsStr += '''var casing = document.getElementById("casing");
            initialCost["'''+str(multiblockCasing[i][1])+'''"] = Number(casing.innerHTML);
            '''+appendIOCostStr(multiblockIOPorts[i]["MAIN"])

            ioCostCalculationsStr += '''
        }'''
        else:
            if("MAIN" in multiblockIOPorts[i]):
                print("[ERROR][ioCostCalculations] Invalid data in multiblockMaxIO for "+str(i)+": "+str(multiblockMaxIO[i]))
            elif("MAIN" in multiblockMaxIO[i]):
                print("[ERROR][ioCostCalculations] Invalid data in multiblockIOPorts for "+str(i)+": "+str(multiblockIOPorts[i]))
            else:
                print("[ERROR][ioCostCalculations] Invalid data in multiblockMaxIO and multiblockIOPorts for "+str(i)+": "+str(multiblockMaxIO[i])+", "+str(multiblockIOPorts[i]))

# -- IO functions strings --
steamHatchStr = getIOSelectedStr("steam", "S")
IhatchStr = getIOSelectedStr("Ihatch", "IH")
OhatchStr = getIOSelectedStr("Ohatch", "OH")
IBusStr = getIOSelectedStr("inputB", "IB", "IB(S)")
OBusStr = getIOSelectedStr("outputB", "OB", "IB(S)")
DynamoStr = getIOSelectedStr("dynamo", "DH")
EnergyStr = getIOSelectedStr("energy", "EH")
ChousingStr = getIOSelectedStr("CHousing", "C")

# -- IO Group Multiblocks --
for i in multiblockMaxIO:
    if(type(multiblockMaxIO[i]) is type({})):
        if("MAIN" not in multiblockMaxIO[i]):
            pass

@app.route('/')
def main():
    a = render_template('index.html', recipeSelections=recipeSelections, options=options, multiblockSelectionList=multiblockSelectionList, recipeStr=recipeStr, recipeSelDict=recipeSelDict, maxIOStr=maxIOStr, minIOStr=minIOStr, multiblockCostStr=multiblockCostStr, ioStr=ioStr, steamHatchStr=steamHatchStr, IhatchStr=IhatchStr, OhatchStr=OhatchStr, IBusStr=IBusStr, OBusStr=OBusStr, DynamoStr=DynamoStr, EnergyStr=EnergyStr, ChousingStr=ChousingStr, ioCostCalculationsStr=ioCostCalculationsStr)
    if(debugFile):
        with open("resultHTML.html", "w") as f:
            f.write(str(a))
    return a

@app.route('/privacy')
def privacyPage():
    return render_template('privacyPage.html')