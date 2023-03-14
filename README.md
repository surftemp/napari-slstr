# napari-slstr

Launch the napari image viewer/labelling tool on an Sentinel 3 / SLSTR scene

For more information on napari see: [https://napari.org/](https://napari.org/)



## Installation Prerequisites

* conda or miniconda
* git

## Installation

On Mac, ensure you have XCode installed.

Set up a conda environment with python 3.9

```
conda create -y -n napari-env python=3.9
conda activate napari-env
```

Create a new folder and clone this repo into it

```
mkdir napari_slstr_install
cd napari_slstr_install
git clone git@github.com:surftemp/napari-slstr.git
```

Install napari-slstr `image_labeller` command, napari and other dependencies:

```
pip install -e .
```

Check that the tool will open, requires an unzipped Sentinel3 SLSTR scene, eg

```
image_labeller ~/Projects/napari/S3A_SL_1_RBT____20170122T094902_20170122T095202_20181004T064548_0179_013_264______LR1_R_NT_003.SEN3 ./resources/example.cfg
```

![napari](https://user-images.githubusercontent.com/58978249/220682442-4c52e903-8409-4888-a36c-d14fd1062e9d.png)


## Install updates

To install updates to the `image_labelling` tool:

```
cd napari_slstr_install
git pull
```

## Using

### Defaults

By Default all channels are shown, with nadir and oblique views, plus a false colour view constructed from bands S3 (red), S2 (green) and S1 (blue).

```
image_labeller <path-to-SLSTR-scene-folder> <path-to-napari-slstr-cfg>
```



