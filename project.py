import uuid
import json
import copy
import ipaddress
from interface import Interface
from stream import Stream
from access import Access

class Project():

	def __init__(self, name, id = ""):
		#self.id = str(uuid.uuid4())
		self.id = str(uuid.uuid4()) if id == "" else id
		self.name = name
		self.interfaces = []
		self.streams = []
		self.parent_interfaces = []
		self.access = []

	def apply_settings(self, settings):
		# Setting the available interface types:
		for interface in settings["interfaces"]:
			self.parent_interfaces.append({"name": interface, "type": "", "used": False, "used-vlans": []})

		self.parent_interfaces_orig = copy.deepcopy(self.parent_interfaces)

	def get_template_data(self):
		data = {
			"id": self.id,
			"name": self.name
		}

		return data

	def generate_interfaces_html(self):
		html = ""
		for interface in self.interfaces:
			html = html + interface.get_as_html()

		return html

	def generate_streams_html(self):
		html = ""
		for stream in self.streams:
			html = html + stream.get_as_html()

		return html

	def update_stream_interfaces_after(self):
		interfaces = []
		for interface in self.interfaces:
			interfaces.append({"value": interface.get_interface_name(), "nice": interface.get_interface_name()})

		for stream in self.streams:
			stream.update_interface_information(interfaces)

	def add_access_interface(self, parent):
		# We firstly need to check, if the parent interface is available for this application
		for interface in self.parent_interfaces:
			if interface["name"] == parent and interface["used"] == False and interface["type"] == "":
				self.interfaces.append(Interface(parent, 0))
				interface["used"] = True
				interface["type"] = "access"
				self.update_stream_interfaces_after()
				return "200"
		return "902"

	def add_vlan_interface(self, parent, vlan):
		for interface in self.parent_interfaces:
			if interface["name"] == parent and interface["used"] == False and interface["type"] == "":
				# This is the simplest, we do not need to make any vlan checking.
				self.interfaces.append(Interface(parent, int(vlan)))
				interface["used"] = True
				interface["type"] = "trunk"
				interface["used-vlans"] = [int(vlan)]

				self.update_stream_interfaces_after()
				return "200"
			elif interface["name"] == parent and interface["type"] == "trunk":
				# The interface already gets used as a trunk, so we need to make sure, there is no duplicate vlan id
				if int(vlan) in interface["used-vlans"]:
					# Duplicate
					return "901"

				self.interfaces.append(Interface(parent, int(vlan)))
				interface["used-vlans"].append(int(vlan))
				self.update_stream_interfaces_after()
				return "200"
		return "902"

	def remove_interface(self, ifid):
		# we need to get the index
		found = False
		for i,interface in enumerate(self.interfaces):
			if interface.id == ifid:
				found = True
				break

		if not found:
			return "910"

		# We need to adjust the parent_interfaces

		if ":" in interface.get_interface_name():
			# We need to adjust the vlan count. If it now is 0, we reset the type and the used value
			parts = interface.get_interface_name().split(":")
			name = parts[0]
			vlan = int(parts[1])

			for parent_interface in self.parent_interfaces:
				if parent_interface["name"] == name:
					# Check the len of the vlans attribute
					if len(parent_interface["used-vlans"]) == 1:
						parent_interface["used-vlans"] = []
						parent_interface["used"] = False
						parent_interface["type"] = ""
					else:
						# We remove the vlan from the list
						parent_interface["used-vlans"].remove(vlan)
		else:
			for parent_interface in self.parent_interfaces:
				if parent_interface["name"] == interface.get_interface_name():
					parent_interface["used"] = False
					parent_interface["type"] = ""


		del self.interfaces[i]

		self.update_stream_interfaces_after()
		return "200"

	def update_interface_information(self, ifid, value, field):
		for interface in self.interfaces:
			if interface.id == ifid:
				return interface.update_value(field, value)
		return "999"

	def generate_available_interfaces_html(self):
		# When this function gets called, we want to present the user with the list of available interfaces and what type they area
		result = ""
		i = -1
		for interface in self.parent_interfaces:
			# First, we need to check, wether this interface is used as a trunk or access port and wether or not it is available
			if interface["used"] == True and interface["type"] in ["access", "access-protocol"]:
				continue

			i = i + 1

			uid = str(uuid.uuid4()).split("-")[0]

			# We define the contents based on the type

			if interface["type"] == "trunk":
				# We present the user with an option to add a new vlan to this interface only
				description = "Used as a trunk Port, you can add a new VLAN"
				actions = """
							<input type="text" class="w3-input w3-light-gray" numeric pattern="([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-4][0][0-9][0-5])" id="{1}_vlan" style="width: 100%">
							<button class="w3-button w3-green" onclick="addNewVLANInterface('{0}', '{1}_vlan')" style="width: 100%">Add new VLAN</button>
						""".format(interface["name"], uid)
			elif interface["type"] == "":
				# If this interface is not used and not an trunk interface, this value must be empty. We present the user the option to either declare it as an Trunk interface or an Access Interface
				description = "Unused. You can either define it as an access port or as a trunk port with a VLAN"
				actions = """
						
							<button class="w3-button w3-green" onclick="addNewAccessInterface('{0}')" style="width: 100%">Define as Access</button><br>
							<p style="width: 100%" class="w3-center w3-margin-top w3-margin-bottom">- or -</p>
							<input type="text" class="w3-input w3-center w3-light-gray" placeholder="VLAN-ID" numeric pattern="([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-4][0][0-9][0-5])" id="{1}_vlan" style="width: 100%">
							<button class="w3-button w3-green" onclick="addNewVLANInterface('{0}', '{1}_vlan')" style="width: 100%">Define as Trunk</button>
						""".format(interface["name"], uid)

			# We check if this is the beginning of a row to add an opening tag
			if i % 3 == 0:
				result = result + "<div class=\"w3-row\">"


			# We define the card with the results from earlier
			result = result + """
				<div class=\"w3-third interface\">
					<div class=\"w3-card {0} w3-margin w3-padding\">
						<h4 class="bng-cursor" onclick=\"toggleCards('{2}_add_details')\">Interface {1}</h4>
						{3}
						<div class="w3-container w3-hide add-interface-details w3-padding-small" id="{2}_add_details">
							<div class="w3-container">
								{4}
							</div>
						</div>
					</div>
				</div>
				""".format(("w3-pale-green" if interface["type"] == "" else "w3-pale-yellow"), interface["name"], uid, description, actions)

			# We check if this is the end of a row to add an closing tag (or if it is the last element)
			if i % 3 == 2 or i == len(self.parent_interfaces) - 1:
				result = result + "</div>"

		if result == "":
			result = """
						<div class="w3-orange w3-round w3-padding">
							There are no interfaces left on the BNG Blaster that can be used.
						</div>
					"""		

		result = """
			<div class="w3-modal-content w3-animate-top w3-padding w3-round">
				<p class="w3-center w3-hover-red w3-round bng-cursor" style="width: 100%" onclick="hideAddInterface()">Close</p>
				<h2>Add Interface to project</h2>
			""" + result + "</div>"

		return result

	def generate_interfaces_for_access_html(self):
		# This function generates the HTML for the interfaces, which can be used for access protocols. In order to be availble, the same criteria as for a access interface is needed:
		listing = ""

		for interface in self.parent_interfaces:
			if interface["used"] == True and interface["type"] == "access":
				continue

			if interface["used"] == False and interface["type"] == "":
				listing = listing + """<option value="{0}">{0}</option>""".format(interface["name"])

		html = """ 
				<h3>Protocol</h3>
				<select id="access-type-select" class="w3-select">
					<option value="ipoe">IPoE</option>
					<option value="pppoe">PPPoE</option>
				</select>
				<h3>Interface</h3>
				<select id="access-interface-select" class="w3-select">
					{}
				</select>
				""".format(listing)

		return html

	def add_access_protocol(self, ifname, type):
		# We firstly need to check, that the interface is still available and even exists
		for interface in self.parent_interfaces:
			if not interface["name"] == ifname:
				continue

			if not interface["type"] == "" or interface["used"]:
				# The interface was specified with a different type
				return "913"

			# We reserve the interface
			interface["used"] = True
			interface["type"] = "access-protocol"
			self.access.append(Access(type, ifname))
			return "200"

		return "912"

	def generate_access_list_html(self):
		html = ""
		for access in self.access:
			html = html + access.get_as_html()
		return html

	def generate_access_template_html(self, access_id):
		for access in self.access:
			if access.id == access_id:
				return access.generate_available_templates_html()

		return "914"

	def add_access_template(self, access_id, template):
		for access in self.access:
			if access.id == access_id:
				return access.add_template(template)

		return "914"

	def remove_access_template(self, access_id, template):
		for access in self.access:
			if access.id == access_id:
				return access.remove_template(template)

		return "914"


	def delete_stream(self, stream_id):
		for i in range(len(self.streams)):
			if self.streams[i].id == stream_id:
				del self.streams[i]
				return "200"

	def add_stream(self, name):
		# We need to check if a stream exists with this name. Else, we create it
		for stream in self.streams:
			if stream.name == name:
				return "906"

		# We create the Stream
		self.streams.append(Stream(name))
		self.update_stream_interfaces_after()
		return "200"

	def get_stream_attributes(self, stream_id):
		for stream in self.streams:
			if stream.id == stream_id:
				return stream.generate_available_attributes_html()

	def add_stream_attribute(self, stream_id, attribute):
		for stream in self.streams:
			if stream.id == stream_id:
				return stream.add_attribute(attribute)

	def delete_stream_attribute(self, stream_id, attribute):
		for stream in self.streams:
				if stream.id == stream_id:
					return stream.delete_attribute(attribute)

	def set_stream_attribute(self, stream_id, attribute, value):
		for stream in self.streams:
			if stream.id == stream_id:
				return stream.set_attribute_value(attribute, value)

	def stream_state_change(self, stream_id, state):
		for stream in self.streams:
			if stream.id == stream_id:
				stream.active = bool(int(state))
				return "200"

		return "907"


	def json(self, stringify = True):
		# We generate the json datastructure for the project
		project = {}

		# Generating the interfaces
		interfaces = {"network": []}
		streams = []
		# Interfaces refers to network interfaces only
		for interface in self.interfaces:
			interfaces["network"].append(interface.json())

		for stream in self.streams:
			if stream.active:
				streams.append(stream.json())

		project["interfaces"] = interfaces
		project["streams"] = streams

		return json.dumps(project, indent = 4) if stringify else project

	def load_json(self, obj):
		# We take the attributes for network interfaces and streams, generate each entry and let the instance load its json by itself
		self.interfaces = []
		self.parent_interfaces = copy.deepcopy(self.parent_interfaces_orig)
		self.streams = []

		for interface in obj["interfaces"]["network"]:
			vlan = 0
			if "vlan" in interface:
				vlan = int(interface["vlan"])
			if vlan == 0:
				self.add_access_interface(interface["interface"])
			else:
				self.add_vlan_interface(interface["interface"], vlan)

			# Now we grab the interface and use the load_json() function
			name_added_one = interface["interface"] + "" if vlan == 0 else ":" + str(vlan)
			for interf in self.interfaces:
				if interf.get_interface_name() == name_added_one:
					interf.load_json(interface)

		for stream in obj["streams"]:
			name = stream["name"]
			t_stream = Stream(name)
			t_stream.load_json(stream)
			self.streams.append(t_stream)

		return "200"

	def save(self, path):
		file = path + self.id + ".json"
		meta_path = path + self.id + "_meta.json"

		meta = {"id": self.id, "name": self.name}

		with open(file, "w") as f:
			f.write(self.json())

		with open(meta_path, "w") as f:
			f.write(json.dumps(meta, indent=4))

		return "200"


	def get_options(self):
		html = """
			<p>
				The project on the server needs to be saved in order to persist it. Unless the project is closed or the server restarted, your changes are temporarily saved. If you do not want to save the current project state and revert to the original state, please close and reopen the project.<br>
				<button class="w3-button w3-green w3-margin" onclick="saveProject()">Save project</button>
			</p>
			<p>
				If you want to revert to your previous version or open another project, you have to close this project first.<br>
				<button class="w3-button w3-orange w3-margin" onclick="closeProject()">Close project</button>
			</p>
		"""

		return html
