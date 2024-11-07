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
import os.path

import napari
import xarray as xr
import numpy as np
import logging
import sys

class Viewer:

    def __init__(self, path_layers, x_dim=None, y_dim=None):
        """
        Create a Viewer object to manage the loading of data into napari

        :param path_layers: map from path to a list of strings controlling which layers to display from that file
        :param x_dim: the dimension to use along the x-dimension (prefix with - to flip)
        :param y_dim: the dimension to use along the y-dimension (prefix with - to flip)

        """
        self.path_layers = path_layers
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


    def __get_arrays(self,variable_name, path, allow_extra_dim=False):
        ds = xr.open_dataset(path)
        da = ds[variable_name].squeeze()

        extra_dim = ""
        extra_dim_size = 1

        for idx in range(len(da.dims)):
            dim = da.dims[idx]
            if dim != self.y_dim and dim != self.x_dim:
                if allow_extra_dim == False:
                    raise ValueError(
                        f"Cannot handle non-unit extra dimension, found {dim}.")
                if extra_dim:
                    raise ValueError(f"Cannot handle more than one non-unit extra dimension, found {dim} and {extra_dim}")
                extra_dim = dim
                extra_dim_size = da.shape[idx]

        arrays = []
        for extra_dim_index in range(extra_dim_size):

            if extra_dim:
                da1 = da.isel(**{extra_dim:extra_dim_index})
                label = variable_name+ f"[{extra_dim}={extra_dim_index}]"
            else:
                da1 = da
                label = variable_name

            # arrange the data so that the y-axis is the first dimension, x-axis is the second
            da1 = da1.transpose(self.y_dim, self.x_dim)

            data = da1.data

            # flip the x- or y-axis as instructed

            if self.y_flip:
                data = np.flipud(data)
            if self.x_flip:
                data = np.fliplr(data)
            arrays.append((label,data))
        return arrays

    def add_image_layer(self, layer, path):
        """
        Add a single channel or rgb of 3 channels as an image layer
        :param variable: the variable name and optionally other information, notation name[:min:max[:colourmap]] or rgb(name:name:name)
        """
        layer_name = layer
        if layer.startswith("rgb("):
            rgb_channels = layer[4:-1].split(":")
            rgb_arrays = []
            for channel in rgb_channels:
                arrays = self.__get_arrays(channel,path,False)
                (label, array) = arrays[0]
                rgb_arrays.append(array)
            data = np.stack(rgb_arrays,axis=-1)
            self.viewer.add_image(data, name=layer_name, rgb=True)
        else:
            variable_parts = layer.split(":")
            variable_name = variable_parts[0]
            scale = None
            cmap = "viridis"
            if len(variable_parts) > 2:
                scale = (float(variable_parts[1]),float(variable_parts[2]))
            if len(variable_parts) > 3:
                cmap = variable_parts[3]
            arrays = self.__get_arrays(variable_name, path, True)
            for (label, data) in arrays:
                self.viewer.add_image(data, name=label, colormap=cmap,contrast_limits=scale)

    def open(self):
        """
        Open the SLSTR scene files and display in napari
        """
        added_ok = 0
        for path in self.path_layers:
            fname = os.path.split(path)[1]
            for layer in self.path_layers[path]:
                print(f"Adding layer {layer}/{fname}", end="")
                try:
                    self.add_image_layer(layer, path)
                    print(f"[Done]")
                    added_ok += 1
                except Exception as ex:
                    print(f"[Failed] {ex}")

        if added_ok > 0:
            napari.run()



def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path_layers", nargs="+", help="path to a netcdf file(s) to display followed by layer_specifications where layers are specified using notation:  name[:min:max[:colourmap]] or rgb(name:name:name)")

    parser.add_argument("--x-dim", help="Specify the x-dimension to use", default="x")
    parser.add_argument("--y-dim", help="Specify the y-dimension to use", default="y")

    logging.basicConfig(level=logging.INFO)

    layers = {}
    path = None
    args = parser.parse_args()
    for path_layer in args.path_layers:
        if path_layer.endswith(".nc"):
            path = path_layer
            layers[path] = []
        else:
            if path is not None:
                layers[path].append(path_layer)
            else:
                print("Invalid arguments"
                      "")
                sys.exit(-1)


    viewer = Viewer(layers, x_dim=args.x_dim, y_dim=args.y_dim)

    try:
        viewer.open() # exits when the user closes the napari window
    except Exception as ex:
        logging.exception("Error when opening napari")


if __name__ == '__main__':
    main()
