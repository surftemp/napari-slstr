import napari
import xarray as xr
import numpy as np
import os.path

OBLIQUE_OFFSET_RADIANCE = 1096 # trackOffset/nadir=1996 - trackOffset/oblique=900
OBLIQUE_OFFSET_BT = 448        # trackOffset/nadir=998 - trackOffset/oblique=450

label_layers = {
    "Cloud": ( "cloud_labels.nc","white"),
    "Ice": ( "ice_labels.nc","lightblue"),
    "Clear": ( "clear_labels.nc","black")
}

class SceneLabeler:

    def __init__(self, scene_path):
        self.scene_path = scene_path
        self.viewer = napari.Viewer()
        self.data_dims = ("rows","columns")
        self.data_shape = (1200,1500)

        self.masks = {} # populated on open

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

    def open(self):
        self.add_image_layer("S9_BT_in", cmap="magma")
        self.add_image_layer("S9_BT_io", cmap="magma")
        self.add_image_layer("S8_BT_in", cmap="magma")
        self.add_image_layer("S7_BT_in",cmap="magma")
        self.add_image_layer("S6_radiance_an")
        self.add_image_layer("S6_radiance_ao")
        self.add_image_layer("S5_radiance_an")
        self.add_image_layer("S5_radiance_ao")
        self.add_image_layer("S4_radiance_an")
        self.add_image_layer("S4_radiance_ao")
        self.add_image_layer("S3_radiance_an")
        self.add_image_layer("S3_radiance_ao")
        self.add_image_layer("S2_radiance_an")
        self.add_image_layer("S1_radiance_ao")
        self.add_image_layer("S1_radiance_an")
        self.add_rgb_layer("S3/S2/S1 RGB", "S3_radiance_an","S2_radiance_an","S1_radiance_an")

        for name in label_layers:
            (filename,colour) = label_layers[name]
            path = os.path.join(self.scene_path,filename)
            if os.path.exists(path):
                self.masks[name] = xr.open_dataarray(path)
            else:
                self.masks[name] = xr.DataArray(data=np.zeros(dtype=int,shape=self.data_shape),dims=self.data_dims)
            layer_name = "Label-"+name+"("+colour+")"
            self.viewer.add_labels(self.masks[name].data, name=layer_name, num_colors=1, color={1:colour})
        napari.run()

    def save(self):
        for name in label_layers:
            (filename,colour) = label_layers[name]
            path = os.path.join(self.scene_path,filename)
            self.masks[name].close()
            self.masks[name].to_netcdf(path)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("scene_path",help="path to an SLSTR scene to label")
    args = parser.parse_args()

    labeler = SceneLabeler(args.scene_path)
    labeler.open()
    labeler.save()

if __name__ == '__main__':
    main()