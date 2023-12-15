import uuid
import json
import copy
import ipaddress

class Project():

	def __init__(self, name, id = ""):
		#self.id = str(uuid.uuid4())
		self.id = str(uuid.uuid4()) if id == "" else id
		self.name = name
		self.interfaces = []
		self.streams = []
		self.parent_interfaces = []

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
		result = """
				<div class="w3-modal-content w3-animate-top w3-padding w3-round">
					<p class="w3-center w3-hover-red w3-round bng-cursor" style="width: 100%" onclick="hideAddInterface()">Close</p>
					<h2>Add Interface to project</h2>
				"""
		i = -1
		for interface in self.parent_interfaces:
			# First, we need to check, wether this interface is used as a trunk or access port and wether or not it is available
			if interface["used"] == True and interface["type"] == "access":
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

		return result + "</div>"

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

class Interface():

	def __init__(self, parent, vlan):
		# These are the most common parameters, which will be available in the "basic tab"
		self.id = str(uuid.uuid4()).split("-")[0]
		self.values = {}
		self.values["interface"] = parent
		self.values["address"] = ""
		self.values["gateway"] = ""
		self.values["address-ipv6"] = ""
		self.values["gateway-ipv6"] = ""
		self.values["ipv6-router-advertisement"] = 1
		self.values["vlan"] = vlan
		self.value_keys = ["interface", "address", "gateway", "address-ipv6", "gateway-ipv6", "ipv6-router-advertisement", "vlan"]

	def update_value(self, field, value):
		if field in self.values:
			# We will need to do some type checking for specific values only, everything else gets treated as string
			if field == "vlan" or field == "ipv6_router_advertisement":
				value = int(value)

			self.values[field] = value
			return "200"

		return "900" # Error Code for Value not found

	def get_as_html(self):
		# We generate an html structure for this:
		if bool(self.values["ipv6-router-advertisement"]) == False:
			router_advertisement_values = "<option value=\"0\" selected>No</option><option value=\"1\">Yes</option>"
		else:
			router_advertisement_values = "<option value=\"0\">No</option><option value=\"1\" selected>Yes</option>"
		html = """
				<div class="w3-third interface">
					<div class="w3-card w3-margin w3-padding basic_settings">
						<h3>Basic Interface Settings:</h3>
						<table style="width: 100%">
							<tr>
								<td>Parent Interface:</td>
								<td><input type="text" class="w3-input interface" disabled value="{1}"></td>
							</tr>
							<tr>
								<td>VLAN ID:</td>
								<td><input type="text" numeric class="w3-input vlan" disabled value="{7}"><br></td>
							</tr>
							<tr>
								<td>Local IPv4 Address CIDR:</td>
								<td><input type="text" class="w3-input address" id="{0}_address" onfocusout="updateInterfaceValue('{0}_address')" pattern="^([0-9]{{1,3}}\.){{3}}[0-9]{{1,3}}(\/([0-9]|[1-2][0-9]|3[0-2]))$" value="{2}"></td>
							</tr>
							<tr>
								<td>Gateway IPv4 Address:</td>
								<td><input type="text" class="w3-input gateway" id="{0}_gateway" onfocusout="updateInterfaceValue('{0}_gateway')" pattern="^([0-9]{{1,3}}\.){{3}}[0-9]{{1,3}}" value="{3}"></td>
							</tr>
							<tr>
								<td>Local IPv6 Address:</td>
								<td><input type="text" class="w3-input address_ipv6" id="{0}_address-ipv6" onfocusout="updateInterfaceValue('{0}_address_ipv6')" pattern="^s*((([0-9A-Fa-f]{{1,4}}:){{7}}([0-9A-Fa-f]{{1,4}}|:))|(([0-9A-Fa-f]{{1,4}}:){{6}}(:[0-9A-Fa-f]{{1,4}}|((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}})|:))|(([0-9A-Fa-f]{{1,4}}:){{5}}(((:[0-9A-Fa-f]{{1,4}}){{1,2}})|:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}})|:))|(([0-9A-Fa-f]{{1,4}}:){{4}}(((:[0-9A-Fa-f]{{1,4}}){{1,3}})|((:[0-9A-Fa-f]{{1,4}})?:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:))|(([0-9A-Fa-f]{{1,4}}:){{3}}(((:[0-9A-Fa-f]{{1,4}}){{1,4}})|((:[0-9A-Fa-f]{{1,4}}){{0,2}}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:))|(([0-9A-Fa-f]{{1,4}}:){{2}}(((:[0-9A-Fa-f]{{1,4}}){{1,5}})|((:[0-9A-Fa-f]{{1,4}}){{0,3}}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:))|(([0-9A-Fa-f]{{1,4}}:){{1}}(((:[0-9A-Fa-f]{{1,4}}){{1,6}})|((:[0-9A-Fa-f]{{1,4}}){{0,4}}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:))|(:(((:[0-9A-Fa-f]{{1,4}}){{1,7}})|((:[0-9A-Fa-f]{{1,4}}){{0,5}}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:)))(%.+)?s*(\/([0-9]|[1-9][0-9]|1[0-1][0-9]|12[0-8]))?$" value="{4}"></td>
							</tr>
							<tr>
								<td>Gateway IPv6 Address:</td>
								<td><input type="text" class="w3-input gateway_ipv6" id="{0}_gateway-ipv6" onfocusout="updateInterfaceValue('{0}_gateway_ipv6')" pattern="^s*((([0-9A-Fa-f]{{1,4}}:){{7}}([0-9A-Fa-f]{{1,4}}|:))|(([0-9A-Fa-f]{{1,4}}:){{6}}(:[0-9A-Fa-f]{{1,4}}|((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}})|:))|(([0-9A-Fa-f]{{1,4}}:){{5}}(((:[0-9A-Fa-f]{{1,4}}){{1,2}})|:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}})|:))|(([0-9A-Fa-f]{{1,4}}:){{4}}(((:[0-9A-Fa-f]{{1,4}}){{1,3}})|((:[0-9A-Fa-f]{{1,4}})?:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:))|(([0-9A-Fa-f]{{1,4}}:){{3}}(((:[0-9A-Fa-f]{{1,4}}){{1,4}})|((:[0-9A-Fa-f]{{1,4}}){{0,2}}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:))|(([0-9A-Fa-f]{{1,4}}:){{2}}(((:[0-9A-Fa-f]{{1,4}}){{1,5}})|((:[0-9A-Fa-f]{{1,4}}){{0,3}}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:))|(([0-9A-Fa-f]{{1,4}}:){{1}}(((:[0-9A-Fa-f]{{1,4}}){{1,6}})|((:[0-9A-Fa-f]{{1,4}}){{0,4}}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:))|(:(((:[0-9A-Fa-f]{{1,4}}){{1,7}})|((:[0-9A-Fa-f]{{1,4}}){{0,5}}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){{3}}))|:)))(%.+)?s*" value="{5}"></td>
							</tr>
							<tr>
								<td>Send v6 Router Advertisements:</td>
								<td>
									<select class="w3-select ipv6_router_advertisement" id="{0}_ipv6-router-advertisement" onfocusout="updateInterfaceValue('{0}_ipv6_router_advertisement')">
										{6}
									</select>
								</td>
							</tr>
							<tr>
								<td></td>
								<td>
									<button class="w3-button w3-red" onclick="deleteInterface('{0}')">Delete Interface</button>
								</td>
							</tr>
						</table>
					</div>
				</div>
		""".format(self.id, self.values["interface"], self.values["address"], self.values["gateway"], self.values["address-ipv6"], self.values["gateway-ipv6"], router_advertisement_values, self.values["vlan"])
		return html

	def get_interface_name(self):
		# If the vlan is not 0, we return name:vlan, else only name
		if self.values["vlan"] == 0:
			return self.values["interface"]

		return "{}:{}".format(self.values["interface"], str(self.values["vlan"]))

	def load_json(self, obj):
		# We iterate through the keys of the json and set our variables accordingly
		for key in obj.keys():
			self.values[key] = obj[key]

	def json(self):
		interface = {}
		for key in self.value_keys:
			# First, some special rules, then a default rule:
			if key == "vlan" and self.values[key] == 0:
				# Default VLAN is 0
				continue
			elif key == "ipv6-router-advertisement" and self.values[key] == 1:
				# RAs are active by default
				continue
			elif key == "ipv6-router-advertisement":
				interface[key] = bool(self.values[key])
			elif self.values[key] == "":
				# Default String empty Rule
				continue
			else:
				interface[key] = self.values[key]
		return interface

