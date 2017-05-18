import os
import logging
import pymediainfo

encode_dict = {
    "html": {
        "line_sep": "<br>",
        "text_strong": "<strong>{text}</strong>"
    },
    "bbcode": {
        "line_sep": "\n",
        "text_strong": "[b]{text}[/b]"
    }
}


class MediaInfo(object):
    def __init__(self, file, encode):
        self.file = file
        self.encode = encode

    def show(self, return_str=None):
        try:
            sorted_info = self.raw2dict()
        except TypeError as err:
            logging.warning("Can't get MediaInfo for \"{0}\",errmsg: \"{1}\"".format(self.file, err.args[0]))
        else:
            return_str = self.dict2out(sorted_info)
            logging.info("Get MediaInfo for \"{0}\"".format(self.file))
        return return_str

    def raw2dict(self):
        media_info_raw = pymediainfo.MediaInfo.parse(self.file)
        suffix = str(os.path.splitext(self.file)[1][1:])

        general = []
        video = []
        audio = []
        if suffix.lower() == "mkv":
            for track in media_info_raw.tracks:
                if track.track_type == 'General':
                    general = ["File Name : {0}".format(track.file_name + "." + track.file_extension),
                               "Unique ID : {0}".format(track.other_unique_id[0]),  # TODO Error when group is fleet
                               "Format : {0}".format(track.format),
                               "Format version : {0}".format(track.format_version),
                               "File size : {0}".format(track.other_file_size[0]),
                               "Duration : {0}".format(track.other_duration[0]),
                               "Overall bit rate : {0}".format(track.other_overall_bit_rate[0]),
                               "Encoded date : {0}".format(track.encoded_date),
                               "Writing application : {0}".format(track.writing_application),
                               "Writing library : {0}".format(track.writing_library)
                               ]
                if track.track_type == 'Video':
                    video.append([
                        "ID : {0}".format(track.track_id),
                        "Format : {0}".format(track.format),
                        "Format profile : {0}".format(track.codec_profile),
                        "Bit rate : {0}".format(track.other_bit_rate[0]),
                        "Width : {0}".format(track.width),
                        "Height : {0}".format(track.height),
                        "Display aspect ratio : {0}".format(track.display_aspect_ratio),
                        "Frame rate : {0}".format(track.other_frame_rate[0]),
                        "Chroma subsampling : {0}".format(track.chroma_subsampling),
                        "Bit depth : {0}".format(track.other_bit_depth[0]),
                        "Writing library : {0}".format(track.writing_library),
                        "Encoding settings : {0}".format(track.encoding_settings),
                        "Matrix coefficients : {0}".format(track.matrix_coefficients),
                    ])
                if track.track_type == 'Audio':
                    audio.append([
                        "ID : {0}".format(track.track_id),
                        "Format : {0}".format(track.format),
                        "Bit rate : {0}".format(track.other_bit_rate[0]),
                        "Channel(s) : {0}".format(track.channel_s),
                        "Sampling rate : {0}".format(track.other_sampling_rate[0]),
                        "Forced : {0}".format(track.forced),
                    ])
        elif suffix.lower() == "mp4":
            for track in media_info_raw.tracks:
                if track.track_type == 'General':
                    general = ["File Name : {0}".format(track.file_name + "." + track.file_extension),
                               "Format : {0}".format(track.format),
                               "File size : {0}".format(track.other_file_size[0]),
                               "Duration : {0}".format(track.other_duration[0]),
                               "Overall bit rate : {0}".format(track.other_overall_bit_rate[0])
                               ]
                if track.track_type == 'Video':
                    video.append([
                        "ID : {0}".format(track.track_id),
                        "Format : {0}".format(track.format),
                        "Bit rate : {0}".format(track.other_bit_rate[0]),
                        "Width : {0}".format(track.width),
                        "Height : {0}".format(track.height),
                        "Display aspect ratio : {0}".format(track.display_aspect_ratio),
                        "Frame rate : {0}".format(track.other_frame_rate[0]),
                    ])
                if track.track_type == 'Audio':
                    audio.append([
                        "ID : {0}".format(track.track_id),
                        "Format : {0}".format(track.format),
                        "Bit rate : {0}".format(track.other_bit_rate[0]),
                        "Channel(s) : {0}".format(track.channel_s),
                        "Sampling rate : {0}".format(track.other_sampling_rate[0]),
                    ])

        return [general, video, audio]

    def dict2out(self, sorted_info):
        line_sep = encode_dict[self.encode]["line_sep"]
        text_strong = encode_dict[self.encode]["text_strong"]

        general_output = text_strong.format(text="General") + line_sep + line_sep.join(sorted_info[0]) + line_sep
        video_output = text_strong.format(text="Video") + line_sep
        audio_output = text_strong.format(text="Audio") + line_sep
        for i in sorted_info[1]:
            video_output_temp = line_sep.join(i) + line_sep * 2
            video_output += video_output_temp
        for i in sorted_info[2]:
            audio_output_temp = line_sep.join(i) + line_sep * 2
            audio_output += audio_output_temp

        return line_sep.join([general_output, video_output, audio_output])
