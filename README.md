# Quelea2OBS

## INSTALATION 
Install python3 for your platform
than with executable in hand do 

```python3 -m pip install -r requirements.txt```
this will install all dependencies necessary for the program to run.

## quelea configuration
go to configuration » server settings and activate mobile remote


## Python configuration
change the lines for the ip and port that appear in server settings.
change file location to a folder in your pc

quelea_remote = "http://192.168.1.14:1112"
file_location = "/home/igreja/StreamResources/QueleaActiveLyrics.txt"

## python run
python3 main.py

## obs settings
add a browser source and type as url
the http://«ip running the python script»:«port in configuration»/live_obs_html/«source name»/first
set high and width to your video resolution
copy one of the examples style_music.css or style_verse.css and paste in personalized css box.
activate refresh when turning visible

## usage
- open quelea
- go to http://«ip running the python script»:«port in configuration»
- enter the password that is set in server settings
- you can use the lighter blue to change the lines that are being sent to obs.

## troubleshooting
if you have refresh when turning visible if any of the views bug you can activate and deactivate to force a refresh of the page
if the proble persist you can click on refresh cache of the page on the preferences of the source

