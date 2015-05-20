import bpy
import os
import subprocess

bl_info = {
    "name": "Open Strip Source",
    "description": "Open VSE audio/video source with an external program.",
    "author": "Joe Button",
    "version": (1, 0),
    "blender": (2, 73, 0),
    "location": "Sequencer",
    "warning": "Highly sketchy",
    "wiki_url": "",
    "category": "Sequencer"
}


class OpenStripSource(bpy.types.Operator):
    """Open VSE Strip Source"""
    bl_idname = "vse.openstripsource"
    bl_label = "Open Strip Source"

    # Change these if you want to use different external programs:
    openers = {
        "SOUND": ("audacity", "{filename}"),
        "MOVIE": ("avidemux", "{filename}"),
    }


    def execute(self, context):
        c = context.scene.sequence_editor.active_strip
        try:
            opener = self.openers[c.type]
        except KeyError:
            self.report({'ERROR'}, "No opener for '%s' strip type" % c.type)
            return {"CANCELLED"}
        filename = os.path.abspath(
            bpy.path.abspath(c.filepath)
        )
        opener = [s.format(filename=filename) for s in opener]
        subprocess.call(opener)

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(OpenStripSource.bl_idname)


def register():
    bpy.utils.register_class(OpenStripSource)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)


def unregister():
    bpy.utils.unregister_class(OpenStripSource)


if __name__ == "__main__":
    register()
