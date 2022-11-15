###################################################################
# Generates subtitles for the clipped videos
#
# Author: Jessica Nephin (jessica.nephin@dfo-mpo.gc.ca)
# Nov 2022
#
# Requirements:
#   Requires ffmpeg command line tool to capture images,
#   Download at https://ffmpeg.org/
#   Python version 3.9.12
#
# Description:
#   1) Uses csv output from ROV tracking data processing:
#     (https://github.com/phantomboots/ROV-Tracking-Data-Processing)
#   2) Formats the chosen variables into a subtitle file
#
# Instructions:
#   1) Check that all required modules are installed.
#   2) Ensure input videos are named following this format:
#      TripID_DiveID_YYYMMDD_HHMMSS.mp4, with no other underscores
#   3) Modify inputs section below as needed.
###################################################################


###################################################################
#   Required modules
###################################################################

import os
import subprocess
import pandas as pd


###################################################################
#   Inputs
###################################################################


# Folder name with video clips, full path if not within current wd
# Video files must be named: TripID_DiveID_YYYYMMDD_HHMMSS.mp4
videopath = 'Video_clips'

# CSV output from ROV tracking data processing, for all transects
# full path should be included in filename if not within current wd
csvfile = 'Anchorages_2022_SensorData_Georeferenced.csv'

# Column names to include in subtitle files
names = ['Datetime','Dive_Name','ROV_Longitude_loess','ROV_Latitude_loess','Depth_m','Speed_kts','Altitude_m']			


###################################################################
#   Set-up
###################################################################

# Load tracking data and subset columns
data = pd.read_csv(csvfile)
data = data[names]

# 

###################################################################
#   Loop through each video file and generate subtitles
# ###################################################################

# List video files
videofiles = os.listdir(videopath)

 # Loop through each video file
for video in videofiles:

    # Parse video filename
    parts = video.split('_')
    tripid = parts[0]
    divename = parts[1]
    videostart = parts[2] + '_' + parts[3].split('.')[0]

    # Subset rows by dive name
    divedata = data[data['Dive_Name'] == divename]

    # Format start datetime of video
    videoStartDateTime = pd.to_datetime(videostart, format='%Y%m%d_%H%M%S')

    # Get duration of video file in seconds, add a one second buffer
    durcall = ('ffprobe -v error -show_entries format=duration ' + videopath + '/' + video )
    durproc = subprocess.run(durcall, shell=True, capture_output=True, text=True)
    dur = float(re.sub('[^0-9.]', '', durproc.stdout)) + 1

    # Calculate datetime at end of video clip
    videoEndDateTime = videoStartDateTime + pd.Timedelta(seconds=int(dur))

    # Format datetime from data
    divedata = pd.to_datetime(divedata['Datetime'], format='%Y-%m-%d %H:%M:%S')

    # Subset data by datetime of video
    vdata = divedata[divedata['Datetime'] >= videoStartDateTime]
    vdata = vdata[vdata['Datetime'] <= videoEndDateTime]
    vdata = vdata.reset_index()

#! problem with this function
# makes more sense to write the lines in str_writer and then loop through str_writer, then write to file
# e.g. https://picovoice.ai/blog/how-to-create-subtitles-for-any-video-with-python/

    # Create subtitles
    def srt_writer(i, df, fields):
        return(
            f'{i+1}\n'
            f'{str(df["Datetime"].dt.time[i])} --> {str(df["Datetime"].dt.time[i+1])}\n'
            for n in fields:
                f'{n}: {str(df[n][i])}\n'
                f'\n'
        )

    # Subtitle file name
    sfile = videopath + '/' + video.split('.')[0] + '.srt'
    # Write subtitles by iterating by rows of vdata
    with open( sfile, 'w') as srt:
        for ind in vdata.index: 
            entry = srt_writer(ind, vdata, names)
            srt.write(entry)
            srt.write('\n')

