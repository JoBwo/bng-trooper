from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory
import project
import blaster
import os
import threading
import json

app = Flask(__name__)


PROJECTS = {}

# We define some static Settings
SETTINGS = {"interfaces": ["eth1", "eth2"]}

# Location Arrays
LOCATION_PROJECT = {"project": "w3-blue", "settings": "", "create": "", "home": ""}
LOCATION_SETTINGS = {"project": "", "settings": "w3-blue", "create": "", "home": ""}
LOCATION_CREATE = {"project": "", "settings": "", "create": "w3-blue", "home": ""}
LOCATION_HOME = {"project": "", "settings": "", "create": "", "home": "w3-blue"}

SAVE_FOLDER = "saves/"

#### DUMMY DATA HARDCODED
#PROJECTS["abcde"] = project.Project("Test project")
#PROJECTS["abcde"].apply_settings(SETTINGS)
server = "127.0.0.1"
port = 8001

# We initialize the blaster
blaster.server(server, port)

# Dummy Strings to fill in
ERROR_DIV = "<div class=\"error\"><h2>The following error occured:</h2>{}</div>"

def get_project_by_id(id):
	# Check if id is none or empty, return None
	if id == None or id == "":
		return None

	# The next step is to check, if the project is currently loaded in RAM
	if id in PROJECTS:
		# The project is loaded in RAM
		return PROJECTS[id]

	return None

@app.route("/api/project/control", methods=["POST"])
def project_control():
	# This endpoint is responsible for the communication to the bngblaster
	# We need to query the project id first, then we need to get the project reference
	project = get_project_by_id(request.form["id"])

	if project == None:
		return ERROR_DIV.format("The project could not be found on the server.")

	mode = request.form["mode"]

	if mode == "healthcheck":
		# We just want to check, if we can reach the bng-blaster
		return blaster.do_health_check()
	elif mode == "control":
		return blaster.generate_control(project.id, project.json(False))
	elif mode == "upload":
		return blaster.upload(project.id, project.json(False))
	elif mode == "start":
		return blaster.start(project.id)
	elif mode == "stop" or mode == "kill":
		return blaster.stop(project.id, True if mode == "kill" else False)
	elif mode == "download-dry":
		return blaster.download_from_server_modal(project.id)
	elif mode == "download":
		return project.load_json(blaster.download_from_server(project.id))
	elif mode == "log":
		return blaster.log(project.id)
	elif mode == "error":
		return blaster.error_log(project.id)


@app.route("/api/project/interfaces", methods=["POST"])
def project_interfaces():
	# We need to query the project id first, then we need to get the project reference
	project = get_project_by_id(request.form["id"])

	if project == None:
		return ERROR_DIV.format("The project could not be found on the server.")

	mode = request.form["mode"]

	if mode == "add-access":
		return project.add_access_interface(request.form["parent"])
	elif mode == "add-vlan":
		return project.add_vlan_interface(request.form["parent"], request.form["vlan"])
	elif mode == "get":
		return project.generate_interfaces_html()
	elif mode == "update":
		return project.update_interface_information(request.form["ifid"], request.form["value"], request.form["field"])
	elif mode == "available":
		return project.generate_available_interfaces_html()
	elif mode == "delete":
		return project.remove_interface(request.form["ifid"])

@app.route("/api/project/streams", methods=["POST"])
def project_streams():
	# We need to query the project id first, then we need to get the project reference
	project = get_project_by_id(request.form["id"])

	if project == None:
		return ERROR_DIV.format("The project could not be found on the server.")

	mode = request.form["mode"]

	if mode == "get-streams":
		return project.generate_streams_html()
	elif mode == "get-attributes":
		return project.get_stream_attributes(request.form["stream"])
	elif mode == "add-attribute":
		return project.add_stream_attribute(request.form["stream"], request.form["attribute"])
	elif mode == "set-attribute":
		return project.set_stream_attribute(request.form["stream"], request.form["attribute"], request.form["value"])
	elif mode == "delete":
		return project.delete_stream(request.form["stream"])
	elif mode == "add":
		return project.add_stream(request.form["name"])
	elif mode == "set-state":
		return project.stream_state_change(request.form["stream"], request.form["state"])
	elif mode == "delete-attribute":
		return project.delete_stream_attribute(request.form["stream"], request.form["key"])

