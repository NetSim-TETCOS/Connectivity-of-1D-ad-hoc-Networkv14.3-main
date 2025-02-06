import subprocess
import random
import shutil
import numpy as np
import time
import os

# Set the path of 64-bit NetSim Binaries to be used for simulation.
NETSIM_PATH = "C:\\Users\\MIC\\Documents\\NetSim\\Workspaces\\Defv14-3-6\\bin_x64"
LICENSE_ARG = "5053@192.168.0.4"

# Set NETSIM_AUTO environment variable to avoid keyboard interrupt at the end of each simulation
os.environ["NETSIM_AUTO"] = "1"

# Create directories if they don’t exist
os.makedirs("IOPath", exist_ok=True)
os.makedirs("Data", exist_ok=True)

# Clear IOPath directory from previous runs
for root, dirs, files in os.walk("IOPath"):
    for file in files:
        os.remove(os.path.join(root, file))

# Delete result.csv if it exists
if os.path.isfile("result.csv"):
    os.remove("result.csv")

# Create a CSV file to log output metrics
with open("result.csv", "w") as csvfile:
    csvfile.write("X1,X2,X3,X4,X5,X6,X7,X8,X9,X10,Range,Packets Received,")

# Create random UE positions
np.random.seed(0)
ran_arr = np.round(1000 * np.random.rand(100, 10), 2)
ran_arr = np.sort(ran_arr, axis=1)

# Create a timestamped output folder
foldername = time.strftime("%Y-%m-%d-%H.%M.%S")

# Iterate through parameter range
for j in range(50, 1001, 50):
    for i in range(100):  # Fixed indentation issue here

        # Remove old files before running the simulation
        for filename in ["Configuration.netsim", "IOPath\\Configuration.netsim", "IOPath\\Metrics.xml"]:
            if os.path.isfile(filename):
                os.remove(filename)

        # Call ConfigWriter.exe
        cmd = f'ConfigWriter.exe {ran_arr[i,0]} {ran_arr[i,1]} {ran_arr[i,2]} {ran_arr[i,3]} {ran_arr[i,4]} {ran_arr[i,5]} {ran_arr[i,6]} {ran_arr[i,7]} {ran_arr[i,8]} {ran_arr[i,9]} {j}'
        print(cmd)
        os.system(cmd)

        # Copy generated Configuration.netsim file
        if os.path.isfile("Configuration.netsim"):
            shutil.copy("Configuration.netsim", "IOPath\\Configuration.netsim")

        # Copy Additional Files
        if os.path.exists('ConfigSupport'):
            shutil.rmtree("IOPath\\ConfigSupport", ignore_errors=True)
            shutil.copytree("ConfigSupport", "IOPath\\ConfigSupport")

        # Run NetSim via CLI
        strIOPATH = os.getcwd() + "\\IOPath"
        cmd = (
            f'start "NetSim_Multi_Parameter_Sweeper" /wait /d "{NETSIM_PATH}" '
            f'NetSimcore.exe -apppath "{NETSIM_PATH}" -iopath "{strIOPATH}" -license {LICENSE_ARG}'
        )
        os.system(cmd)

        # Process Metrics.xml if available
        OUTPUT_PARAM_COUNT = 1
        if os.path.isfile("IOPath\\Metrics.xml"):
            shutil.copy("IOPath\\Metrics.xml", "Metrics.xml")
            os.system("MetricsCsv.exe IOPath")

            with open("result.csv", "a") as csvfile:
                csvfile.write(f"\n{ran_arr[i,0]},{ran_arr[i,1]},{ran_arr[i,2]},{ran_arr[i,3]},{ran_arr[i,4]},{ran_arr[i,5]},{ran_arr[i,6]},{ran_arr[i,7]},{ran_arr[i,8]},{ran_arr[i,9]},{j},")

            if OUTPUT_PARAM_COUNT == 1:
                subprocess.run(["MetricsReader.exe", "result.csv"], check=True)
            else:
                for n in range(1, OUTPUT_PARAM_COUNT + 1):
                    os.rename(f"Script{n}.txt", "Script.txt")
                    subprocess.run(["MetricsReader.exe", "result.csv"], check=True)
                    with open("result.csv", "a") as csvfile:
                        csvfile.write(",")
                    os.rename("Script.txt", f"Script{n}.txt")

        else:
            # If Metrics.xml is missing, mark it as "crash"
            with open("result.csv", "a") as csvfile:
                csvfile.write(f"\n{i},crash,crash,crash,crash,crash,crash,")

        # Save output results
        OUTPUT_PATH = f"Data\\{foldername}\\Range_{j}\\Output_{i}"
        #OUTPUT_PATH = f"Data\\{foldername}\\Output_{i}"
        os.makedirs(OUTPUT_PATH, exist_ok=True)

        if os.path.isfile("result.csv"):
            shutil.copy("result.csv", f"Data\\{foldername}")

        for file_name in os.listdir("IOPath"):
            shutil.move(os.path.join("IOPath", file_name), OUTPUT_PATH)

        # Safe deletion with retry for locked Metrics.xml
        for filename in ["Configuration.netsim", "Metrics.xml"]:
            if os.path.isfile(filename):
                for _ in range(5):  # Retry up to 5 times
                    try:
                        os.remove(filename)
                        break
                    except PermissionError:
                        print(f"File {filename} is locked, retrying in 2 seconds...")
                        time.sleep(2)
