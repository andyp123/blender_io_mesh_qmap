# Quake MAP File Importer for Blender

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=S3GTZ2J938U6Y&lc=GB&item_name=Andrew%20Palmer&currency_code=GBP&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)

An add-on for [Blender](https://www.blender.org/) that makes it possible to import
Quake MAP files, which are used by Quake level editors such as Trenchbroom to define
the level geometry using convex volumes known as brushes. These volumes can be
imported into Blender and used for convex collision meshes for other game engines.

__Note:__ You will need Blender 2.80 or above (tested up to 3.3 alpha) to use this add-on.
Get the latest version of Blender [here](https://www.blender.org).

![Imported level (apdm3)](https://raw.githubusercontent.com/andyp123/blender_io_mesh_qmap/master/README_img/map_importer_apdm3.PNG)

## Installation
1. Download the latest release from GitHub by clicking [here](https://github.com/andyp123/blender_io_mesh_qmap/releases).
2. In Blender, open Preferences (Edit > Preferences) and switch to the Add-ons section.
3. Select 'Install Add-on from file...' and select the file that you downloaded.
4. Search for the add-on in the list (enter 'map' to quickly find it) and enable it.
5. Save the preferences if you would like the script to always be enabled.

## Usage
Once the add-on has been installed, you will be able to import Quake MAP files from
File > Import > Quake MAP (.map). Selecting this option will open the file browser
and allow you to select a file to load. Before loading the file, you can tweak some
options to change how the MAP will be imported into Blender.

### Scale (default: 0.03125)
Changes the size of the imported geometry. The size of a unit in Quake is not the
same as in Blender. Scale is set so that 32 units in Quake is 1m in Blender, so setting
scale to 1 will make everything huge.

### Worldspawn Only (default: Off)
Worldspawn is the name given to the entity representing the world in Quake. It is
always the very first entity defined in a MAP or BSP file. If this option is enabled
only the first entity will be imported.

### Group Entities (default: On)
This will create an empty for each entity, and parent its brushes to the empty. Disable
this option if you want all the brushes to be imported into the root of the map's collection.

### Ignore Triggers (default: On)
Triggers are also composed of brushes, so can be imported into Blender with this add-on,
however, they can get in the way, so by default they are not imported. Disable this
option if you would like to import triggers.

### Ignore Clip (default: On)
Clip is the name of a texture applied to brushes in all Quake engine games in order
to simplify the collision mesh and iron out parts on which the player could get stuck.
Disable this option to import them

### Ignore Hint (default: On)
Hint is the name of a texture applied to brushes in some Quake engine games in order
to give the BSP compiler a hint as to where to create portals. Disable this option to
import them.

## Tips for Working with Imported Data
Materials are created when importing a map for various geometry types, so by using
Blender's 'Select Linked' feature (Shift+L), you can select all geometry of a certain type.
For example, to select all the sky in an imported map, click on one part of the sky, hit
'Shift+L' and select 'Material'.

By default, all brushes in the MAP file are imported with origins at (0,0,0). If you would
like to move the origin of all brushes to their center, the easiest way is to select everything
and use the 'Set Origin' function.