class Stream:

	# We need to do some constructing of attributes. Pattern will always be the same
	ATTRIBUTES = {
		"stream-group-id": {"name": "stream-group-id", "type": "integer", "default": 0, "required": False, "description": "Stream group identifier."},
		"type": {"name": "type", "type": "select", "values": [{"value": "ipv4", "nice": "IPv4"},
																{"value": "ipv6", "nice": "IPv6"},
																{"value": "ipv6pd", "nice": "IPv6 Prefix Delegation"}], "default": "ipv4", "required": True, "description": "Mandatory stream type"},
		"direction": {"name": "direction", "type": "select", "values": [{"value": "upstream", "nice": "Upstream"},
																		{"value": "downstream", "nice": "Downstream"},
																		{"value": "both", "nice": "Both"}], "default": "both", "required": False, "description": "Stream direction"},
		"source-port": {"name": "source-port", "type": "integer", "default": 65056, "range": "0-65535", "required": False, "description": "Overwrite the default source port."},
		"destination-port": {"name": "destination-port", "type": "integer", "default": 65056, "range": "0-65535", "required": False, "description": "Overwrite the default destination port."},
		"network-interface": {"name": "network-interface", "type": "select", "values": [], "required": False, "description": "Select the corresponding network interface for this stream."},
		"ipv4-df": {"name": "ipv4-df", "type": "select", "values": [{"value": "true", "nice": "True"},
																	{"value": "false", "nice": "False"}], "default": "true", "required": False, "description": "Set IPv4 DF bit."},
		"priority": {"name": "priority", "type": "integer", "default": 0, "range": "0-255", "range-include": True, "required": False, "description": "IPv4 TOS / IPv6 TC. For L2TP downstream traffic, the IPv4 TOS is applied to the outer IPv4 and inner IPv4 header."},
		"vlan-priority": {"name": "vlan-priority", "type": "integer", "default": 0, "range": "0-7", "range-include": True, "required": False, "description": "VLAN priority."},
		"length": {"name": "length", "type": "integer", "default": 128, "range": "76-9000", "range-include": True, "required": False, "description": "Layer 3 (IP header + payload) traffic length."},
		"pps": {"name": "pps", "type": "integer", "default": 1, "required": False, "description": "Stream traffic rate in packets per second."},
		"network-ipv4-address": {"name": "network-ipv4-address", "type": "ipv4", "required": False, "description": "Overwrite network interface IPv4 address."},
		"network-ipv6-address": {"name": "network-ipv6-address", "type": "ipv6", "required": False, "description": "Overwrite network interface IPv6 address."},
		"destination-ipv4-address": {"name": "destination-ipv4-address", "type": "ipv4", "required": False, "description": "Overwrite the IPv4 destination address."},
		"destination-ipv6-address": {"name": "destination-ipv6-address", "type": "ipv6", "required": False, "description": "Overwrite the IPv6 destination address."},
		#"priority": {"name": "", "type": "", "default": "", "required": False, "description": ""},
	}

	def __init__(self, name):
		self.id = str(uuid.uuid4()).split("-")[0]
		self.name = name
		self.values = {}
		self.attributes = {}
		self.active = True
		self.interface_list = []

		# We now coppy all required attributes in our self.attributes list
		for key in Stream.ATTRIBUTES.keys():
			if Stream.ATTRIBUTES[key]["required"]:
				self.attributes[key] = copy.deepcopy(Stream.ATTRIBUTES[key])

	def update_interface_information(self, list):
		# We set a special attribute in the stream, which contains a list of all interfaces. If the network-interface attribute got already added, we alter the select values
		self.interface_list = list

		if "network-interface" in self.attributes:
			self.attributes["network-interface"]["values"] = list

	def add_attribute(self, attribute):
		# This function adds an attribute from Stream.ATTRIBUTES to self.attributes without a value
		# We firstly need to check, if the attribute is already present:
		if attribute in self.attributes:
			return "903"

		# We then check, if this attribute even exists:
		if not attribute in Stream.ATTRIBUTES:
			return "904"

		# Now we create a copy from Stream.ATTRIBUTES
		self.attributes[attribute] = copy.deepcopy(Stream.ATTRIBUTES[attribute])
		# We set the interface_list if this ist the network-interface attribute
		if attribute == "network-interface":
			self.attributes[attribute]["values"] = self.interface_list

		return "200"

	def delete_attribute(self, attribute):
		del self.attributes[attribute]
		return "200"

	def set_attribute_value(self, attribute, value):
		# We check if the attribute exists currently
		if not attribute in self.attributes:
			return "905"

		# We now save the value as the type it is (defaulting to string)
		if self.attributes[attribute]["type"] == "integer":
			# We firstly need to check if the value is inside the boundaries of the range command (if set).
			if "range" in self.attributes[attribute]:
				ranges = self.attributes[attribute]["range"].split("-")
				# if the range-include is true, we add / substrac 1 from the limits, else not
				range_include = 0 if not "range-include" in self.attributes[attribute] or not self.attributes[attribute]["range-include"] else 1
				if not (int(value) > int(ranges[0]) - range_include and int(value) < int(ranges[1]) + range_include):
					# The value ist the wrong size
					return "908"

			self.attributes[attribute]["value"] = int(value)
		elif self.attributes[attribute]["type"] == "ipv4" or self.attributes[attribute]["type"] == "ipv6":
			# We check, if we have a valid ip address#
			try:
				ip = ipaddress.ip_address(value)
				# We check which version:
				if "ipv" + str(ip.version) == self.attributes[attribute]["type"]:
					self.attributes[attribute]["value"] = str(value)
					return "200"
				else:
					return "909"
			except ValueError:
				return "909"
		else:
			self.attributes[attribute]["value"] = value

		return "200"


	def get_as_html(self):
		# We create the attribute html and then put it in the stream header
		content = ""

		for key in self.attributes.keys():
			# We generate a table row with the individual input format for the attribute
			attr = self.attributes[key]

			# We define the current value
			if not "value" in attr:
				# We do not have a value and check, if there is a default one
				value = "" if not "default" in attr else attr["default"]
			else:
				# We set the value to the exact type
				value = attr["value"]

			if attr["type"] == "integer":
				#### TBD Range in pattern umwandeln
				input_field = """<input type="text" class="w3-input" numeric {0} value="{1}" id="{2}_{3}" onfocusout="updateAttributeValue('{2}_{3}')">""".format(("required" if attr["required"] else ""), value, self.id, key)
			elif attr["type"] == "ipv4" or attr["type"] == "ipv6":
				input_field = """<input type="text" class="w3-input" {0} value="{1}" id="{2}_{3}" onfocusout="updateAttributeValue('{2}_{3}')">""".format(("required" if attr["required"] else ""), value, self.id, key)
			elif attr["type"] == "select":
				# We create the options first
				options = ""
				for option in attr["values"]:
					options = options + """<option value="{}" {}>{}</option>""".format(option["value"], ("selected" if value == option["value"] else ""), option["nice"])
				input_field = """
									<select class="w3-select" id="{1}_{2}" onfocusout="updateAttributeValue('{1}_{2}')" {3} value="{4}">
										{0}
									</select>
								""".format(options, self.id, key, ("required" if attr["required"] else ""), value)


			# Now we create the table row
			default = "" if not "default" in attr else "<i>Default:</i> " + str(attr["default"])
			val_from_between = " Between " if not "range-include" in attr or not attr["range-include"] else " From "
			val_range ="" if not "range" in attr else " <i>Range:</i>" + val_from_between + attr["range"]

			content = content + """
								<tr>
									<td>
										<h4>{0}</h4>
										{1}
									</td>
									<td>
										{3}
									</td>
									<td>
										<button class="w3-button w3-red" onclick="removeAttributeFromStream('{2}', '{0}')">Remove</button>
									</td>
								</tr>
								""".format(key, attr["description"] + "<br>" + default + val_range, self.id, input_field)


		header = """
			<div class="w3-container">
				<div class="w3-card w3-margin w3-padding">
					<h3>{0}</h3>
						<table class="w3-margin-bottom" style="width: 100%">
							{1}
						</table>
					<button class="w3-button w3-green" onclick="showAddStreamAttribute('{2}')">Add Attribute</button>
					<button class="w3-button w3-orange" onclick="do{3}Stream('{2}')">{3} Stream</button>
					<button class="w3-button w3-red" onclick="showDeleteStream('{2}')">Delete Stream</button>
				</div>
			</div>
		""".format("Stream: " + self.name if self.active else "<del>Stream: " + self.name + "</del><ins>Deactivated</ins>", content, self.id, "Deactivate" if self.active else "Activate")

		return header

	def generate_available_attributes_html(self):
		# We compare the set attributes with the available ones and only return the card for the available ones
		html = ""
		for key in Stream.ATTRIBUTES.keys():
			if not key in self.attributes:
				# We add the attribute to the list
				attr = Stream.ATTRIBUTES[key]
				color = "w3-orange" if Stream.ATTRIBUTES[key]["required"] else ""
				html = html + """
					<div class="attribute bng-cursor {0} w3-hover-pale-green w3-padding w3-round" onclick="addStreamAttribute('{1}', '{2}')">
						<h4>{1}</h4>
						Description: {3}
					</div>
				""".format(color, key, self.id, Stream.ATTRIBUTES[key]["description"])

		attribute_list = """
				<div class="w3-modal-content w3-animate-top w3-padding w3-round">
					<p class="w3-center w3-hover-red w3-round bng-cursor" style="width: 100%" onclick="hideAddStreamAttribute()">Close</p>
					<h2>Add Attribute to Stream {}</h2>
					{}
				</div>
		""".format(self.name, html)

		return attribute_list

	def json(self):
		stream = {"name": self.name}
		for key in self.attributes.keys():
			# We check if the value field is empty. If yes and there is no data in the default field, we ignore the attribute
			if not "value" in self.attributes[key]:
				if "default" in self.attributes[key]:
					stream[key] = self.attributes[key]["default"]
			else:
				stream[key] = self.attributes[key]["value"]

			# We now do some type checking
			if stream[key] == "false" or stream[key] == "true":
				stream[key] = bool(stream[key])

		return stream

	def load_json(self, obj):
		for key in obj.keys():
			# Here, the story is a bit more easy, we just trigger the add_attribute and set_attribute functions
			self.add_attribute(key)
			self.set_attribute_value(key, obj[key])

