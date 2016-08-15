import bpy
import subprocess
import os
import re

bl_info = {
    "name": "Sync Audio",
    "description": "Sync audio strips in the VSE using cross-correlation.",
    "author": "Joe Button",
    "version": (1, 0),
    "blender": (2, 73, 0),
    "location": "Sequencer",
    "warning": "Highly sketchy",
    "wiki_url": "",
    "category": "Sequencer"
}

executable_name = os.path.join(os.path.dirname(__file__), "syncaudio")

output_re = re.compile(b'^lag = -?\d+ samples, (?P<seconds>-?[0-9+]\.?\d*) seconds')



class SyncAudio(bpy.types.Operator):
    """Sync audio clips using shenidam"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "audio.sync"        # unique identifier for buttons and menu items to reference.
    bl_label = "Sync Audio"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):
        active_strip = bpy.context.scene.sequence_editor.active_strip
        selected_sequences = [s for s in bpy.context.selected_sequences if s != active_strip]
        if len(selected_sequences) != 1:
            self.report({'ERROR'}, "Exactly two strips must be selected")
            return {'CANCELLED'}
        base_strip = selected_sequences[0]

        try:
            active_strip_filepath = bpy.path.abspath(active_strip.sound.filepath)
            base_strip_filepath = bpy.path.abspath(base_strip.sound.filepath)
        except AttributeError:
            # for older versions of blender
            active_strip_filepath = bpy.path.abspath(active_strip.filepath)
            base_strip_filepath = bpy.path.abspath(base_strip.filepath)

        try:
            output = subprocess.check_output([executable_name,
                                              active_strip_filepath,
                                              base_strip_filepath])
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        m = output_re.match(output)
        if m is None:
            self.report({'ERROR'}, "syncaudio returned unexpected output:\n%s" % output)
            return {'CANCELLED'}

        lag_secs = float(m.group('seconds'))

        fps = context.scene.render.fps
        lag_frames = fps * lag_secs

        active_strip.frame_start = base_strip.frame_start - lag_frames

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(SyncAudio.bl_idname)


def register():
    bpy.utils.register_class(SyncAudio)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SyncAudio)


if __name__ == "__main__":
    register()
