import uuid
import json
import copy
import ipaddress


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
