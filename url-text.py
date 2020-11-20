
import obspython as obs
import urllib.request
import urllib.error
import threading
import json
from time import sleep

url         = ""
interval    = 30
source_name = ""
update_threads = []
label_2_url =  {}
index = 0
multiline_square = ""
# ------------------------------------------------------------

def keep_updating_fn(b, u):
	global keep_updating
	while(keep_updating):
		update_text(b,u)


def update_text(b,u):

	source = None
	try:
		source = obs.obs_get_source_by_name(b)
		if source is not None:
			try:
				obs.script_log(obs.LOG_INFO,f"{str(datetime.datetime.now())} - Requesting <{u}>")
				with urllib.request.urlopen(u) as response:
					data = response.read()
					text = data.decode('utf-8')
					obs.script_log(obs.LOG_INFO,f"{str(datetime.datetime.now())} - Requesting <{u}> got me <{text}>")

					settings = obs.obs_data_create()
					obs.obs_data_set_string(settings, "text", text)
					obs.obs_source_update(source, settings)
					obs.obs_data_release(settings)

			except urllib.error.URLError as err:
				obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} -  Error opening URL '" + url + "': " + str(err))
				sleep(1)
				#obs.remove_current_callback()

	except Exception as e:
		obs.script_log(obs.LOG_INFO, "Error : " + str(e))
	finally:
		if source is not None:
			obs.obs_source_release(source)


def __start__():
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - BEGIN START FUNCTION")

	__stop__()
	global update_threads
	global label_2_url
	global keep_updating
	keep_updating = True

	update_threads = []

	for k,v in label_2_url.items():
		obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - starting thread {k} : {v}")
		update_thread = threading.Thread(target=keep_updating_fn, args=(k,v))
		update_thread.start()
		update_threads.append(update_thread)
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - END START FUNCTION")


def __stop__():
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - BEGIN STOP FUNCTION")
	global update_threads
	global keep_updating
	global label_2_url

	keep_updating = False
	for update_thread in update_threads:
		obs.script_log(obs.LOG_INFO, f"stopping {update_thread is not None}")
		if update_thread is not None:
			update_thread.join()
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - END STOP FUNCTION")

def start_pressed(props, prop):
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - START WAS PRESSED")
	__start__()


def stop_pressed(props, prop):
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - STOP WAS PRESSED")
	__stop__()


def __load_pressed__():
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - BEGIN LOAD PRESSED FUNCTION")
	global label_2_url
	global url
	global multiline_square

	label_2_url = json.loads(multiline_square)
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - END LOAD PRESSED FUNCTION")


def load_pressed(props, prop):
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - LOAD WAS PRESSED")
	__load_pressed__()


def script_load(settings):
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - SCRIPT LOADED")
	script_update(settings)
	__load_pressed__()
	__start__()


def script_unloaded():
	obs.script_log(obs.LOG_INFO, f"{str(datetime.datetime.now())} - SCRIPT UNLOADED")
	__stop__()

# ------------------------------------------------------------

def script_description():
	return "Updates a text source to the text retrieved from a URL at every specified interval.\n\nBy Jim"


def script_update(settings):
	global multiline_square
	multiline_square = obs.obs_data_get_string(settings, "multiline_square_name")
	
def script_defaults(settings):
	pass


def script_properties():
	props = obs.obs_properties_create()


	p = obs.obs_properties_add_list(props, "source", "List of Names", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	sources = obs.obs_enum_sources()
	if sources is not None:
		for source in sources:
			source_id = obs.obs_source_get_unversioned_id(source)
			if source_id == "text_gdiplus" or source_id == "text_ft2_source":
				name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(p, name, name)

		obs.source_list_release(sources)
	
	obs.obs_properties_add_text(props, "multiline_square_name", """{"label":"url"}""", obs.OBS_TEXT_MULTILINE)
	#obs.obs_properties_add_text(props, "url", "URL", obs.OBS_TEXT_DEFAULT)

	obs.obs_properties_add_button(props, "buttonLoad", "Load", load_pressed)
	obs.obs_properties_add_button(props, "button", "Start", start_pressed)
	obs.obs_properties_add_button(props, "button2", "Stop", stop_pressed)



	return props
