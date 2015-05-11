import bpy
import os
from .ardoursession import ArdourSession

bl_info = {
    "name": "VSE Ardour Export",
    "description": "Export the VSE timeline to an ardour session.",
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


class ArdourVseExport(bpy.types.Operator):
    """Export the VSE timeline audio to an ardour session"""
    bl_idname = "vse.ardourexport"
    bl_label = "Export VSE to Ardour"


    def get_blender_sequence_data(self):
        """Build a dict containing the sequencer strip data from Blender, mapped
        by channel (aka "track" / "playlist")"""
        self.blender_sequence_data =  {}
        for s in bpy.context.sequences:
            if s.type == "SOUND":
                sd = SequenceData()
                sd.clip_audio_start_frames = s.animation_offset_start
                sd.clip_audio_end_frames = s.animation_offset_end
                sd.audio_start_time_frames = s.frame_start - 1
                sd.audio_duration_frames = s.frame_duration
                sd.strip_start_time_frames = s.frame_start -1 + s.frame_offset_start
                sd.strip_end_time_frames = sd.audio_start_time_frames + sd.audio_duration_frames - s.frame_offset_end
                sd.audio_filename = os.path.basename(s.filepath)
                sd.audio_file_location = bpy.path.abspath(s.filepath)
                sd.channel = s.channel
                sd.mute = s.mute
                try:
                    self.blender_sequence_data[sd.channel].append(sd)
                except KeyError:
                    self.blender_sequence_data[sd.channel] = [sd]


    def execute(self, context):
        self.get_blender_sequence_data()
        ardour_session = ArdourSession()
        spf = 1.0 / context.scene.render.fps # seconds per frame
        for track_no in self.blender_sequence_data.keys():
            strips = self.blender_sequence_data[track_no]
            track_name = "Blender-%d" % (track_no, )
            playlist = ardour_session.add_playlist(track_name)
            ardour_session.add_track(track_name, track_name)
            for strip in strips:
                ardour_session.create_region(
                    strip.audio_file_location,
                    playlist,
                    strip.strip_start_time_frames * spf,
                    (strip.strip_start_time_frames - strip.audio_start_time_frames + strip.clip_audio_start_frames) * spf,
                    (strip.strip_end_time_frames - strip.strip_start_time_frames) * spf,
                    muted = strip.mute,
                )
        dest = os.path.join(
            bpy.path.abspath("//"),
            "ardour-session",
            "ardour-session.ardour"
        )
        ardour_session.write(dest)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ArdourVseExport.bl_idname)


def register():
    bpy.utils.register_class(ArdourVseExport)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ArdourVseExport)


if __name__ == "__main__":
    register()
