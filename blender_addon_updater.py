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
- implement popup UI with prop_popup and a UIList
- Use the github API or just flat out do website scraping?
https://developer.github.com/v3/

"""


import bpy
import os
import urllib.request
import zipfile
import shutil
from html.parser import HTMLParser
from bpy.app.handlers import persistent


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

		global ADDON_UPDATE_LIST
		global ADDON_UPDATE
		ADDON_UPDATE_LIST.clear()

		link_list = self.list_updates(context)
		for addon in link_list:
			# first parse for tag releases, append "release/" to the link
			# or append "tag/", but doens't have direct link to "downloads"
			update_status = self.check_for_update(addon)
			if update_status['available']==True:
				ADDON_UPDATE_LIST.append(update_status)
				print("added "+update_status["name"])
		if len(ADDON_UPDATE_LIST) > 0: ADDON_UPDATE = True

		# menu popup to show
		if self.ui == True:
			bpy.ops.wm.updater_addon_popup('INVOKE_DEFAULT')
		else:
			print("Update READY! Show user in another way..")

		return {'FINISHED'}


	def list_updates(self,context):
		print("grabbing the list of links to check for updates")
		# hard coded for now, but this would grab from a webserver
		# or scrape a website will a listing of all addons (and source links)

		print("Hard coded: checking for updates to the updater addon? 2meta4me")
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

		update_status = {'available':True,
			'link':'https://github.com/TheDuckCow/blender-addon-updater/releases/',
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
		description="Addon to update",
		default="")

	def execute(self,context):
		
		# find the according addon
		# better way to more directly get this?
		# make the ADDON_UPDATE_LIST a dictionary structure?
		addon_info = {}
		for addon in ADDON_UPDATE_LIST:
			if addon["name"] != self.addon_name:continue
			addon_info = addon
			break
		if addon_info=={}: return # didn't find the addon match

		# addon_info is now the addon we want to update

		dlink = self.getDownLoadLink(addon["link"])

		# download the repository in whole
		# as it could be more than a .py
		# should download in the addon's local folder directory, a temp folder
		# then unzip, see if __init__ file, and accordingly move files over to
		# blender addons folder, remove caches, and reload modules.
		# don't forget to copy current one, pre-updated for backup's sake (and
		# later check the internal folder for restore addons to recover with)

		# ensure our folder is always "clean"
		local = os.path.join(os.path.dirname(__file__), "staging")
		if os.path.isdir(local) == True:
			shutil.rmtree(local)
		try:
			os.makedirs(local)
		except:
			print("ERRRROR making staging directory")
			return {'CANCELLED'}

		print("we here.")
		urllib.request.urlretrieve(dlink, os.path.join(local,"source.zip"))
		print("we here?")

		# now unzip and see what's there
		secure_unzip(os.path.join(local,"source.zip"), os.path.join(local,"source"))
		# unzipped, but really need to rename it - to drop the tag

		# now try to unload existing addon, move new one to place, remove caches
		# (or use the install manually)
		# refresh;
		# and catch any error popups if possible...
		# popup saying if anything gos wrong, restart blender
		# and if still not updated, then use the "restore" button (yet 2b implemented)


		return {'FINISHED'}

	def getDownLoadLink(self, link):
		# the following code does website scraping and is very specific to
		# GitHub. For this hard coded example, we just know it needs to be the
		# most recent tag link

		# in the future, a proper repository would bypass this with a real 
		# html/REST request

		print("Downloading webpage")
		content = urllib.request.urlopen(link,timeout=100).read().decode('utf-8')
		print("Proceeding to scrape the website for download link")

		# scrape for specific, most "recent release"
		# looking for different "tags" on the download page
		
		[base,subLink] = link.split(".com") # should always just be 2
		subLink = subLink.split("releases")[0]
		base += ".com"
		divider = 'href="'+subLink

		pre_possible_links = content.split(divider)
		possible_links = []
		compiled_source_exists = False
		for pre in pre_possible_links:
			possible_links.append(pre.split('"')[0])
			if "/download/" in possible_links:
				compiled_source_exists = True
		possible_links = possible_links[1:]

		print("POSSIBLE LINKS")
		for a in possible_links:print(a)
		print("###########")

		# if compiled_source_exists == True:# if specific .zip was included to download
		# instead of via source code itself (in case repo is not self contained)
		# else, assume use the tag/download the source folder.


		# scraping not quite done, so hack it for now and return the "right answer"
		final_link = "https://github.com/TheDuckCow/blender-addon-updater/archive/0.0.1.zip"


		# once we get the right link, return the download link we want
		return final_link


def secure_unzip(source_filename, dest_dir):
		with zipfile.ZipFile(source_filename) as zf:
			for member in zf.infolist():
				words = member.filename.split(os.path.sep)
				path = dest_dir
				for word in words[:-1]:
					drive, word = os.path.splitdrive(word)
					head, word = os.path.split(word)
					if word in (os.curdir, os.pardir, ''): continue
					path = os.path.join(path, word)
				zf.extract(member, path)


class updater_addon_popup(bpy.types.Operator):
	"""Popup menu to display current updates available"""
	bl_idname = "wm.updater_addon_popup"
	bl_label = "Updater popup"
	bl_description = "Popup menu to display current updates available"

	def invoke(self, context, event):
		return context.window_manager.invoke_popup(self) # can force width

	def draw(self, context):
		layout = self.layout
		print("popup")

		# case where there are no updates
		if len(ADDON_UPDATE_LIST)==0:
			col = layout.column()
			col.label("No addon updates found")
			col.label("Click OK to close popup")
			return

		# otherwise, list the updates
		row = layout.row()
		row.label("Addons with available updates")
		row = layout.row()
		col1 = row.column()
		col2 = row.column()
		for addon in ADDON_UPDATE_LIST:

			col1.operator("wm.updater_addon_run_update",
				text="Update x addon".format(x=addon["name"])
				).addon_name = addon["name"]
			col2.operator("wm.url_open", text="Website").url = addon["link"]

		# but with this UI method, pressing a button does not
		# dismiss the popup, though full control over UI and is draggable

		# alternative would be check boxes or a UI list where user
		# checks all the ones they want updated
		


	def execute(self,context):

		# based on elections above, decide which ones to install
		# this function doesn't actually run anything,
		# but this format forces a floating "OK" window
		print("ran popup exec")
		return {'FINISHED'}



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

class updater_check_blender_update(bpy.types.Operator):
	"""Check for new blender update"""
	bl_idname = "wm.updater_check_blender_update"
	bl_label = "Check blender update"
	bl_description = "Check for new blender update"

	def execute(self,context):
		
		self.report({'ERROR'}, "Not implemented yet")
		return {'CANCELLED'}

		return {'FINISHED'}

# -----------------------------------------------------------------------------
# MENU/PREFERENCES DEFINITIONS
# -----------------------------------------------------------------------------

def update_header_menu_APPEND(self, context):
	
	if ADDON_UPDATE == True or BLENDER_UPDATE == True:
		self.layout.menu(update_menu.bl_idname, icon='ERROR',\
				text="Update available")
	else:
		self.layout.menu(update_menu.bl_idname)


class update_menu(bpy.types.Menu):
	bl_label = "Check updates"
	bl_idname = "updater_check_menu"
	bl_description = "Check for blender and addon updates"

	def draw(self, context):
		layout = self.layout
		if ADDON_UPDATE==True:
			layout.operator(updater_check_addon_updates.bl_idname,icon="ERROR",\
					text="Addon updates available")
		else:
			layout.operator(updater_check_addon_updates.bl_idname)
		
		if BLENDER_UPDATE==True:
			layout.operator(updater_check_blender_update.bl_idname,icon='ERROR',\
					text="Blender update available")
		else:
			layout.operator(updater_check_blender_update.bl_idname)


def debug_addon_update(self, context):
	global ADDON_UPDATE
	ADDON_UPDATE = self.debug_addon

def debug_blender_update(self, context):
	global BLENDER_UPDATE
	BLENDER_UPDATE = self.debug_blender

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
	
	debug_addon = bpy.props.BoolProperty(
		name="Pretend addon updates ready",
		default=False,
		update=debug_addon_update
	)

	debug_blender = bpy.props.BoolProperty(
		name="Pretend blender update ready",
		default=False,
		update=debug_blender_update
	)

	# setting for how the notification appears?

	def draw(self, context):

		layout = self.layout
		row = layout.row()
		row.prop(self,"auto_check_update")
		row = layout.row()
		row.enabled = self.auto_check_update
		row.prop(self,"check_frequency")
		if self.check_frequency=='custom':
			row = layout.row()
			row.label("eventually custom text box for days/months/etc")
		col = layout.column()
		col.label("Debugging")
		box = col.box()
		box.prop(self,"debug_addon")
		box.prop(self,"debug_blender")
		box.label("Addon:{x}, Blender:{y}".format(x=ADDON_UPDATE,y=BLENDER_UPDATE))


# -----------------------------------------------------------------------------
# REGISTRATION
# -----------------------------------------------------------------------------


def register():
	bpy.types.USERPREF_HT_header.append(update_header_menu_APPEND)
	#bpy.types.USERPREF_HT_header.append("updater_check_menu")

	# the "hack" to run the update check on opening blender, run it here
	# add handler that then auto-removes itself to run with context
	bpy.app.handlers.scene_update_pre.append(load_handler)
		
def unregister():
	bpy.types.USERPREF_HT_header.remove(update_header_menu_APPEND)
	# bpy.types.USERPREF_HT_header.remove("updater_check_menu")

if __name__ == "__main__":
	register()
