# Quelea2OBS

## Instalation
Install python3 for your platform then with the executable run.

```python3 -m pip install -r requirements.txt```
this will install all dependencies necessary for the program to run.

## Quelea Configuration
Go to ```configuration > server settings``` and activate mobile remote.


## Python Configuration
Change the lines for the ip and port that appear in server settings.

```
quelea_remote = "http://192.168.1.14:1112"
```

## Python Run
`python3 -u waitress_server.py`

## OBS Settings
Add a browser source and type as URL the following: ```http://<ip running the python script>:<port in configuration>/live_obs_html/<source name>/first```.

Set height and width equals to your video resolution.

Copy one of the examples `style_music.css` or `style_verse.css` and paste in `personalized css box`.

Activate `refresh when turning visible`.

## Usage
- Open Quelea.
- Go to ```http://<ip running the python script>:<port in configuration>```.
- Enter the password that is set in Quelea server settings.
- You can use the lighter blue to change the lines that are being sent to obs.

## Troubleshooting
If you have `refresh when turning visible` on if any of the views bug out, you can activate and deactivate to force a refresh of the page.

If the problem persist you can click on `refresh cache of the page` on the preferences of the source.

