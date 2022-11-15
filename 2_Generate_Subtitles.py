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
#   2) Formats the specified variables from that csv file into 
#      subtitle files for each video clip
#
# Instructions:
#   1) Check that all required modules are installed
#   2) Ensure input videos are named following this format:
#      TripID_DiveID_YYYMMDD_HHMMSS.mp4, with no other underscores
#   3) Modify inputs section below as needed
#   4) Position and font of subtitles can be adjusted within VLC 
###################################################################


###################################################################
#   Required modules
###################################################################

import os
import subprocess
import pandas as pd
import re


###################################################################
#   Inputs
###################################################################


# Folder name with video clips, full path if not within current wd
# Video files must be named: TripID_DiveID_YYYYMMDD_HHMMSS.mp4
# No other files can be in this folder, including other subtitle files
videopath = 'Video_clips'

# CSV output from ROV tracking data processing, for all transects
# full path should be included in filename if not within current wd
csvfile = 'Anchorages_2022_SensorData_Georeferenced.csv'

# Column names to include in subtitle files, must be found in csv file
names = ['Datetime','Dive_Name','ROV_Longitude_loess','ROV_Latitude_loess','Depth_m','Speed_kts','Altitude_m']			


###################################################################
#   Set-up
###################################################################

# Load tracking data and subset columns
data = pd.read_csv(csvfile)
data = data[names]

# Format datetime from data
data['Datetime'] = pd.to_datetime(data['Datetime'], format='%Y-%m-%d %H:%M:%S')
# Format time from datetime
data['Time'] = data['Datetime'].dt.time
names.insert(1, 'Time')
data = data[names]

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
    
     # Format start datetime of video
    videoStartDateTime = pd.to_datetime(videostart, format='%Y%m%d_%H%M%S')
    
    # Get duration of video file in seconds, add a one second buffer
    durcall = ('ffprobe -v error -show_entries format=duration ' + videopath + '/' + video )
    durproc = subprocess.run(durcall, shell=True, capture_output=True, text=True)
    dur = float(re.sub('[^0-9.]', '', durproc.stdout)) + 1

    # Calculate datetime at end of video clip
    videoEndDateTime = videoStartDateTime + pd.Timedelta(seconds=int(dur))
    # Subset rows by dive name
    divedata = data.loc[data['Dive_Name'] == divename]
    divedata = divedata.reset_index(drop=True)

    # Subset data by datetime of video
    vdata = divedata.loc[divedata['Datetime'] >= videoStartDateTime]
    vdata = vdata.loc[vdata['Datetime'] <= videoEndDateTime]
    vdata = vdata.reset_index(drop=True)

    # Filter names to simplify, remove "ROV" and Loess and units after underscores
    newnames = [re.sub('ROV_|loess', '', n) for n in names]
    newnames = [re.sub('_.*', '', n) for n in newnames]
    vdata.columns = newnames

    # Round all fields except for lat and lon fields and dive and datetime
    r = re.compile('.*Lat|.*Lon|.*Time')
    stdfields = list(filter(r.match, newnames)) 
    othercols = list(set(newnames) - set(stdfields + list(['Dive', 'Datetime'])))
    # Round other columns to 1 decimal
    vdata[othercols] = vdata[othercols].round(decimals=1)
    # Round standard columns (lat/lon) to 5 decimals
    vdata[stdfields] = vdata[stdfields].round(decimals=5)

    # Add elapse time field
    vdata['elapsed'] = vdata['Datetime'] - videoStartDateTime
    vdata['elapsedstr'] = vdata['elapsed'].astype(str).str.split(' ').str[-1]
    
    # Start list to append line
    strlist = list()

    # Create subtitles, loop through all rows except the last
    for i in vdata.iloc[:-1].index:
        strlist.append( f'{i+1}\n' )
        strlist.append( f'{vdata["elapsedstr"][i]} --> {vdata["elapsedstr"][i+1]}\n' )
        # Add line for standard fields
        for s in stdfields:
            strlist.append( f'{s}: {str(vdata[s][i])}   ' )
        strlist.append( f'\n' )
        # Add line for other fields
        for o in othercols:
            strlist.append( f'{o}: {str(vdata[o][i])}   ' )
        strlist.append( f'\n\n' )

    # Subtitle file name
    sfile = videopath + '/' + video.split('.')[0] + '.srt'
    # Write subtitles by iterating by rows of vdata
    with open( sfile, 'w') as f:
        f.writelines(strlist)