@app.route("/api/project/options", methods=["POST"])
def project_options():
	project = get_project_by_id(request.form["id"])

	if project == None:
		return ERROR_DIV.format("The project could not be found on the server.")

	mode = request.form["mode"]

	if mode == "get-options":
		return project.get_options()
	elif mode == "save":
		return project.save(SAVE_FOLDER)
	elif mode == "close":
		# The closing process means deleting the project from the PROJECTS Dict
		del PROJECTS[project.id]
		return "200"

@app.route("/api/project", methods=["POST"])
def project_endpoint():
	global PROJECTS
	# We need to query the project id first, then we need to get the project reference
	mode = request.form["mode"]

	project_entry = None

	if "id" in request.form:
		project_entry = get_project_by_id(request.form["id"])

	if project_entry == None:
		if mode == "create":
			name = request.form["name"]

			new = project.Project(name)
			PROJECTS[new.id] = new
			new.save(SAVE_FOLDER)

			return new.id
		else:
			return ERROR_DIV.format("The project could not be found on the server.")

	
	if mode == "json":
		return project_entry.json()


@app.route("/projects/<project_id>", methods=["GET","POST"])
def project_view(project_id):
	global PROJECTS
	# The user opened a specific project id.

	# This is the project instance, we are going to use for this call
	project_entity = get_project_by_id(project_id)

	# If it equals None, and no project is open, we will try to load the json for this project. If this is not possible, we return an error

	if project_entity == None:
		if len(PROJECTS) == 0:
			# Trying to open the files
			if os.path.isfile(SAVE_FOLDER + project_id + ".json") and os.path.isfile(SAVE_FOLDER + project_id + "_meta.json"):
				# We load the meta file and extract the name for the project. We then set the ID
				with open(SAVE_FOLDER + project_id + "_meta.json", "r") as f:
					meta = json.loads(f.read())

				with open(SAVE_FOLDER + project_id + ".json", "r") as f:
					obj = json.loads(f.read())

				new = project.Project(meta["name"], project_id)
				new.apply_settings(SETTINGS)
				new.load_json(obj)
				print(new.json(True))
				PROJECTS[project_id] = new
				project_entity = get_project_by_id(project_id)
			else:
				return render_template("project_not_found.html", location=LOCATION_PROJECT)
		else:
			# we query data from the currently open project:
			for key in PROJECTS.keys():
				open_project = PROJECTS[key]
			return render_template("other_project_open.html", location=LOCATION_PROJECT, project={"name": open_project.name, "id": open_project.id})

	# Now we found our project and have to interpret, what we should do. If the page was loaded via a GET, we reply with the project page
	if request.method == "GET":
		return render_template("project.html", project=project_entity.get_template_data(), location=LOCATION_PROJECT)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory("static", 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/")
def home():
	# We generate an json object which holds all projects and which state they are in. With this information, the template renders a table
	# We read all files from saves
	files = os.listdir(SAVE_FOLDER)
	all_projects = []

	for file in files:
		# We check the filename, if it contains "_meta". If yes, we check if the file with the id only exists.
		if "_meta" in file:
			file_id = file.replace("_meta", "")

			if file_id in files:
				# We have the metadata and file itself. Now we check if we have the project open
				project_open = False
				project_running = False
				if file_id.split(".")[0] in PROJECTS:
					# this project is currently opened
					project_open = True

				# We also check if the project is running via the blaster.py file
				project_running = blaster.check_project_running(file_id.split(".")[0])

				# Now we generate an entry for the table
				with open(SAVE_FOLDER + file, "r") as f:
					file_data = json.loads(f.read())

				all_projects.append({"name": file_data["name"], "id": file_data["id"], "open": project_open, "running": project_running})
	print(all_projects)

	return render_template("home.html", location=LOCATION_HOME, projects=all_projects)

@app.route("/create")
def create():
	return render_template("create.html", location=LOCATION_CREATE)

@app.route("/settings")
def settings():
	return render_template("settings.html", location=LOCATION_SETTINGS)

if __name__ == "__main__":
	app.run(debug=True)