import os
import logging
from pymediainfo import MediaInfo


# TODO Optimize,Use Class to manage some function


# 原始信息整理(mkv)
def sort_mkv_info(media_info_raw):
    general = []
    video = []
    audio = []
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
            video_temp = [
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
            ]
            video.append(video_temp)
        if track.track_type == 'Audio':
            audio_temp = [
                "ID : {0}".format(track.track_id),
                "Format : {0}".format(track.format),
                "Bit rate : {0}".format(track.other_bit_rate[0]),
                "Channel(s) : {0}".format(track.channel_s),
                "Sampling rate : {0}".format(track.other_sampling_rate[0]),
                "Forced : {0}".format(track.forced),
            ]
            audio.append(audio_temp)
    return [general, video, audio]


# 原始信息整理(mp4)
def sort_mp4_info(media_info_raw):
    general = []
    video = []
    audio = []
    for track in media_info_raw.tracks:
        if track.track_type == 'General':
            general = ["File Name : {0}".format(track.file_name + "." + track.file_extension),
                       "Format : {0}".format(track.format),
                       "File size : {0}".format(track.other_file_size[0]),
                       "Duration : {0}".format(track.other_duration[0]),
                       "Overall bit rate : {0}".format(track.other_overall_bit_rate[0])
                       ]
        if track.track_type == 'Video':
            video_temp = [
                "ID : {0}".format(track.track_id),
                "Format : {0}".format(track.format),
                "Bit rate : {0}".format(track.other_bit_rate[0]),
                "Width : {0}".format(track.width),
                "Height : {0}".format(track.height),
                "Display aspect ratio : {0}".format(track.display_aspect_ratio),
                "Frame rate : {0}".format(track.other_frame_rate[0]),
            ]
            video.append(video_temp)
        if track.track_type == 'Audio':
            audio_temp = [
                "ID : {0}".format(track.track_id),
                "Format : {0}".format(track.format),
                "Bit rate : {0}".format(track.other_bit_rate[0]),
                "Channel(s) : {0}".format(track.channel_s),
                "Sampling rate : {0}".format(track.other_sampling_rate[0]),
            ]
            audio.append(audio_temp)
    return [general, video, audio]


# 将整理过的info信息变成html字符串
def from_info_list_to_html(sorted_info):
    general_output = "<strong>General</strong><br>" + "<br>".join(sorted_info[0]) + "<br>"
    video_output = "<strong>Video</strong><br>"
    audio_output = "<strong>Audio</strong><br>"
    for i in sorted_info[1]:
        video_output_temp = "<br>".join(i) + "<br><br>"
        video_output += video_output_temp
    for i in sorted_info[2]:
        audio_output_temp = "<br>".join(i) + "<br><br>"
        audio_output += audio_output_temp
    return "{0}<br>{1}<br>{2}".format(general_output, video_output, audio_output)


# 主程序调用函数
def show_media_info(setting, file="", return_str=""):
    suffix_lower = str(os.path.splitext(file)[1][1:]).lower()
    media_info_raw = MediaInfo.parse(file)
    try:
        sorted_info = "<br>"
        if suffix_lower == "mkv":
            sorted_info = sort_mkv_info(media_info_raw)
        elif suffix_lower == "mp4":
            sorted_info = sort_mp4_info(media_info_raw)
    except TypeError as err:
        logging.warning("Can't get MediaInfo for \"{0}\",errmsg: \"{1}\"".format(file, err.args[0]))
    else:
        return_str = setting.descr_media_info(info=from_info_list_to_html(sorted_info))
        logging.info("Get MediaInfo for \"{0}\"".format(file))

    return return_str
