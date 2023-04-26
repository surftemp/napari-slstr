# MIT License
#
# Copyright (c) 2023 surftemp
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import napari
import xarray as xr
import numpy as np
import logging

class Viewer:

    def __init__(self, path, variables):
        """
        Create a Viewer object to manage the loading of data into napari

        :param path: path to the scene
        :param variables: a dictionary controlling which variables to display.

        """
        self.scene_path = path
        self.variables = variables
        self.viewer = napari.Viewer()
        self.layers = variables
        self.ds = xr.open_dataset(self.scene_path)


    def add_image_layer(self, variable, name, cmap="viridis"):
        """
        Add a single channel as an image layer
        :param variable: the name of the variable
        :param name: the name to give the layer in napari
        :param cmap: the name of the napart colour map to use, eg magma, viridis
        """
        da = self.ds[variable].squeeze()

        self.viewer.add_image(np.flipud(da.data), name=name, colormap=cmap)

    def open(self):
        """
        Open the SLSTR scene files and display in napari
        """
        for variable in self.layers:

            print(f"Adding layer {variable}", end="")
            self.add_image_layer(variable, variable)

            print(f"[Done]")

        napari.run()



def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to a netcdf file to display")
    parser.add_argument("variables", help="Specify the variables to display as a comma separated list")

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()
    filepath = args.path
    vars = args.variables.split(",")

    viewer = Viewer(filepath, vars)

    try:
        viewer.open() # exits when the user closes the napari window
    except Exception as ex:
        logging.exception("Error when opening napari")


if __name__ == '__main__':
    main()
