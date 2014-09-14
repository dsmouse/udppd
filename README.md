udppd
=====

Usenet Download Post-Processing daemon

This is a system to use ffmpeg to reprocess files to use preferred codecs and to not exceed specified bitrates. 
This uses ffmpeg to do it. 

Right now this is what works:
*Reads the config file and command line options
*will process a directory

When it processes a directory it creates two subfolders "orig" and "dest", and moves all the existing files to "orig". 
Then it goes through each file, classifies it as a video file or not.  For video files, it recodes it into the "dest" direcotry, changing the extention/container format as needed (mkv by default). 
For non video files, it just copies them to dest
When done, it'll clean up by deleting orig and moving everything in dest to the base dir. 
