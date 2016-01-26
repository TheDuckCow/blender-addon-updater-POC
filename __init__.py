# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####



bl_info = {
	"name": "Addon & Blender Updater (Proof of Concept)",
	"description": "Check and update for new addon and blender versions",
	"author": "Patrick W. Crawford",
	"version": (0, 0, 1),
	"blender": (2, 76, 0),
	"wiki_url": "https://github.com/TheDuckCow/blender-addon-updater/",
	"location": "Info bar",
	"warning": "In development",
	"category": "System"
}


if "bpy" in locals():

	import importlib
	importlib.reload(blender_addon_updater)

else:
	import bpy

	from . import blender_addon_updater


def register():
	bpy.utils.register_module(__name__)
	blender_addon_updater.register()


def unregister():
	bpy.utils.unregister_module(__name__)
	blender_addon_updater.unregister()


if __name__ == "__main__":
	register()
