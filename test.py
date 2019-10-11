import re 

rasterName = "A2_Y2018_M7_9_VIS_BR_LVR1_DEM"

# Get the date and location
dateCode = { 
    "1_": "1",
    "2_": "2",
    "3_": "3",
    "4_": "4",
    "5_": "5",
    "6_": "6",
    "7_": "7",
    "8_": "8",
    "9_": "9",
    "10_": "10",
    "11_": "11",
    "12_": "12",
    "7_9_": "13",
} 
date = re.search(r"(?<=Y)[0-9]+", rasterName).group() + dateCode[re.search(r"(?<=M)[0-9_]+", rasterName).group()]
print(date)