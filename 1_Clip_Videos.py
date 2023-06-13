###################################################################
# Video clipping using ffmpeg
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
#   1) Gets start and end transect time from dive log and 
#       clips full dive videos into segments, starting 30 seconds
#       before the transect start time and ending at least 30 seconds 
#       after the transect end time.
#   2) Names the video clips using the same formats as the input videos.
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
from datetime import datetime
from datetime import timedelta
import subprocess
import csv
import re


###################################################################
#   Inputs
###################################################################

# Size of video clips in minutes, as text string 'mm'
clipsize = '10'

# Folder name with videos, full path if not within current wd
# Video files must be named: TripID_DiveID_YYYYMMDD_HHMMSS.mp4
videopath = 'Videos'

# Dive log file, full path if not within current wd
divelog = 'Pac2022_Anchor_divelog.csv'

# Column number in the dive log with dive name and start time
dive = 6 # column with dive name
start = 11 # column with start time in UTC
end = 12 # column with end time in UTC


###################################################################
#   Set-up
###################################################################

# Function to convert a csv file into dictionaries
def csv_dict(variables_file, col1, col2):
    # Load csv and create a dictionary
    with open(variables_file, mode='r') as infile:
        reader = csv.reader(infile, delimiter=',')
        dict_list = {rows[col1-1]:rows[col2-1] for rows in reader}
        return dict_list

# Calls to csv_dict,
# returns dictionary of video filenames and start times and end times
startsDict = csv_dict(divelog, dive, start)
startsDict.pop('Dive_Name', None)
endsDict = csv_dict(divelog, dive, end)
endsDict.pop('Dive_Name', None)

# Create directory to save images if it doesn't exist
outputdir = 'Video_clips'
if not os.path.exists(outputdir):
    os.makedirs(outputdir)


###################################################################
#   Loop through each video file and clip
###################################################################

# List video files
videofiles = os.listdir(videopath)

# Loop through each video file
for video in videofiles:

    # Parse video filename
    parts = video.split('_')
    tripid = parts[0]
    divename = parts[1]
    videostart = parts[2] + ' ' + parts[3].split('.')[0]

    # Get start datetime of video
    videoStartDateTime = datetime.strptime(videostart, '%Y%m%d %H%M%S')

    # Get start and end datetime of transect
    tstart = startsDict.get(divename)
    transectStartDateTime = datetime.strptime(tstart, '%Y-%m-%d %H:%M:%S')
    tend = endsDict.get(divename)
    transectEndDateTime = datetime.strptime(tend, '%Y-%m-%d %H:%M:%S')

    # Video should start before transect starts, check:
    if videoStartDateTime > transectStartDateTime:
        print("Warning! Transect " + divename + " starts before the video file starts")

    # Subtract and add 30 seconds from transect start and end times to allow for a buffer
    transectStartDateTime = transectStartDateTime - timedelta(seconds=30)
    transectEndDateTime = transectEndDateTime + timedelta(seconds=30)

    # Calculate the elapsed time to the start of transect to begin the first video clip
    elapsedSecs = transectStartDateTime - videoStartDateTime
    
    # Get duration of video file in seconds
    durcall = ('ffprobe -v error -show_entries format=duration ' + videopath + '/' + video )
    durproc = subprocess.run(durcall, shell=True, capture_output=True, text=True)
    dur = float(re.sub('[^0-9.]', '', durproc.stdout))

    # Original video file should end after end of transect in dive log, check:
    elapsedSecs_endtransect = (transectEndDateTime - videoStartDateTime).seconds
    if elapsedSecs_endtransect > dur:
        print("Warning! Transect " + divename + " ends after the video file finishes")


    # Clip videos while elpased time is less than duration
    while elapsedSecs.seconds < elapsedSecs_endtransect:

        # Video clip file name
        starttime = videoStartDateTime + elapsedSecs
        strstarttime = starttime.strftime('%Y%m%d_%H%M%S')
        clipname = outputdir +'/'+ tripid +'_'+ divename + '_' + strstarttime + '.mp4'

        # Clip video
        elapsedtime = str(elapsedSecs)
        clipcall = ('ffmpeg -ss ' + elapsedtime + ' -i ' + videopath + '/' + video + ' -t 00:' + clipsize + ':00 -c copy ' + clipname)
        subprocess.call(clipcall, shell = True)

        # Add to elapsed seconds
        elapsedSecs = elapsedSecs + timedelta(minutes=int(clipsize))


