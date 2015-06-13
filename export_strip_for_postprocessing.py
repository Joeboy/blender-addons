import bpy
import os
import subprocess
import re
from shutil import copyfile

bl_info = {
    "name": "Export Strip For Postprocessing",
    "description": "Export the contents of a video strip as pngs for postprocessing.",
    "author": "Joe Button",
    "version": (1, 0),
    "blender": (2, 73, 0),
    "location": "Sequencer",
    "warning": "Highly sketchy",
    "wiki_url": "",
    "category": "Sequencer"
}

handle_secs = 1.0

png_re = re.compile(r'^[0-9]{5}\.png$')


class ExportStripForPostprocessing(bpy.types.Operator):
    """Export VSE Strip for Postprocessing"""
    bl_idname = "vse.exportforpostprocessing"
    bl_label = "Export for PostProcessing"
    ffmpeg_cmd = "ffmpeg"  # You might want to replace this with "avconv", if that's what you have.

    def execute(self, context):
        c = context.scene.sequence_editor.active_strip
        if c is None:
            self.report({'ERROR'}, "You must select a movie strip to export")
            return {"CANCELLED"}
        if c.type != "MOVIE":
            self.report({'ERROR'}, "Only works on movie strips")
            return {"CANCELLED"}
        src_path = os.path.abspath(
            bpy.path.abspath(c.filepath)
        )
        output_dir = bpy.path.abspath("//exported/%s" % os.path.basename(c.filepath))
        processed_dir = os.path.join(output_dir, 'processed')
        if not os.path.isdir(processed_dir):
            try:
                os.makedirs(processed_dir)
            except OSError:
                self.report({'ERROR'}, "Can't create output directory")
                return {"CANCELLED"}

        # afaict it's not possible to give ffmpeg a start frame in a reliably
        # frame-accurate way, so I guess let's output the whole thing up until
        # the last frame we want, then remove the bit at the start. Ugh.
        start_handle_frames = int(handle_secs * context.scene.render.fps)
        print("shf=", start_handle_frames)
        end_handle_frames = handle_secs * context.scene.render.fps
        frames_before_start = c.frame_offset_start + c.animation_offset_start  # number of frames we have that are outside the start of the clip
        print("frames_before_start=", frames_before_start)
        if frames_before_start < start_handle_frames:
            start_handle_frames = frames_before_start
        print("shf=", start_handle_frames)
        for a in ('frame_start', 'frame_offset_start', 'animation_offset_start'):
            print(a, getattr(c, a))
        # TODO: Work out where the end frame is
        subprocess.check_call([
            self.ffmpeg_cmd,
            '-i', src_path,
#            '-t', 'hh:mm:ss:ms',
            "%s/%%05d.png" % output_dir,
        ])
        # Copy the frames into the 'processed' dir, and set the 'processed'
        # frames as the new source for the clip
#        filenames = [f for f in os.listdir(output_dir) if png_re.match(f)]
#        for f in filenames:
#            copyfile(os.path.join(output_dir, f), os.path.join(processed_dir, f))
        files=[{'name': '%05d.png' % f} for f in range(1 + frames_before_start - start_handle_frames, 100 + frames_before_start - start_handle_frames)]
        bpy.ops.sequencer.image_strip_add(
            directory=bpy.path.relpath(processed_dir),
            frame_start=c.frame_start + c.frame_offset_start - start_handle_frames,
            #frame_end=500,
            replace_sel=True,
            files=files
        )
        print(files)
        print("start_handle_frames =",start_handle_frames)
        print("frames_before_start =", frames_before_start)
        for a in ('frame_start', 'frame_offset_start', 'animation_offset_start'):
            print(a, getattr(c, a))
        # frame_offset_start = soft clipped start
        # frame_animation_start = hard clipped start
        strip = context.scene.sequence_editor.active_strip
        strip.frame_offset_start = start_handle_frames
        print(strip, dir(strip))

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ExportStripForPostprocessing.bl_idname)


def register():
    bpy.utils.register_class(ExportStripForPostprocessing)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportStripForPostprocessing)


if __name__ == "__main__":
    register()
