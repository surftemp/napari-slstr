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
import threading

import napari
import xarray as xr
import numpy as np
import os.path
import logging
import time

try:
    import tomllib
except ModuleNotFoundError:
    # python < 3.11
    import tomli as tomllib

# work out offsets for superimposing the narrow oblique grid on the wider nadir grid
# TODO shout this be calculated from each scene's manifest file?
OBLIQUE_OFFSET_RADIANCE = 1096  # 0.5km/trackOffset/nadir=1996 - 0.5km/trackOffset/oblique=900
OBLIQUE_OFFSET_BT = 548  # 1km/trackOffset/nadir=998 - 1km/trackOffset/oblique=450


class SceneLabeler:

    def __init__(self, scene_path, layers):
        """
        Create a SceneLabeller object to manage the loading of data into and saving of label data out of napari,
        given an SLSTR scene L1C
        :param scene_path: path to the scene
        :param layers: a dictionary controlling which layers to load, with layer names as keys and layer settings as values.

        Loaded from the configuration file.  See comments in resources/example.cfg
        """
        self.scene_path = scene_path
        self.viewer = napari.Viewer()
        # record the expected dimensions and shape for the 1km nadir grid
        self.data_dims = ("rows", "columns")
        self.data_shape = (1200, 1500)
        self.masks = {}  # populated on open
        self.layers = layers

    def coarsen(self, da, aggregate):
        """
        Convert an array from the 0.5km to the 1km grid, using the specified aggregation method on each group of 4 pixels to be merged
        :param da: an xarray.DataArray object containing 0.5km grid
        :param aggregate: the aggregate function to apply, either "mean" or "sdev"
        :return: an xarray.DataArray object containing aggregated data on the 1km grid
        """

        if aggregate == "mean":
            return da.coarsen(rows=2, columns=2).mean()
        elif aggregate == "sdev":
            return da.coarsen(rows=2, columns=2).std()
        else:
            raise ValueError(f'Invalid aggregate name {aggregate} should be either "mean" or "sdev"')

    def add_image_layer(self, channel, variable, name, cmap="viridis", aggregate="mean"):
        """
        Add a single channel as an image layer
        :param channel: filename, without the .nc suffix eg. S3_radiance_an, S8_BT_in etc
        :param variable: the name of the variable inside the channel file
        :param name: the name to give the layer in napari
        :param cmap: the name of the napart colour map to use, eg magma, viridis
        :param aggregate: an aggregate function to use if the data needs to be aggregated to the 1km grid
        """
        channel_path = os.path.join(self.scene_path, channel + ".nc")
        if not os.path.exists(channel_path):
            raise FileNotFoundError(channel_path)

        # channel should be named
        # SN_(radiance|BT)_(a|b|i)(n|o)
        oblique = channel.endswith("o")

        ds = xr.open_dataset(channel_path)
        da = ds[variable].squeeze()
        if oblique:
            if da.data.shape == (2400, 1800):
                # 500m grid
                data = np.zeros(shape=(2400, 3000))
                data[:, :] = np.nan
                data[:, OBLIQUE_OFFSET_RADIANCE:OBLIQUE_OFFSET_RADIANCE + 1800] = da.data
                da = xr.DataArray(data, dims=("rows", "columns"))
            else:
                # 1km grid
                data = np.zeros(shape=(1200, 1500))
                data[:, :] = np.nan
                data[:, OBLIQUE_OFFSET_BT:OBLIQUE_OFFSET_BT + 900] = da.data
                da = xr.DataArray(data, dims=("rows", "columns"))

        if da.data.shape == (2400, 3000):
            da = self.coarsen(da, aggregate)

        if da.data.shape != self.data_shape:
            raise TypeError(
                f"Data for channel {channel} has incompatible shape: {da.data.shape} should be {self.data_shape}")

        self.viewer.add_image(da.data, name=name, colormap=cmap)

    def add_rgb_layer(self, name, rgb_channels, rgb_variables, aggregate="mean"):
        """
        Add a set of 3 channels to form a FalseColour RGB layer
        :param name: the name of the layer to display in napari
        :param rgb_channels: a list of three channel names, [red-channel,green-channel,blue-channel] each channel is the filename without .nc suffix
        :param rgb_variables: a list of three variable names, [red-channel,green-channel,blue-channel] to load from each channel
        :param aggregate: an aggregate function to use if the data needs to be aggregated to the 1km grid
        """
        rgb_arrays = []
        for idx in range(3):
            channel = rgb_channels[idx]
            channel_path = os.path.join(self.scene_path, channel + ".nc")
            if not os.path.exists(channel_path):
                raise FileNotFoundError(channel_path)

            variable = rgb_variables[idx]
            ds = xr.open_dataset(os.path.join(self.scene_path, channel + ".nc"))
            da = ds[variable].squeeze()
            if da.data.shape == (2400, 3000):
                da = self.coarsen(da, aggregate)
            max_radiance = np.nanmax(da.data)
            da = da / max_radiance

            if da.data.shape != self.data_shape:
                raise TypeError(
                    f"Data for channel {channel} has incompatible shape: {da.data.shape} should be {self.data_shape}")

            rgb_arrays.append(da)

        rgb_data = xr.concat(rgb_arrays, "rgb")
        rgb_data = rgb_data.transpose(*rgb_data.dims[1:] + rgb_data.dims[0:1])
        self.viewer.add_image(rgb_data.data, name=name, rgb=True)

    def open(self):
        """
        Open the SLSTR scene files and display in napari
        """
        for (layer_name, layer) in self.layers.items():

            layer_type = layer["type"]
            enabled = layer.get("enabled", True)
            if enabled:
                print(f"Adding layer {layer_name}:{layer_type} ... ", end="")
            else:
                continue

            try:
                if layer_type == "image":
                    colourmap = layer["colourmap"]
                    filename = layer["filename"]
                    filename_root = os.path.splitext(filename)[0]
                    aggregate = layer.get("aggregate", "mean")
                    variable = layer.get("variable", filename_root)
                    self.add_image_layer(filename_root, variable, layer_name, cmap=colourmap, aggregate=aggregate)

                elif layer_type == "rgb_image":
                    red_filename = layer["red_filename"]
                    green_filename = layer["green_filename"]
                    blue_filename = layer["blue_filename"]
                    root_filenames = [os.path.splitext(filename)[0] for filename in
                                      [red_filename, green_filename, blue_filename]]
                    red_variable = layer.get("red_variable", root_filenames[0])
                    green_variable = layer.get("green_variable", root_filenames[1])
                    blue_variable = layer.get("blue_variable", root_filenames[2])
                    aggregate = layer.get("aggregate", "mean")
                    self.add_rgb_layer(layer_name, rgb_channels=root_filenames,
                                       rgb_variables=[red_variable, green_variable, blue_variable], aggregate=aggregate)

                elif layer_type == "label":
                    colour = layer["colour"]
                    filename = layer["filename"]
                    path = os.path.join(self.scene_path, filename)
                    if os.path.exists(path):
                        da = xr.open_dataarray(path)
                        self.masks[layer_name] = da
                        da.close()
                    else:
                        self.masks[layer_name] = xr.DataArray(data=np.zeros(dtype=int, shape=self.data_shape),
                                dims=self.data_dims, name=layer_name, attrs={"description":"mask for label: "+layer_name})
                    self.viewer.add_labels(self.masks[layer_name].data, name=layer_name + " (" + colour + ")",
                                           num_colors=1, color={1: colour})

                else:
                    raise ValueError(f"Unknown layer type {layer_type}")
                print(f"[Done]")
            except Exception as ex:
                print("[Failed]")
                logging.exception(f"Failed to add layer {layer_name}:{layer_type}")

        napari.run()

    def save(self):
        """
        Save the labels data to files
        """
        for (layer_name, layer) in self.layers.items():
            if layer["type"] == "label":
                filename = layer["filename"]
                path = os.path.join(self.scene_path, filename)
                print(f"Saving labels from {layer_name} to {path}... ", end="")
                try:
                    self.masks[layer_name].to_netcdf(path)
                    print("[Done]")
                except Exception as ex:
                    print("[Failed]")
                    logging.exception("Failed to write labels file")

    def close(self):
        self.save()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("scene_path", help="path to an SLSTR scene to label")
    parser.add_argument("cfg_path", help="Specify the path to a file configuring label layers")

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()

    # load the configuration defining each layer to display
    with open(args.cfg_path) as f:
        layers = tomllib.loads(f.read())

    labeler = SceneLabeler(args.scene_path, layers)

    # load and open the layers.  catch exceptions and try to save updated labels
    try:
        labeler.open() # exits when the user closes the napari window
    except Exception as ex:
        logging.exception("Error when opening napari")
    labeler.close() # save labels back to file


if __name__ == '__main__':
    main()
