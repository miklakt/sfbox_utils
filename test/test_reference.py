#%%
# usualy it is what we need
# comment if working directory is different from script directory
import sys, os
os.chdir(sys.path[0])

import pandas as pd
import matplotlib.pyplot as plt

#make sure you import sfbox_utils to expand pandas DataFrame methods
import sfbox_utils

reference_tbl = pd.read_pickle("test_sfbox_reference.pkl")
phi_arr = reference_tbl.iloc[0].dataset["phi"].squeeze()

fig, ax = plt.subplots()
im = ax.imshow(phi_arr, origin="lower")
ax.set_xlabel("z")
ax.set_ylabel("x")
cbar = plt.colorbar(im, orientation = "horizontal")
cbar.set_label("$\phi$")
ax.set_title("Polymer brush volume density profile")
