import requests
import json
import time

CONNECT_SERVER = ""
CONNECT_PORT = ""
CONNECT_ENDPOINT = ""
API_ENDPOINT = ""

def server(server, port, proto = "http"):
	global CONNECT_SERVER, CONNECT_PORT, CONNECT_ENDPOINT, API_ENDPOINT
	CONNECT_SERVER = server
	CONNECT_PORT = port
	CONNECT_ENDPOINT = proto + "://" + CONNECT_SERVER + ":" + str(CONNECT_PORT)
	API_ENDPOINT = CONNECT_ENDPOINT + "/api/v1/instances"

def do_health_check():
	# We just grab the information from the metrics page and return the data in HTML format
	try:
		metrics = requests.get(CONNECT_ENDPOINT + "/metrics")
	except requests.exceptions.ConnectionError:
		return "<div class=\"w3-container w3-red w3-padding w3-round\" style=\"width: 400px;\">The BNG Blaster is currently unreachable!</div>"

	running = 0
	total = 0

	# We remove the comments and query the instances parameters
	for line in metrics.text.split("\n"):
		if line.startswith("#"):
			continue

		# we split by space to get the desriptor and the number
		data = line.split(" ")
		if "instances_running" in data[0]:
			running = int(data[1])
		elif "instances_total" in data[0]:
			total = int(data[1])

	# Now we create the html for the server
	html = """
			<div class="w3-card w3-third w3-teal w3-padding w3-margin">
				<h4>Currently running instances: {}</h4>
			</div>
			<div class="w3-card w3-third w3-amber w3-padding w3-margin">
				<h4>Total instances: {}</h4>
			</div>
	""".format(str(running), str(total))

	return html

def ordered(obj):
	# This function orders an obj to make it comparable
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj

def check_project_running(project_id):
	try:
		exists = requests.get("{}/{}".format(API_ENDPOINT, project_id))
		if exists.status_code == 200 and exists.json()["status"] == "started":
			return True
	except requests.exceptions.ConnectionError:
		return False

	return False

def generate_control(project_id, json_object):
	# We do this as a try catch. If nothing answers, we send the corresponding message.

	# We have an HTML frame with a specific number of buttons and depending on the different requests, we make some of them unusable

	showUpload = ""
	showDownload = "disabled"
	showStart = "disabled"
	showStop = "disabled"
	showKill = "disabled"
	showError = "disabled"


	# All Variables are disabled by default. We check if the project exists. If not, we keep them like this
	try:
		exists = requests.get("{}/{}".format(API_ENDPOINT, project_id))
	except requests.exceptions.ConnectionError:
		return "<div class=\"w3-container w3-red w3-padding w3-round\" style=\"width: 400px;\">The BNG Blaster is currently unreachable!</div>"

	if exists.status_code == 200:
		# The project exists and we can get the status
		data = exists.json()
		if data["status"] == "stopped":
			# We make the start button available
			showStart = ""
			showDownload = ""
			showError = ""
		elif data["status"] == "started":
			# We make the stop and kill button available
			showStop = ""
			showKill = ""
			showUpload = "disabled" # We definately want to disable it, whether or not the configs are the same

		if error_log(project_id, True) == "":
			showError = "disabled"

		# We no can check the configuration
		# We query the json from the server and compare it to our local json
		server_json = requests.get("{}/{}/config.json".format(API_ENDPOINT, project_id)).json()
		if ordered(server_json) == ordered(json_object):
			showUpload = "disabled"
			showDownload = "disabled"

	html = """
		<button class="w3-button w3-blue control-button" onclick="uploadToServer()" {}>Upload to Blaster</button>
		<button class="w3-button w3-blue control-button" onclick="downloadFromServer()" {}>Download From Blaster</button>
		<button class="w3-button w3-green control-button" onclick="startInstance()" {}>Start Instance</button>
		<button class="w3-button w3-red control-button" onclick="stopInstance()" {}>Stop Instance</button>
		<button class="w3-button w3-orange control-button" onclick="killInstance()" {}>Kill Instance</button>
		<button class="w3-button control-button w3-red" onclick="loadErrorLog()" {}>Load Error Log</button>
	""".format(showUpload, showDownload, showStart, showStop, showKill, showError)

	return html

