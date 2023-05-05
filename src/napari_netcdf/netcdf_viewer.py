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

    def __init__(self, path, layers, x_dim=None, y_dim=None):
        """
        Create a Viewer object to manage the loading of data into napari

        :param path: path to the scene
        :param layers: a list of strings controlling which layers to display.
        :param x_dim: the dimension to use along the x-dimension (prefix with - to flip)
        :param y_dim: the dimension to use along the y-dimension (prefix with - to flip)

        """
        self.scene_path = path
        self.layers = layers
        self.viewer = napari.Viewer()
        self.x_dim = x_dim
        self.x_flip = False
        self.y_dim = y_dim
        self.y_flip = False

        if self.x_dim and self.x_dim.startswith("-"):
            self.x_dim = self.x_dim[1:]
            self.x_flip = True

        if self.y_dim and self.y_dim.startswith("-"):
            self.y_dim = self.y_dim[1:]
            self.y_flip = True

        self.ds = xr.open_dataset(self.scene_path)

    def __get_array(self,variable_name):
        da = self.ds[variable_name].squeeze()
        if len(da.shape) != 2:
            raise ValueError(f"{variable_name} should not have more than two dimensions with size > 1")
        # arrange the data so that the y-axis is the first dimension, x-axis is the second
        if self.y_dim:
            if self.x_dim:
                da = da.transpose(self.y_dim, self.x_dim)
            else:
                da = da.transpose(self.y_dim, ...)
        else:
            if self.x_dim:
                da = da.transpose(..., self.x_dim)
        data = da.data

        # flip the x- or y-axis as instructed

        if self.y_flip:
            data = np.flipud(data)
        if self.x_flip:
            data = np.fliplr(data)
        return data

    def add_image_layer(self, layer):
        """
        Add a single channel or rgb of 3 channels as an image layer
        :param variable: the variable name and optionally other information, notation name[:min:max[:colourmap]] or rgb(name:name:name)
        """
        if layer.startswith("rgb("):
            rgb_channels = layer[4:-1].split(":")
            rgb_arrays = []
            for channel in rgb_channels:
                rgb_arrays.append(self.__get_array(channel))
            data = np.stack(rgb_arrays,axis=-1)
            self.viewer.add_image(data, name=layer, rgb=True)
        else:
            variable_parts = layer.split(":")
            variable_name = variable_parts[0]
            scale = None
            cmap = "viridis"
            if len(variable_parts) > 2:
                scale = (float(variable_parts[1]),float(variable_parts[2]))
            if len(variable_parts) > 3:
                cmap = variable_parts[3]
            data = self.__get_array(variable_name)
            self.viewer.add_image(data, name=variable_name, colormap=cmap,contrast_limits=scale)

    def open(self):
        """
        Open the SLSTR scene files and display in napari
        """
        added_ok = 0
        for layer in self.layers:

            print(f"Adding layer {layer}", end="")
            try:
                self.add_image_layer(layer)
                print(f"[Done]")
                added_ok += 1
            except Exception as ex:
                print(f"[Failed] {ex}")

        if added_ok > 0:
            napari.run()



def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to a netcdf file to display")
    parser.add_argument("variables", help="Specify the variables to display as a comma separated list"+
                        " where variables are specified using notation:  name[:min:max[:colourmap]]")
    parser.add_argument("--x-dim", help="Specify the x-dimension to use (defaults to second dimension)")
    parser.add_argument("--y-dim", help="Specify the y-dimension to use (defaults to first dimension)")

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()
    filepath = args.path
    vars = args.variables.split(",")

    viewer = Viewer(filepath, vars, x_dim=args.x_dim, y_dim=args.y_dim)

    try:
        viewer.open() # exits when the user closes the napari window
    except Exception as ex:
        logging.exception("Error when opening napari")


if __name__ == '__main__':
    main()
