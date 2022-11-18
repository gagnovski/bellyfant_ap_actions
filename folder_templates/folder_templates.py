""" Anchorpoint Action for creating folders
"""

import os
import shutil
import string
from pathlib import Path

import anchorpoint as ap
import apsync
ctx = ap.Context.instance()

JOBS_FOLDER = "jobs"
PROJECTS_FOLDER = ""
ASSETS_FOLDER = "assets"
SEQUENCES_FOLDER = "sequences"
EPISODES_FOLDER = "episodes"
SHOTS_FOLDER = "shots"
EMPTY_FILE = ".jobfile"

ATTRIBUTE_VERSION_STATUS = "Version Status"
ATTRIBUTE_APPROVED_VERSION = "Approved Version"
NOT_APPROVED_STATUS = "Not Approved"
APPROVED_STATUS = "Approved"

PROJECTS_TEMPLATE = os.path.join(ctx.yaml_dir, ctx.inputs["project_template"]).replace(os.path.sep, "/")
ASSETS_TEMPLATE = os.path.join(ctx.yaml_dir, ctx.inputs["asset_template"]).replace(os.path.sep, "/")
EPISODES_TEMPLATE = os.path.join(ctx.yaml_dir, ctx.inputs["episode_template"]).replace(os.path.sep, "/")
SEQUENCES_TEMPLATE = os.path.join(ctx.yaml_dir, ctx.inputs["sequence_template"]).replace(os.path.sep, "/")
SHOTS_TEMPLATE = os.path.join(ctx.yaml_dir, ctx.inputs["shot_template"]).replace(os.path.sep, "/")

