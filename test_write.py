import os
print(f"Current directory: {os.getcwd()}")
print(f"Writing test file...")

filepath = r"D:\git\1108\AI_ad_spend02\testfile_marker.txt"
with open(filepath, "w") as f:
    f.write("Test successful\n")

print(f"File written to: {filepath}")
print(f"File exists: {os.path.exists(filepath)}")
