""" Anchorpoint Action for creating folders
"""

import os
import shutil
from pathlib import Path

import anchorpoint as ap
import apsync

ctx = ap.Context.instance()

ATTRIBUTE_VERSION_STATUS = "Version Status"
ATTRIBUTE_APPROVED_VERSION = "Approved Version"
NOT_APPROVED_STATUS = "Not Approved"
APPROVED_STATUS = "Approved"

class SetApprovedVersion:

    def __init__(self):
        """ Init for SetApprovedVersion
        """

        self._context = ctx
        self._parent_folder = None
        self._version_folder = None
        self._version_filename = None
        self._filename_suffix = None
        self._resolved_filename = None
        self._approved_version = None
        self._ui = ap.UI()

        self._get_file_information()
        self._copy_version_file()

    def _resolve_approved_file(self):
        """ Resolves the filename to move to the versions folder parent directory.
            Removes the version number from the file
        """

        resolved_filename = self._version_filename.split("_")

        self._approved_version = resolved_filename[-1]
        resolved_filename.pop(-1)
        resolved_filename = "_".join(resolved_filename) + "." + self._filename_suffix

        return resolved_filename

    def _get_file_information(self):
        """ Sets the file information and checks if the file being approved is in the versions folder
        """

        self._version_filename = self._context.filename
        self._filename_suffix = self._context.suffix

        if "versions" in self._context.folder:
            self._version_folder = self._context.folder
            self._parent_folder = Path(self._version_folder).parent.absolute()
  
    def _copy_version_file(self):
        """ Copies the resolved filename to the desired location in the project
        """

        try:
           
            # Check if the filename is for Maya. Copies the versioned file into the parent folder
            if self._filename_suffix == "ma":
                source_file = os.path.join(self._version_folder, (self._version_filename + "." + self._filename_suffix) )
                source_path = os.path.join(self._version_folder, source_file).replace(os.path.sep, "/")
                target_filename = self._resolve_approved_file()
                target_path = os.path.join(str(self._parent_folder), target_filename).replace(os.path.sep, "/")

            # Check if the filename is an mov and if it's a playblast file, and copy to the main playblast folder for the episode
            if self._filename_suffix == "mov" and "playblasts" in self._context.path:
                source_file = os.path.join(self._version_folder, (self._version_filename + "." + self._filename_suffix) )
                source_path = os.path.join(self._version_folder, source_file).replace(os.path.sep, "/")
                episode_folder = self._context.path.split("/")
                episode_folder = os.path.join(episode_folder[0], episode_folder[1], episode_folder[2], episode_folder[3], "playblasts")
                target_filename = self._resolve_approved_file()
                target_path = os.path.join(episode_folder, target_filename).replace(os.path.sep, "/")

            # Check if the filename is an mov and if it's a playblast file, and copy to the main playblast folder for the episode
            if self._filename_suffix == "mov" and "render" in self._context.path:
                source_file = os.path.join(self._version_folder, (self._version_filename + "." + self._filename_suffix) )
                source_path = os.path.join(self._version_folder, source_file).replace(os.path.sep, "/")
                episode_folder = self._context.path.split("/")
                episode_folder = os.path.join(episode_folder[0], episode_folder[1], episode_folder[2], episode_folder[3], "finals")
                target_filename = self._resolve_approved_file()
                target_path = os.path.join(episode_folder, target_filename).replace(os.path.sep, "/")

            shutil.copyfile(source_path, target_path)

            for file in os.listdir(self._version_folder):
                if file.endswith(self._filename_suffix):
                    path = os.path.join(self._version_folder, file).replace(os.path.sep, "/")
                    #apsync.set_attribute_tag(path, ATTRIBUTE_VERSION_STATUS, NOT_APPROVED_STATUS, apsync.AttributeType.single_choice_tag, True, apsync.TagColor.red)

            
            apsync.set_attribute_text(target_path, ATTRIBUTE_APPROVED_VERSION, self._approved_version)
            apsync.set_attribute_tag(source_path, ATTRIBUTE_VERSION_STATUS, APPROVED_STATUS, apsync.AttributeType.single_choice_tag, True, apsync.TagColor.green)

            self._ui.show_success("Approval Successful!")
        except Exception:
            self._ui.show_error("Cannot set approval status on referenced files!")
                  
SetApprovedVersion()

