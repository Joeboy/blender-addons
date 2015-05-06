import bpy
#import subprocess
import os
import shutil
#import re
from xml.etree import ElementTree as ET

bl_info = {
    "name": "VSE Export",
    "description": "Export the VSE timeline to a text file.",
    "author": "Joe Button",
    "version": (1, 0),
    "blender": (2, 73, 0),
    "location": "Sequencer",
    "warning": "Highly sketchy",
    "wiki_url": "",
    "category": "Sequencer"
}

class SequenceData(object):
    pass



class VseExport(bpy.types.Operator):
    """Export the VSE timeline to a text file"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "vse.export"        # unique identifier for buttons and menu items to reference.
    bl_label = "Export VSE"         # display name in the interface.


    def get_empty_ardour_session(self):
        skel_path = os.path.join(os.path.dirname(__file__), "empty-session")
        et = ET.parse(os.path.join(skel_path, "empty-session.ardour"))
        self.session = et.getroot()
        self.session.set("name", self.session_name)


    def get_blender_sequence_data(self):
        """Build a dict containing the sequencer strip data from Blender, mapped
        by channel (aka "track" / "playlist")"""
        self.blender_sequence_data =  {}
        for s in bpy.context.sequences:
            if s.type == "SOUND":
                sd = SequenceData()
                sd.audio_start_time_frames = s.frame_start - 1
                sd.audio_duration_frames = s.frame_duration
                sd.clip_start_time_frames = s.frame_start -1 + s.frame_offset_start
                sd.clip_end_time_frames = sd.audio_start_time_frames + sd.audio_duration_frames - s.frame_offset_end - 1
                sd.audio_filename = os.path.basename(s.filepath)
                sd.audio_file_location = bpy.path.abspath(s.filepath)
                sd.channel = s.channel
                try:
                    self.blender_sequence_data[sd.channel].append(sd)
                except KeyError:
                    self.blender_sequence_data[sd.channel] = [sd]


    def write_audiofile_to_session(self, path_to_file):
        # TODO: resample to self.session_audio_rate if necessary
        shutil.copy(path_to_file,
                    os.path.join(self.ardour_session_root,
                                 "interchange",
                                 self.session_name,
                                 "audiofiles"))


    def _get_next_id(self):
        if not hasattr(self, "_id_counter"):
            # Find biggest numeric id in session:
            ids = (e.attrib.get('id') for e in self.session.findall(".//*[@id]"))
            ids = (int(i) for i in ids if i.isnumeric())
            self._id_counter = max(ids)
        self._id_counter += 1
        return str(self._id_counter)


    def execute(self, context):
        self.session_name = "ardour-session"
        self.blender_project_root = bpy.path.abspath("//")
        self.ardour_session_root = os.path.join(self.blender_project_root, self.session_name)
        self.get_empty_ardour_session()
        self.session_audio_rate = int(self.session.attrib.get("sample-rate", "48000"))
        self.spf = 1.0 / context.scene.render.fps # seconds per frame
        # TODO: Look for existing session and modify it if it exists
        try:
            os.makedirs(os.path.join(self.ardour_session_root, "interchange", self.session_name, "audiofiles"))
        except:
            pass

        sources = self.session.find("Sources")
        regions = self.session.find("Regions")
        playlists = self.session.find("Playlists")

        self.get_blender_sequence_data()
        for track_no in self.blender_sequence_data.keys():
                #<Playlist id="255" name="test-base" type="audio" orig-track-id="224" frozen="no" combine-ops="0">
            playlist_attrs = {
                'id': self _get_next_id(),
                'name': "Blender-%d" % track_no,
                'type': "audio",
#                'orig-track-id': "TODO",
                'frozen': "no",
                'combine-ops': "0",
            }
            ET.SubElement(playlists, "Playlist", playlist_attrs)

            
            clips = self.blender_sequence_data[track_no]
            print(track_no, clips)
        return {'FINISHED'}
        for strip in self.audio_strips:
            self.write_audiofile_to_session(strip.audio_file_location)
            source_id = self._get_next_id()
            attrs = {'name': strip.audio_filename, 
                     'type': 'audio',
                     'flags': '',
                     'id': source_id,
                     'channel': "0",
                     'origin': ''
            }
            ET.SubElement(sources, "Source", attrs)

            # "Whole file region":
            region_attrs = {
                'name': strip.audio_filename + 'asf',
                'muted': "0",
                'opaque': "1",
                'locked': "0",
                'automatic': "0",
                'whole-file': "1",
                'import': "0",
                'external': "1",
                'sync-marked': "0",
                'left-of-split': "0",
                'right-of-split': "0",
                'hidden': "0",
                'position-locked': "0",
                'valid-transients': "0",
                'start': "0",
                'length': "TODO",
                'position': "0",
                'sync-position': "0",
                'ancestral-length': "0",
                'stretch': "1",
                'shift': "1",
                'positional-lock-style': "AudioTime",
                'layering-index': "0",
                'envelope-active': "0",
                'default-fade-in': "0",
                'default-fade-out': "0",
                'fade-in-active': "1",
                'fade-out-active': "1",
                'scale-amplitude': "1",
                'id': self._get_next_id(),
                'type': "audio",
                'first-edit': "nothing",
                'source-0': source_id,
                'master-source-0': source_id,
                'channels': "1",
            }
            ET.SubElement(Regions, "Region", attrs)
        #     <Region name="test-base" muted="0" opaque="1" locked="0" video-locked="0" automatic="0" whole-file="1" import="0" external="1" sync-marked="0" left-of-split="0" right-of-split="0" hidden="0" position-locked="0" valid-transients="0" start="0" length="288187" position="0" sync-position="0" ancestral-start="0" ancestral-length="0" stretch="1" shift="1" positional-lock-style="AudioTime" layering-index="0" envelope-active="0" default-fade-in="0" default-fade-out="0" fade-in-active="1" fade-out-active="1" scale-amplitude="1" id="215" type="audio" first-edit="nothing" source-0="213" master-source-0="213" channels="1"/>

#        ET.dump(self.session)
        return {'FINISHED'}

        self.report({'ERROR'}, "Exactly two strips must be selected")
        return {'CANCELLED'}


def menu_func(self, context):
    self.layout.operator(VseExport.bl_idname)


def register():
    bpy.utils.register_class(VseExport)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)


def unregister():
    bpy.utils.unregister_class(VseExport)


if __name__ == "__main__":
    register()