def upload(project_id, json_object):
	headers = {"Content-Type": "application/json"}

	try:
		upload = requests.put("{}/{}".format(API_ENDPOINT, project_id), data=json.dumps(json_object), headers=headers)
	except requests.exceptions.ConnectionError:
		return "990"

	# We examine the response code
	if upload.status_code in [200, 204]:
		# all is good, we request the server to reload the buttons
		return "200"
	else:
		return str(upload.status_code)

def start(project_id):
	commands = {
		"logging": True,
		"logging_flags": ["error", "ip"],
		"pcap_capture": False,
		"session_count": 1
	}

	try:
		start = requests.post("{}/{}/_start".format(API_ENDPOINT, project_id), json=commands)
	except requests.exceptions.ConnectionError:
		return "990"

	return str(start.status_code)

def stop(project_id, kill):
	try:
		stop = requests.post("{}/{}/_{}".format(API_ENDPOINT, project_id, "kill" if kill else "stop"))
	except requests.exceptions.ConnectionError:
		return "990"

	return str(stop.status_code)

def log(project_id):
	# We now request the stdout and return it as html, if the instance exists

	log = "The instance was not pushed to the blaster and never ran."
	try:
		exists = requests.get("{}/{}".format(API_ENDPOINT, project_id))
	except requests.exceptions.ConnectionError:
		return "990"

	if exists.status_code == 200:
		# We check if the project is running and adjust accordingly
		if exists.json()["status"] == "started":
			log = "The instance is currently running. Please terminate it in order to see the log."
		else:
			log = requests.get("{}/{}/run.stdout".format(API_ENDPOINT, project_id)).text

			if log == "":
				log = "There is no Log-File currently available. The instance was never started or it was killed. Poor instance."

	html = """
		<div class="w3-container w3-padding">
			<h3>Results</h3>
			<div class="w3-white">
				<code class="w3-margin-top" style="word-wrap: break-word; white-space: pre-wrap;">{}
				</code>
			</div>
		</div>
	""".format(log)

	return html

def error_log(project_id, pure = False):
	# We now request the stdout and return it as html, if the instance exists

	log = "The instance was not pushed to the blaster and never ran."

	try:
		exists = requests.get("{}/{}".format(API_ENDPOINT, project_id))
	except requests.exceptions.ConnectionError:
		return "990"

	if exists.status_code == 200:
		log = requests.get("{}/{}/run.stderr".format(API_ENDPOINT, project_id)).text

	if pure:
		return log

	if log == "":
			log = "Currently, there are no errors"

	html = """
		<div class="w3-container w3-margin w3-padding">
			<h3>Results</h3>
			<div class="w3-white">
				<code class="w3-margin-top" style="word-wrap: break-word; white-space: pre-wrap;">{}
				</code>
			</div>
		</div>
	""".format(log)

	return html

def download_from_server_modal(project_id):
	try:
		server_json = requests.get("{}/{}/config.json".format(API_ENDPOINT, project_id)).json()
	except requests.exceptions.ConnectionError:
		return "990"

	html = """
		<div class="w3-modal-content w3-padding w3-round">
			<h2>Overwrite Project?</h2>
			The following configuration is currently placed on the server. If you proceed, all local changes will be overwritten.
			<div class="s3-white">
				<code class="w3-margin-top" style="word-wrap: break-word; white-space: pre-wrap;">{}
				</code>
			</div>
			<button class="w3-button w3-red" onclick="proceedOverwriteProject()">Proceed and overwrite project</button>
			<button class="w3-button" onclick="hideOverwriteProject()">Cancel</button>
		</div>
	""".format(json.dumps(server_json, indent = 4))

	return html

def download_from_server(project_id):
	try:
		obj = requests.get("{}/{}/config.json".format(API_ENDPOINT, project_id)).json()
	except requests.exceptions.ConnectionError:
		return None

	return obj