class CreateFolderTemplate:

    def __init__(self):

        self._context = ctx
        self._ui = ap.UI()
        self._dialog = None
        self._folder_type = None
        self._input_name = None
        self._increment = 10
        self._override_increment = False
        self._capitalize = False
        self._parent_folder = None
        self._episode_name = None
        self._sequence_name = None
        self._variation_name = "A"
        self._build_type = "char"
        #self._progress = ap.Progress("Custom Folder Creation")

        #print (self._context)

        self._display_folder_context()

    def _enable_shotoverride(self, dialog, value):
        if value:
            self._dialog.set_enabled("name", True)
        else:
            self._dialog.set_enabled("name", False)

    def create_project_dialog(self):
        """ Create the dialog for creating a new episode folder
        """

        self._dialog = ap.Dialog()

        self._dialog.title = "New Project"
        if ctx.icon:
            self._dialog.icon = ctx.icon
        
        # Present the dialog to the user
        self._dialog.add_text("Project Name").add_input("", var="name")
        self._dialog.add_separator()
        self._dialog.add_separator()
        self._dialog.add_text("\t\t\t\t").add_button("Create", callback=self._launch_template_builder)
        self._dialog.show()

    def create_asset_dialog(self):
        """ Create the dialog for creating a new asset folder
        """

        self._dialog = ap.Dialog()

        self._dialog.title = "New Asset"
        if ctx.icon:
            self._dialog.icon = ctx.icon
        
        # Present the dialog to the user
        self._dialog.add_text("Asset Name\t").add_input(placeholder="asset name", var="name")
        self._dialog.add_text("Build Type\t\t").add_dropdown("char", ["char", "prop", "set", "vhcl", "fx"], var="build_type")
        self._dialog.add_text("Variation\t\t").add_dropdown("A", list(string.ascii_uppercase), var="variation")
        self._dialog.add_text("\t")
        self._dialog.add_text("\t\t\t\t").add_button("Create", callback=self._launch_template_builder)
        self._dialog.show()

    def create_episode_dialog(self):
        """ Create the dialog for creating a new episode folder
        """

        self._dialog = ap.Dialog()

        self._dialog.title = "New Episode"
        if ctx.icon:
            self._dialog.icon = ctx.icon
        
        # Present the dialog to the user
        self._dialog.add_text("Episode Name").add_input("", var="name")
        self._dialog.add_text("\t")
        self._dialog.add_text("\t\t\t\t").add_button("Create", callback=self._launch_template_builder)
        self._dialog.show()

    def create_sequence_dialog(self):
        """ Create the dialog for creating a new episode folder
        """

        self._dialog = ap.Dialog()

        self._dialog.title = "New Sequence"
        if ctx.icon:
            self._dialog.icon = ctx.icon
        
        # Present the dialog to the user
        self._dialog.add_checkbox(False, callback=self._enable_shotoverride, var="enable_shotoverride").add_text("Sequence Number").add_input(str(self._increment), var="name", enabled=False)
        self._dialog.add_text("\t")
        self._dialog.add_text("\t\t\t\t").add_button("Create", callback=self._launch_template_builder)
        self._dialog.show()

    def create_shot_dialog(self):
        """ Create the dialog for creating a new episode folder
        """

        self._dialog = ap.Dialog()

        self._dialog.title = "New Shot"
        if ctx.icon:
            self._dialog.icon = ctx.icon
        
        # Present the dialog to the user
        self._dialog.add_checkbox(False, callback=self._enable_shotoverride, var="enable_shotoverride").add_text("Shot Number").add_input(str(self._increment), var="name", enabled=False)
        self._dialog.add_text("\t")
        self._dialog.add_text("\t\t\t\t").add_button("Create", callback=self._launch_template_builder)
        self._dialog.show()

    def _launch_template_builder(self, callback):

        self._dialog.close()

        self._override_increment = self._dialog.get_value("enable_shotoverride")

        input_value = self._dialog.get_value("name")
        self._input_name = input_value
        self._variation_name = self._dialog.get_value("variation")

        if self._dialog.get_value("build_type"):
            self._build_type = self._dialog.get_value("build_type")

        self._build_folder_template()

    def _resolve_file_folder(self, path=None):
        """ Resolves the folder or filename based on provided tokens

            Args:
                path (str): Path to unresolved file / folder

            Returns:
                resolved_path (str): Path to resolved file / folder
        """

        if path:
            if self._capitalize:
                self._input_name = self._input_name.upper()
            else:
                self._input_name = self._input_name[0].upper() + self._input_name[1:]
               
            resolved_path = path.format(
                type=self._build_type,
                increment=self._increment,
                episode=self._episode_name,
                sequence=self._sequence_name,
                name=self._input_name, 
                variation=self._variation_name
                )

            return resolved_path.replace(os.path.sep, "/")

    def _get_folder_count(self, path, increment_offset=1):

        # Define how many folders are in the directory to define the next increment
        directories = os.listdir(path)
        increment = 0
        for directory in directories:
            if os.path.isdir(os.path.join(path, directory)):
                increment += 1

        if not self._override_increment:
            increment = (increment * increment_offset) + increment_offset
        else:
            increment = self._increment

        self._increment = str(increment).zfill(4)

    def _display_folder_context(self):
        """ Get the current context and display the approriate UI for folder creation
        """

        if self._context.relative_path.endswith(":") or self._context.relative_path.endswith(JOBS_FOLDER):
            self._folder_type = PROJECTS_FOLDER
            self._parent_folder = Path(self._context.path).parent.absolute()
            self.create_project_dialog()

        #if self._context.relative_path.endswith(ASSETS_FOLDER):
        if self._context.relative_path == ASSETS_FOLDER:
            self._folder_type = ASSETS_FOLDER
            self._parent_folder = Path(self._context.path).parent.absolute()
            self.create_asset_dialog()

        #if self._context.relative_path.endswith(EPISODES_FOLDER):
        if self._context.relative_path == EPISODES_FOLDER:
            self._folder_type = EPISODES_FOLDER
            self._parent_folder = Path(self._context.path).parent.absolute()
            self.create_episode_dialog()

        #if self._context.relative_path.endswith(SEQUENCES_FOLDER):
        if self._context.path.endswith(SEQUENCES_FOLDER):
            self._folder_type = SEQUENCES_FOLDER
            self._parent_folder = Path(self._context.path).parent.absolute()
            self._episode_name  = str(self._parent_folder).split(os.path.sep)[-1]
            self._get_folder_count(self._context.path, increment_offset=10)
            self.create_sequence_dialog()

        #if self._context.relative_path.endswith(SHOTS_FOLDER):
        if self._context.path.endswith(SHOTS_FOLDER):
            self._folder_type = SHOTS_FOLDER
            self._parent_folder = Path(self._context.path).parent.absolute()
            self._sequence_name  = str(self._parent_folder).split(os.path.sep)[-1]
            self._get_folder_count(self._context.path, increment_offset=10)
            self.create_shot_dialog()      

    def _create_empty_folders(self, directory):
        """ Creates the empty folders and creates an empty file for registering the folder on the cloud drive

            Args:
                directory (str): Path for the directory to create
        """

        if not os.path.exists(directory):
            os.makedirs(directory)

            empty_file = os.path.join(directory, EMPTY_FILE).replace(os.path.sep, "/")
            Path(empty_file).touch()
            os.system("attrib +h {}". format(empty_file))

    def _copy_source_files(self, source_root, source_files, target_root):
        """ Copies the any source files over that should come as a starting point file

            Args:
                source_root (str): Root path from the folder template
                source_files (list): List of files within the root folder
                target_root (str): Target path to copy the files to
        """

        if len(source_files) > 0:
            for file in source_files:
                resolved_file_name = self._resolve_file_folder(file)

                source_destination = os.path.join(source_root, file).replace(os.path.sep, "/")
                target_destination = os.path.join(target_root, resolved_file_name).replace(os.path.sep, "/")

                if file == "emptyfile":
                    continue

                if not os.path.exists(target_destination):
                    shutil.copyfile(source_destination, target_destination)
                    #apsync.copy_file(source_destination, target_destination, True)

                    if os.path.dirname(target_destination).endswith("scenes"):
                        apsync.set_attribute_text(target_destination, ATTRIBUTE_APPROVED_VERSION, "v0001", True)

                    if os.path.dirname(target_destination).endswith("versions"):
                        apsync.add_attribute_tag(target_destination, ATTRIBUTE_VERSION_STATUS, APPROVED_STATUS, apsync.AttributeType.single_choice_tag, True, apsync.TagColor.green)


    def _build_folders(self, folder_type=None, template=None, path=None, increment_offset=10, capitalize=False):
        """ Builds the folders and copies the proxy files across

            Args:
                folder_type (str): What type of folder structure we're creating
                template (str): Path to the folder template we're creating
                path (str): Location to the first folder of the template we're creating
        """

        # Set what style to set the name of the folder to
        if capitalize:
            self._capitalize = True

        # Define how many folders are in the directory to define the next increment
        
        self._get_folder_count(self._context.path, increment_offset=increment_offset)
        if self._override_increment:
            self._increment = str(self._input_name)

        #self._progress.set_text("Creating Folders...")

        for root, dirs, files in os.walk(path):

            folder = self._resolve_file_folder(root)
            folder = folder.replace(template +"/", "")

            base_dir = os.path.join(self._parent_folder, folder_type, folder).replace(os.path.sep, "/")

            if not os.path.exists(base_dir):
                self._create_empty_folders(base_dir)

            self._copy_source_files(root, files, base_dir)

    def _build_folder_template(self):
        """ Create the folder structure based on the current context the user is in
        """

        progress = ap.Progress("Building Folders",infinite = True)

        if self._folder_type == PROJECTS_FOLDER:
            start_folder = os.path.join(PROJECTS_TEMPLATE, os.listdir(PROJECTS_TEMPLATE)[0]).replace(os.path.sep, "/")
            self._build_folders(folder_type=self._context.relative_path, template=PROJECTS_TEMPLATE, path=start_folder)
            self._ui.show_success("Project Folder Created Successful")

        if self._folder_type == ASSETS_FOLDER:

            # Get the first folder within the templated asset folder
            start_folder = os.path.join(ASSETS_TEMPLATE, os.listdir(ASSETS_TEMPLATE)[0]).replace(os.path.sep, "/")
            build_folder = os.path.join(ASSETS_FOLDER, self._build_type).replace(os.path.sep, "/")
            self._build_folders(folder_type=build_folder, template=ASSETS_TEMPLATE, path=start_folder)

            self._ui.show_success("Asset Folder Created Successful")

        if self._folder_type == EPISODES_FOLDER:

            start_folder = os.path.join(EPISODES_TEMPLATE, os.listdir(EPISODES_TEMPLATE)[0]).replace(os.path.sep, "/")
            self._build_folders(folder_type=EPISODES_FOLDER, template=EPISODES_TEMPLATE, path=start_folder, increment_offset=10, capitalize=True)
            self._ui.show_success("Episode Folder Created Successful")

        if self._folder_type == SEQUENCES_FOLDER:

            start_folder = os.path.join(SEQUENCES_TEMPLATE, os.listdir(SEQUENCES_TEMPLATE)[0]).replace(os.path.sep, "/")
            self._build_folders(folder_type=SEQUENCES_FOLDER, template=SEQUENCES_TEMPLATE, path=start_folder, increment_offset=10, capitalize=True)
            self._ui.show_success("Sequence Folder Created Successful")

        if self._folder_type == SHOTS_FOLDER:

            start_folder = os.path.join(SHOTS_TEMPLATE, os.listdir(SHOTS_TEMPLATE)[0]).replace(os.path.sep, "/")
            build_folder = os.path.join(EPISODES_FOLDER, self._parent_folder, SHOTS_FOLDER).replace(os.path.sep, "/")
            #self._context.run_async(self._build_folders, folder_type=build_folder, template=SHOTS_TEMPLATE, path=start_folder, increment_offset=10, capitalize=True)
            self._build_folders(folder_type=build_folder, template=SHOTS_TEMPLATE, path=start_folder, increment_offset=10, capitalize=True)
            self._ui.show_success("Shot Folder Created Successful")

        progress.finish()
                
CreateFolderTemplate()

