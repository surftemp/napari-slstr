# napari-slstr

This repo provides tools for using `napari` to work with remote sensing data files:

* image_labeller: Launch the napari image viewer/labelling tool on an Sentinel 3 / SLSTR scene or slsitr-lite scene
* netcdf_viewer: Launch napari to view 2D gridded data from any netcdf4 file

For more information on napari see: [https://napari.org/](https://napari.org/)

## Installation Prerequisites

* conda or miniconda (recommended)
* git
* Napari
  * On Mac, ensure you have XCode installed.

## Installation

### Installing napari and its dependencies

Install napari, preferably into a new conda environment (see https://napari.org/stable/tutorials/fundamentals/installation.html for instructions for your platform)

Important Note - this software has been tested with napari versions 0.4.18 and 0.5.3 on linux.  You can install a specific version of napari using the following example syntax `python -m pip install "napari[all]==0.4.18"`

Check the version of napari that has been installed

```
$ napari --version
napari version 0.5.3
```

### Installing image_labeller and netcdf_viewer

Create a new folder and clone this repo into it

```
mkdir napari_slstr_install
cd napari_slstr_install
git clone https://github.com/surftemp/napari-slstr.git
```

Install napari-slstr `image_labeller` and `netcdf_viewer` commands from the repo:

```
cd napari-slstr
pip install -e .
```

Check that the `image_labeller` tool will open, requires an unzipped Sentinel3 SLSTR scene, eg

```
image_labeller ~/Projects/napari/S3A_SL_1_RBT____20170122T094902_20170122T095202_20181004T064548_0179_013_264______LR1_R_NT_003.SEN3 ./resources/example.cfg
```

![napari](https://user-images.githubusercontent.com/58978249/220682442-4c52e903-8409-4888-a36c-d14fd1062e9d.png)


## Install updates

To install updates to the `image_labeller` and `netcdf_viewer` tools:

```
cd napari_slstr_install
git pull
```

## Using image_labeller

### Defaults

In the `resources/example.cfg` configuration file, all channels are shown, with nadir and oblique views, plus a false colour view constructed from bands S3 (red), S2(green) and S1(blue).

```
image_labeller <path-to-SLSTR-scene-folder> ./resources/example.cfg
```

When viewing an slstr-lite scene, use configuration file (or one based on) `./resources/example_slstr_lite.cfg`

updated label files are written into the scene folder when the user closes Napari (select Exit from the File menu).

It is recommended to periodically back up label files.

## Using netcdf_viewer

The netcdf_viewer tool uses command line options to control which files and variables are to be displayed, and how to display them.  For example:

```
netcdf_viewer.py [-h] [--x-dim X_DIM] [--y-dim Y_DIM] path layer [layer...] 
```

```
netcdf_viewer LC08_L1TP_205025_20230420_20230429_02_T1.nc rgb(B4:B3:B2) B11:275:295:coolwarm --y-dim=nj
```

* the netcdf file is `LC08_L1TP_205025_20230420_20230429_02_T1.nc`
* two layers are requested:
  * the first layer is a rgb false colour composed from r=B4,g=B3,b=B2
  * the second layer displays B11 using the coolwarm colour map between 275K and 295K
* use dimension nj as the y axis

### Viewing multiple files

Specify multiple paths and their layers using:

```
netcdf_viewer.py [-h] [--x-dim X_DIM] [--y-dim Y_DIM] path layer [layer...] path layer [layer...]
```

### Notes

`--x-dim` and `--y-dim` specify the data dimensions to display on x and y axes.  Prefix the dimension name with a minus sign to flip the axes.

Layers are specified using the following (hopefully self-explanatory) notation:

Use `rgb(r-var-name:g-var-name:b-var-name)` to specify 3 bands to compose a false colour layer

or

Use `var-name[:min-value:max-value[:colour-map]]` to plot a single band, with optional min/max and colour map.  

The following colour maps are available:

"GrBu", "GrBu_d", "PiYG", "PuGr", "RdBu", "RdYeBuCy", "autumn", "blues", "cool", "coolwarm", "cubehelix", "diverging", "fire", "gist_earth", "gray", "gray_r", "grays", "greens", "hot", "hsl", "hsv", "husl", "ice", "inferno", "light_blues", "magma", "orange", "plasma", "reds", "single_hue", "spring", "summer", "turbo", "twilight", "twilight_shifted", "viridis", "winter"

