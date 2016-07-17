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


    def get_blender_sequence_data(self, context):
        """Build a dict containing the sequencer strip data from Blender, mapped
        by channel (aka "track" / "playlist")"""
        self.blender_sequence_data =  {}
        for s in bpy.context.sequences:
            if s.type == "SOUND":
                sd = SequenceData()
                sd.start_time_frames = s.frame_start + s.frame_offset_start - context.scene.frame_start
                sd.clip_audio_start_frames = s.animation_offset_start + s.frame_offset_start
                sd.duration_frames = s.frame_final_duration
                try:
                    sd.audio_file_src = bpy.path.abspath(s.sound.filepath)
                except AttributeError:
                    # for older versions of blender
                    sd.audio_file_src = bpy.path.abspath(s.filepath)
                sd.name = s.name
                sd.channel = s.channel
                sd.mute = s.mute
                try:
                    self.blender_sequence_data[sd.channel].append(sd)
                except KeyError:
                    self.blender_sequence_data[sd.channel] = [sd]


    def get_blender_marker_data(self, context):
        """ Return a sequence of tuples containing the name and frame no of
        each marker."""
        self.marker_data = ((m.name, m.frame - context.scene.frame_start) for m in context.scene.timeline_markers)


    def execute(self, context):
        self.get_blender_sequence_data(context)
        self.get_blender_marker_data(context)
        ardour_session = ArdourSession()
        spf = 1.0 / context.scene.render.fps # seconds per frame
        for track_no in list(self.blender_sequence_data.keys())[::-1]:
            strips = self.blender_sequence_data[track_no]
            track_name = "Blender-%d" % (track_no, )
            playlist = ardour_session.add_playlist(track_name)
            ardour_session.add_track(track_name, track_name)
            for strip in strips:
                ardour_session.create_region(
                    strip.audio_file_src,
                    strip.name,
                    playlist,
                    strip.start_time_frames * spf,
                    strip.clip_audio_start_frames * spf,
                    strip.duration_frames * spf,
                    muted = strip.mute,
                )
        for marker in self.marker_data:
            ardour_session.add_marker(marker[0], marker[1] * spf)

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
