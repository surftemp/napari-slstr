# napari-slstr

Launch the napari image viewer/labelling tool on an Sentinel 3 / SLSTR scene

For more information on napari see: [https://napari.org/](https://napari.org/)



## Installation Prerequisites

* conda or miniconda
* git

## Installation

Set up a conda environment with python 3.9

```
conda create -y -n napari-env -c conda-forge python=3.9
conda activate napari-env
```

Clone this repo

```
cd /parent/directory/for/cloned/repo
git clone git@github.com:surftemp/napari-slstr.git
```

Install napari-slstr `image_labeller` command, napari and other dependencies:

```
cd /parent/directory/for/cloned/repo/napari-slstr
pip install -e .
```

Check that the tool will open, requires an unzipped Sentinel3 SLSTR scene, eg

```
image_labeller ~/Projects/napari/S3A_SL_1_RBT____20170122T094902_20170122T095202_20181004T064548_0179_013_264______LR1_R_NT_003.SEN3
```

![napari](https://user-images.githubusercontent.com/58978249/220682442-4c52e903-8409-4888-a36c-d14fd1062e9d.png)


## Install updates

To install updates to the `image_labelling` tool:

```
cd /parent/directory/for/cloned/repo/napari-slstr
git pull
```

## Using

### Defaults

By Default all channels are shown, with nadir and oblique views, plus a false colour view constructed from bands S3 (red), S2(green) and S1(blue).

```
image_labeller <path-to-SLSTR-scene-folder> 
```

### Specifying label layers

Label layers allow a scene to be annotated on a pixel-by-pixel basis.  

To enable this, create a configuration file - see [resources/example_label_layers.cfg](resources/example_label_layers.cfg) for an example - and pass its path using the `--label-layers-path` option:

```
image_labeller --label-layers-path=resources/example_label_layers.cfg
```

### Selecting bands

To display only bands S4,S5 and S6:

```
image_labeller --bands "S4,S5,S6"
```

To display only bands S4, S5 and S6 plus a FalseColour band based on these bands:

```
image_labeller --bands "S4,S5,S6,FalseColour:S4:S5:S6"
```

Note that the order in which bands are listed determines the order of the layers in Napari.  Later bands are mapped to higher layers.

### Turning off the oblique view

By default, each band creates two layers, nadir and oblique.  The oblique view is narrower.  To disable the oblique views specify the `--no-oblique` option

```
image_labeller --no-oblique
```

### Configuring the default colour maps

By default, the viridis colour map will be used for radiance bands and the magma colour map will be used for BT bands

To change this, use the `--radiance-colourmap` and `--bt-colourmap` options:

```
image_labeller --bt-colourmap=hsv --radiance-colourmap=turbo
```

...where the colourmap names can be listed in the napari UI 

