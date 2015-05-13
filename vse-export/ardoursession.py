import os
from xml.etree import ElementTree as ET
import subprocess


class ArdourSessionException(Exception):
    pass


class ArdourSession(object):
    avconv_cmd = "avconv"  # TODO: set this less stupidly

    def __init__(self, filename=None):
        """Load and parse session from filename, or from default empty session
        file if no filename passed."""
        self.session_src_filename = filename
        if self.session_src_filename:
            # Load session from filename
            self.etree = ET.parse(self.session_src_filename)
        else:
            # load default empty session
            self.etree = ET.parse(
                os.path.join(
                    os.path.dirname(__file__),
                    "empty-session/empty-session.ardour"
                )
            )
        self.session = self.etree.getroot()
        self.audio_rate = int(self.session.attrib.get("sample-rate", "48000"))
        self.sources = self.session.find("Sources")
        self.regions = self.session.find("Regions")
        self.routes = self.session.find("Routes")
        self.playlists = self.session.find("Playlists")
        self.audio_files = []


    def add_playlist(self, name):
        return ET.SubElement(self.playlists, "Playlist", {
                'id': self._get_next_id(),
                'name': name,
                'type': "audio",
#                'orig-track-id': "23",
                'frozen': "no",
                'combine-ops': "0",
        })


    def copy_audiofile(self, src_path, dst_filename, session_dir):
        output_filename = os.path.join(
            session_dir,
            'interchange',
            self.session_name,
            'audiofiles',
            dst_filename
        )
        subprocess.check_call([
            self.avconv_cmd,
            '-i', src_path, '-vn', '-f', 'wav', '-ar', str(self.audio_rate),
            '-y', output_filename
        ])


    def _get_next_id(self):
        if not hasattr(self, "_id_counter"):
            # Find biggest numeric id in session:
            ids = (e.attrib.get('id') for e in self.session.findall(".//*[@id]"))
            ids = (int(i) for i in ids if i.isdigit())
            self._id_counter = max(ids)
        self._id_counter += 1
        return str(self._id_counter)


    def create_region(self, src_filename, strip_name, playlist, position, start, length, muted=False):
        # Add the file, and add it as a source
        # {position} is the beginning of the region (in seconds)
        # {start} is the amount of audio clipped from the start of the region (in seconds)
        # {length} is the lengh of the regoin (in seconds)

        full_path = os.path.abspath(src_filename)
        dest_filename = "%s.wav" % (strip_name,)

        self.audio_files.append((full_path, dest_filename))

        # Add the file as a source:
        source_id = self._get_next_id()
        ET.SubElement(self.sources, "Source", {
            'name': dest_filename,
            'type': 'audio',
            'flags': '',
            'id': source_id,
            'channel': "0",
            'origin': ''
        })

        # Create a "whole file region"
        region_attrs = {
            'name': strip_name,
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
#            'length': str(self.audio_files[full_path]['nframes']),     # Ardour doesn't seem to mind not having this. I think.
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
        ET.SubElement(self.regions, "Region", region_attrs)
        # Create a "playlist region"
        playlist_region_attrs = region_attrs.copy()
        playlist_region_attrs.update({
            'position': str(position * self.audio_rate),
            'start': str(start * self.audio_rate),
            'length': str(length * self.audio_rate),
            'muted': muted and '1' or '0',
        })

        return ET.SubElement(playlist, "Region", playlist_region_attrs)


    def add_track(self, track_name, playlist_name):
        route = ET.SubElement(self.routes, "Route", {
            'active': 'yes',
            'default-type': 'audio',
            'denormal-protection': 'no',
            'id': self._get_next_id(),
            'meter-point': 'MeterPostFader',
            'meter-type': 'MeterPeak',
            'mode': 'Normal',
            'monitoring': '',
            'name': track_name,
            'order-key': '1',
            'phase-invert': '0',
            'saved-meter-point': 'MeterPostFader',
            'self-solo': 'no',
            'solo-isolated': 'no',
            'solo-safe': 'no',
            'soloed-by-downstream': '0',
            'soloed-by-upstream': '0',
        })

        io = ET.SubElement(route, "IO", {
            'name': track_name,
            'id': self._get_next_id(),
            'direction': 'Input',
            'default-type': 'audio',
            'user_latency': '0',
        })
        port = ET.SubElement(io, "Port", {
            'type': 'audio',
            'name': '%s/audio_in 1' % (track_name, ),
        })
        io = ET.SubElement(route, "IO", {
            'name': track_name,
            'id': self._get_next_id(),
            'direction': 'Output',
            'default-type': 'audio',
            'user_latency': '0',
        })
        port = ET.SubElement(io, "Port", {
            'type': 'audio',
            'name': '%s/audio_out 1' % (track_name, ),
        })
        connection = ET.SubElement(port, "Connection", {
            'other': "Master/audio_in 1",
        })
        port = ET.SubElement(io, "Port", {
            'type': 'audio',
            'name': '%s/audio_out 2' % (track_name, ),
        })
        connection = ET.SubElement(port, "Connection", {
            'other': "Master/audio_in 2",
        })
        processor = ET.SubElement(route, "Processor", {
            'active': 'yes',
            'id': self._get_next_id(),
            'name': 'Amp',
            'type': 'trim',
            'user-latency': '0',
        })
        processor = ET.SubElement(route, "Processor", {
            'active': 'yes',
            'id': self._get_next_id(),
            'name': 'Amp',
            'type': 'amp',
            'user-latency': '0',
        })
        ET.SubElement(route, "Diskstream", {
            'capture-alignment': 'Automatic',
            'channels': '1',
            'flags': 'Recordable',
            'id': self._get_next_id(),
            'name': track_name,
            'playlist': playlist_name,
            'speed': '1.000000000000',
        })
        return route


    def write(self, filename=None):
        if filename:
            session_dir, filename = os.path.split(os.path.abspath(filename))
            self.session_name, ext = os.path.splitext(filename)
            self.session.set("name", self.session_name)
        elif self.sesson_src_filename:
            # Write to the original file
            session_dir, filename = os.path.split(os.path.abspath(self.session_src_filename))
            self.session_name, ext = os.path.splitext(filename)
        else:
            raise ArdourSessionException("Destination filename unknown.")
        assert ext == '.ardour', "Destination filename should have .ardour extension"

        try:
            os.makedirs(os.path.join(session_dir, "interchange", self.session_name, "audiofiles"))
        except:
            pass

        self.etree.write(os.path.join(session_dir, filename))

        for filepath, dest_filename in self.audio_files:
            self.copy_audiofile(filepath, dest_filename, session_dir)


if __name__ == "__main__":
    ardour_session = ArdourSession()
    playlist = ardour_session.add_playlist('track1')
    ardour_session.add_track("track1", 'track1')
    ardour_session.create_region(
        "./test.wav",
        playlist,
        5.0,
        0.5,
        1.0
    )
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "test-session", "test-session.ardour")
    ardour_session.write(dest)

