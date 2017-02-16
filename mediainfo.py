from pymediainfo import MediaInfo


# 函数读入视频文件地址，然后生成对应MediaInfo信息（html形式）
def show_media_info(file=''):
    media_info_raw = MediaInfo.parse(file)
    file_extension = media_info_raw.tracks[0].file_extension
    general = []
    video = []
    audio = []
    if file_extension == "mkv":
        for track in media_info_raw.tracks:
            if track.track_type == 'General':
                general = ["File Name : {0}".format(track.file_name + "." + track.file_extension),
                           "Unique ID : {0}".format(track.other_unique_id[0]),
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
    elif file_extension == "mp4":
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
    else:
        return

    # 拼合原始信息
    general_output = "<strong>General</strong><br>" + "<br>".join(general) + "<br>"
    video_output = "<strong>Video</strong><br>"
    audio_output = "<strong>Audio</strong><br>"

    for i in video:
        video_output_temp = "<br>".join(i) + "<br>"
        video_output += video_output_temp

    for i in audio:
        audio_output_temp = "<br>".join(i) + "<br>"
        audio_output += audio_output_temp

    return "<fieldset><legend><b>MediaInfo:（自动生成，仅供参考）</b></legend>{0}<br>{1}<br>{2}</fieldset> ".format(
        general_output, video_output, audio_output)
