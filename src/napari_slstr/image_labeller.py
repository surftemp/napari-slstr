import napari
import xarray as xr
import numpy as np
import os.path
import sys

try:
    import tomllib
except ModuleNotFoundError:
    # python < 3.11
    import tomli as tomllib

DEFAULT_BANDS="S1,S2,S3,S4,S5,S6,S7,S8,S9,FalseColour:S3:S2:S1"

OBLIQUE_OFFSET_RADIANCE = 1096 # 0.5km/trackOffset/nadir=1996 - 0.5km/trackOffset/oblique=900
OBLIQUE_OFFSET_BT = 548        # 1km/trackOffset/nadir=998 - 1km/trackOffset/oblique=450

class SceneLabeler:

    def __init__(self, scene_path, label_layers=None):
        self.scene_path = scene_path
        self.viewer = napari.Viewer()
        self.data_dims = ("rows","columns")
        self.data_shape = (1200,1500)

        self.masks = {} # populated on open
        self.label_layers = label_layers

    def coarsen(self,da):
        return da.coarsen(rows=2,columns=2).mean()

    def add_image_layer(self,channel,name='',cmap="viridis"):
        coarsen = False
        pad = False
        if "radiance" in channel:
            coarsen = True
        if channel.endswith("o"):
            pad = True

        if not name:
            name = channel
        ds = xr.open_dataset(os.path.join(self.scene_path,channel + ".nc"))
        da = ds[channel].squeeze()
        if pad:
            if coarsen:
                data = np.zeros(shape=(2400, 3000))
                data[:, :] = np.nan
                data[:,OBLIQUE_OFFSET_RADIANCE:OBLIQUE_OFFSET_RADIANCE+1800] = da.data
                da = xr.DataArray(data,dims=("rows","columns"))
            else:
                data = np.zeros(shape=(1200,1500))
                data[:, :] = np.nan
                data[:, OBLIQUE_OFFSET_BT:OBLIQUE_OFFSET_BT + 900] = da.data
                da = xr.DataArray(data, dims=("rows", "columns"))

        if coarsen:
            da = self.coarsen(da)

        if da.data.shape != self.data_shape:
            raise TypeError(f"Data for channel {channel} has incompatible shape: {da.data.shape} should be {self.data_shape}")

        self.viewer.add_image(da.data, name=name, colormap=cmap)

    def add_rgb_layer(self,name,red_channel,green_channel,blue_channel,coarsen=True):
        rgb_arrays = []
        for channel in [red_channel,green_channel,blue_channel]:
            ds = xr.open_dataset(os.path.join(self.scene_path, channel + ".nc"))
            da = ds[channel].squeeze()
            if coarsen:
                da = self.coarsen(da)
            max_radiance = np.nanmax(da.data)
            da = da / max_radiance
            rgb_arrays.append(da)

        rgb_data = xr.concat(rgb_arrays,"rgb")
        rgb_data = rgb_data.transpose(*rgb_data.dims[1:]+rgb_data.dims[0:1])
        self.viewer.add_image(rgb_data.data,name=name,rgb=True)

    def open(self, bands, use_oblique_view=True, radiance_colourmap="", bt_colourmap=""):
        for band in bands:
            if band in ["S7","S8","S9"]:
                if radiance_colourmap:
                    self.add_image_layer(f"{band}_BT_in", cmap=bt_colourmap)
                    if use_oblique_view:
                        self.add_image_layer(f"{band}_BT_io", cmap=bt_colourmap)
            elif band in ["S1", "S2", "S3", "S4", "S5", "S6"]:
                if bt_colourmap:
                    self.add_image_layer(f"{band}_radiance_an", cmap=radiance_colourmap)
                    if use_oblique_view:
                        self.add_image_layer(f"{band}_radiance_ao", cmap=radiance_colourmap)
            elif band.startswith("FalseColour"):
                fc_bands = list(map(lambda b:b.strip(),band.split(":")))[1:]
                if len(fc_bands) != 3:
                    print("Please specify three FalseColour bands, for example FalseColour:S3:S2:S1")
                    sys.exit(-1)
                for fc_band in fc_bands:
                    if fc_band not in ["S1","S2","S3","S4","S5","S6"]:
                        print(f"Invalid FalseColour band {fc_band}, should be one of S1,S2,S3,S4,S5,S6")
                self.add_rgb_layer("False Colour S3/S2/S1 RGB", *list(map(lambda b: b+"_radiance_an",fc_bands)))
            else:
                print(f"Ignoring unknown band {band}.")
                sys.exit(-1)

        if self.label_layers:
            for name in self.label_layers:
                label_layer = self.label_layers[name]
                filename = label_layer["filename"]
                colour = label_layer["colour"]
                path = os.path.join(self.scene_path,filename)
                if os.path.exists(path):
                    self.masks[name] = xr.open_dataarray(path)
                else:
                    self.masks[name] = xr.DataArray(data=np.zeros(dtype=int,shape=self.data_shape),dims=self.data_dims)
                layer_name = "Label-"+name+"("+colour+")"
                self.viewer.add_labels(self.masks[name].data, name=layer_name, num_colors=1, color={1:colour})
        napari.run()

    def save(self):
        if self.label_layers:
            for name in self.label_layers:
                label_layer = self.label_layers[name]
                filename = label_layer["filename"]
                path = os.path.join(self.scene_path,filename)
                self.masks[name].close()
                self.masks[name].to_netcdf(path)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("scene_path", help="path to an SLSTR scene to label")
    parser.add_argument("--label-layers-path", help="Specify the path to a file configuring label layers")
    parser.add_argument("--bands", help="specify a comma separated list of bands to visualise, defaults to all bands."
                        "To specify a false colour band, use FalseColour:SX:SY:SZ", default=DEFAULT_BANDS)
    parser.add_argument("--no-oblique", help="Only show nadir views, not oblique ones", action="store_true")
    parser.add_argument("--radiance-colourmap", help="Colourmap for radiance channels.  "
                        "Set to blank to suppress all radiance channels", default="viridis")
    parser.add_argument("--bt-colourmap", help="Colourmap for BT channels. " 
                        "Set to blank to suppress all BT channels", default="magma")

    args = parser.parse_args()

    label_layers = None
    if args.label_layers_path:
        with open(args.label_layers_path) as f:
            label_layers = tomllib.loads(f.read())

    labeler = SceneLabeler(args.scene_path,label_layers=label_layers)
    bands = map(lambda b:b.strip(),args.bands.split(","))
    labeler.open(bands, use_oblique_view=not args.no_oblique,
                 radiance_colourmap=args.radiance_colourmap, bt_colourmap=args.bt_colourmap)
    labeler.save()

if __name__ == '__main__':
    main()