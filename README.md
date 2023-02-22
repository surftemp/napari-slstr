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

## Install updates

To install updates to the `image_labelling` tool:

```
cd /parent/directory/for/cloned/repo/napari-slstr
git pull
```