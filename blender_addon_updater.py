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

"""
Addon purpose
To provide a built-in method of updating addons and evne blender itself

Layout planning
- Mechanics of checking for addon via release tag on git repo
-- If no tags, see if update to normal master branch version number
-- Need to deal with both .py and .zip formats
   hence search first for __init__.py, then any py
- Mechanics of downloading and reloading addon 
- Blender version check (parse https://builder.blender.org/download/)
- Download and unpack blender (to same folder, assumes .zip/make pref options)
- Addon preferences panel for how to check/notify

Todo
- Convert to zip folder structure to have local directory?
- Use the github API or just flat out do website scraping?
https://developer.github.com/v3/

"""


import bpy
import os
import urllib.request
from html.parser import HTMLParser
from bpy.app.handlers import persistent

bl_info = {
	"name": "Addon & Blender Updater (Proof of Concept)",
	"description": "Check and update for new addon and blender versions",
	"author": "Patrick W. Crawford",
	"version": (0, 0, 1),
	"blender": (2, 76, 0),
	"wiki_url": "https://github.com/TheDuckCow/blender-addon-updater/",
	"location": "Info bar",
	"warning": "In development",
	"category": "System"}


# -----------------------------------------------------------------------------
# GLOBAL VARS (keep minimal)
# -----------------------------------------------------------------------------

ADDON_UPDATE_LIST = []
ADDON_UPDATE = False
BLENDER_UPDATE = False


# -----------------------------------------------------------------------------
# ADDON UPDATER FEATURES
# -----------------------------------------------------------------------------

class updater_check_addon_updates(bpy.types.Operator):
	"""Check for updates in addon"""
	bl_idname = "wm.updater_check_addon_updates"
	bl_label = "Check addon updates"
	bl_description = "Check for any available addon updates and "+\
			"prompt to install updates"

	ui = bpy.props.BoolProperty(
		name="Run with user interface",
		description="Enable to show popup of available updates",
		default=True)

	def execute(self,context):

		## OUTLINE
		# get list of updates, for now just a hard-coded repository
		# parse to see if update available
		# bring up menu

		link_list = self.list_updates(context)
		for addon in link_list:
			# first parse for tag releases, append "release/" to the link
			# or append "tag/", but doens't have direct link to "downloads"
			update_status = self.check_for_update(addon)
			if update_status['available']==True:
				ADDON_UPDATE_LIST.append(update_status)
		if len(ADDON_UPDATE_LIST) > 0: ADDON_UPDATE = True

		return {'FINISHED'}


	def list_updates(self,context):
		print("grabbing the list of links to check for updates")
		# hard coded for now

		return ['https://github.com/TheDuckCow/blender-addon-updater/']


	def check_for_update(self, addon_link):

		# here, we must parse the given page...
		# some high level decisions need to be made of where or how it
		# searches for the appropriate link. For this narrow proof of
		# concept, we will just assume the proper download can be found
		# from the /tags page

		# This is also just direct website scraping, if github changes
		# their layout, this will break. Not a long term solution, there
		# should be an official api or listing for addons at some point
		# in the future.

		download_link = addon_link+"tags/"	
		print("Download page:",download_link)

		update_status = {'available':False,
					'link':'https://github.com/TheDuckCow/blender-addon-updater/',
					'type':'py',
					'name':'Addon & Blender Updater'}
		return update_status


class updater_addon_run_update(bpy.types.Operator):
	"""Check for updates in addon"""
	bl_idname = "wm.updater_addon_run_update"
	bl_label = "Install addon update"
	bl_description = "Install new update for a given addon"

	# though, this gives a redo-last item.. not desirable,
	# should be an enum if anything.
	addon_name = bpy.props.StringProperty(
		description="Addon to update")


	def execute(self,context):
		
		# find the according addon
		# better way to more directly get this?
		# make the ADDON_UPDATE_LIST a dictionary structure?
		addon_info = {}
		for addon in ADDON_UPDATE_LIST:
			if addon["name"] != self.addon_name:continue
			addon_info = addon
			break

		# addon_info is now the addon we want to update

		dlink = self.getDownLoadLink(addon["link"])
		# download the repository in whole
		# as it could be more than a .py
		# should download in the addon's local folder directory, a temp folder

		return {'FINISHED'}

	def getDownLoadLink(self, link):
		# we must determine if it is a .py or .zip structure

		# for this hard coded example, we just know it needs to be
		# the most recent tag link

		return 

# hack to auto-run updater when opening blender
@persistent
def load_handler(scene):
	# Now that register has finished and we checked for updates,
	# run code that  removes this handler
	bpy.app.handlers.scene_update_pre.remove(load_handler)

	# conditional check that we should check automatically this time
	# see addon preferences

	print("Checking for addon and blender updates")

	# should try to do in another thread if possible? Does that even work?
	bpy.ops.wm.updater_check_addon_updates(ui=False)


# -----------------------------------------------------------------------------
# BLENDER UPDATER FEATURES
# -----------------------------------------------------------------------------

# blender updater
# see previous attempt by another individual,
# http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/System/Check_for_updates
# but is based on website scraping and already is broken


# -----------------------------------------------------------------------------
# MENU/PREFERENCES DEFINITIONS
# -----------------------------------------------------------------------------

def addon_header_menu(self, context):
	if ADDON_UPDATE == True:
		self.layout.operator(
			updater_addon_run_update.bl_idname,
			text="Updates available",
			icon='ERROR'
		)
	else:
		self.layout.operator(
			updater_check_addon_updates.bl_idname,
			text="Check for update"
		)


class updater_preferences(bpy.types.AddonPreferences):
	bl_idname = __package__
	scriptdir = bpy.path.abspath(os.path.dirname(__file__))

	auto_check_update = bpy.props.BoolProperty(
		name = "Enable update auto-check",
		description = "Auto-check for addon or blender updates when blender starts",
		default=False
	)

	check_frequency = bpy.props.EnumProperty(
		name = "Frequency of auto-check",
		description = "How often to auto-check for updates on blender startup",
		items=[
			('always', "Always", "Check for update everytime blender opens", 0),
			('day', "Daily", "Check for updates daily", 1),
			('week', "Weekly", "Check for updates weekly", 2),
			('month', "Monthly", "Check for updates monthly", 3),
			('custom', "Custom", "Set custom update", 4),
		],
		default = 'week')

	# setting for how the notification appears?

	def draw(self, context):

		layout = self.layout
		row = layout.row()
		row.prop(self,"auto_check_update")
		row.prop(self,"check_frequency")
		row = layout.row()
		row.label("")


# -----------------------------------------------------------------------------
# REGISTRATION
# -----------------------------------------------------------------------------


def register():
	bpy.utils.register_module(__name__)
	bpy.types.USERPREF_HT_header.append(addon_header_menu)

	# the "hack" to run the update check on opening blender, run it here
	# add handler that then auto-removes itself to run with context
	bpy.app.handlers.scene_update_pre.append(load_handler)
		
def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.USERPREF_HT_header.remove(addon_header_menu)

if __name__ == "__main__":
	register()
