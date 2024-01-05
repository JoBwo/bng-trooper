import uuid
import json
import copy
import ipaddress

class Access:

	# We define the fields the same way as in stream.Stream, but dont define any required fields but rather templates/rules, that comprise of different fields
	ATTRIBUTES = {
		"outer-vlan-min": {"name": "outer-vlan-min", "type": "integer", "default": 0, "range": "0-4095", "range-include": True, "description": "Outer VLAN minimum value."},
		"outer-vlan-max": {"name": "outer-vlan-max", "type": "integer", "default": 0, "range": "0-4095", "range-include": True, "description": "Outer VLAN maximum value."},
		"outer-vlan-step": {"name": "outer-vlan-step", "type": "integer", "default": 1, "range": "0-4095", "range-include": False, "description": "Outer VLAN step (iterator). Please don't choose something silly, checking this programatically would cost my nerves."},
		"outer-vlan": {"name": "outer-vlan", "type": "integer", "range": "1-4095", "range-include": True, "description": "Set outer-vlan-min/max equally."},

		"inner-vlan-min": {"name": "inner-vlan-min", "type": "integer", "default": 0, "range": "0-4095", "range-include": True, "description": "Inner VLAN minimum value."},
		"inner-vlan-max": {"name": "inner-vlan-max", "type": "integer", "default": 0, "range": "0-4095", "range-include": True, "description": "Inner VLAN maximum value."},
		"inner-vlan-step": {"name": "inner-vlan-step", "type": "integer", "default": 1, "range": "0-4095", "range-include": False, "description": "Inner VLAN step (iterator). Please don't choose something silly, checking this programatically would cost my nerves."},
		"inner-vlan": {"name": "inner-vlan", "type": "integer", "range": "1-4095", "range-include": True, "description": "Set inner-vlan-min/max equally."},

		"third-vlan": {"name": "third-vlan", "type": "integer", "default": 0, "range": "1-4095", "range-include": True, "description": "Add a static third VLAN (most inner VLAN)."},

		"vlan-mode": {"name": "vlan-mode", "type": "select","values": [{"value": "1:1", "nice": "1:1"},
																		{"value": "N:1", "nice": "N:1"}], "default": "1:1", "description": "Set VLAN mode to 1:1 or N:1."},

		"ipv4": {"name": "ipv4", "type": "select", "values": [{"value": "true", "nice": "True"},
																	{"value": "false", "nice": "False"}], "default": "true", "description": "Set false to deactivate IPv4."},
		"ipv6": {"name": "ipv6", "type": "select", "values": [{"value": "true", "nice": "True"},
																	{"value": "false", "nice": "False"}], "default": "true", "description": "Set false to deactivate IPv6."},

		"address": {"name": "address", "type": "ipv4", "description": "Static IPv4 base address."},
		"address-iter": {"name": "address-iter", "type": "ipv4", "description": "Static IPv4 base address iterator."},
		"gateway": {"name": "gateway", "type": "ipv4", "description": "Static IPv4 gateway address."},
		"gateway-iter": {"name": "gateway-iter", "type": "ipv4", "description": "Static IPv4 gateway address iterator."},

		"username": {"name": "username", "type": "string", "description": "Overwrite the username from the authentication section."},
		"password": {"name": "password", "type": "string", "description": "Overwrite the password from the authentication section."},
		"authentication-protocol": {"name": "authentication-protocol", "type": "select", "values": [{"value": "PAP", "nice": "PAP"},
																									{"value": "CHAP", "nice": "CHAP"}], "default": "PAP", "description": "Overwrite the authentication-protocol from the authentication section."},
	}

	TEMPLATES = {
		"outer-vlan-range": {"name": "VLAN range as outer VLAN", "description": "Specify that the outer VLAN should count up between two boundary VLAN IDs", "attributes": ["outer-vlan-min", "outer-vlan-max", "outer-vlan-step"], "conflicting": ["outer-vlan"], "required": [], "type": ""},
		"outer-vlan-static": {"name": "Static VLAN as outer VLAN", "description": "Specify that the outer VLAN should be a static value", "attributes": ["outer-vlan"], "conflicting": ["outer-vlan-min", "outer-vlan-max", "outer-vlan-step"], "required": [], "type": ""},

		"inner-vlan-range": {"name": "VLAN range as inner VLAN", "description": "Specify that the inner VLAN should count up between two boundary VLAN IDs", "attributes": ["inner-vlan-min", "inner-vlan-max", "inner-vlan-step"], "conflicting": ["inner-vlan"], "required": ["outer-vlan-range", "outer-vlan-static"], "type": ""},
		"inner-vlan-static": {"name": "Static VLAN as inner VLAN", "description": "Specify that the inner VLAN should be a static value", "attributes": ["inner-vlan"], "conflicting": ["inner-vlan-min", "inner-vlan-max", "inner-vlan-step"], "required": ["outer-vlan-range", "outer-vlan-static"], "type": ""},

		"third-vlan-static": {"name": "Static third VLAN", "description": "Specify a static VLAN ID for the third (innermost) VLAN", "attributes": ["third-vlan"], "conflicting": [], "required": ["inner-vlan-range", "inner-vlan-static"], "type": ""},

		"vlan-mode": {"name": "VLAN mode", "description": "Set VLAN mode to 1:1 or N:1", "attributes": ["vlan-mode"], "conflicting": [], "required": [], "type": ""},

		"ipv4": {"name": "IPv4 Support", "description": "Deactivate IPv4 (default is on).", "attributes": ["ipv4"], "conflicting": ["address", "address-iter", "gateway", "gateway-iter"], "required": [], "type": "ipoe"},

		"ipv6": {"name": "IPv6 Support", "description": "Deactivate IPv6 (default is on).", "attributes": ["ipv6"], "conflicting": [], "required": [], "type": "ipoe"},

		"ipv4-settings": {"name": "IPv4 Settings", "description": "Define how the IPv4 addresses and gateways should be set.", "attributes": ["address", "address-iter", "gateway", "gateway-iter"], "conflicting": ["ipv4", "ipv6"], "required": [], "type": "ipoe"},

		"static-user": {"name": "Static User Definition", "description": "Define a static user with authentication protocol. This will ignore the authentication section", "attributes": ["username", "password", "authentication-protocol"], "conflicting": [], "required": [], "type": "pppoe"}
	}


	# Access is comprised of two different Elements. First, there is the interface specification. Secondly, there is the protocol specification. When construction an Object of Class Access, you firstly define the interface itself

	def __init__(self, type, interface):
		self.id = str(uuid.uuid4()).split("-")[0]
		self.attributes = {}
		self.attributes["type"] = type
		self.attributes["interface"] = interface
		self.templates = {}


	def add_template(self, key):
		# In order to add the template, we first have to remove all conflicting attributes from the list. We then add the new ones in Place

		template = Access.TEMPLATES[key]
		self.templates[key] = template

		for conflict in template["conflicting"]:
			if conflict in self.attributes:
				del self.attributes[conflict]

		for new_attr in template["attributes"]:
			attribute = copy.deepcopy(Access.ATTRIBUTES[new_attr])

			if "default" in attribute:
				attribute["value"] = attribute["default"]
			else:
				attribute["value"] = ""

			self.attributes[new_attr] = attribute
		return "200"

	def remove_template(self, key):
		if key in self.templates:
			# We firstly remove the attributes

			for attribute in self.templates[key]["attributes"]:
				if attribute in self.attributes:
					del self.attributes[attribute]

			del self.templates[key]

			return "200"
		return "915"


	def generate_available_templates_html(self):
		# We generate a list of all templates, which are currently not owned by the instance. We also compute, which fields are going to get removed

		# Each Template will be an individual card

		html = """
				<div class="w3-modal-content w3-animate-top w3-padding w3-round">
					<p class="w3-center w3-hover-red w3-round bng-cursor" style="width: 100%" onclick="hideAddAccessTemplate()">Close</p>
					<h2>Use a template to add attributes to the protocol</h2>
				"""

		counter = 0

		for template in Access.TEMPLATES.keys():
			if not template in self.templates:
				# We generate the card:

				temp = Access.TEMPLATES[template]

				# The first thing we check is, if the specified access interface type prohibits this template

				if not temp["type"] == "" and not temp["type"] == self.attributes["type"]:
					continue

				conflicts = []

				# We now check the attributes list, if there is an attribute which conflicts with the template
				for attr in temp["conflicting"]:
					if attr in self.attributes:
						conflicts.append(attr)

				conflcit_span = """<span class="{}">{}</span>""".format("w3-text-orange" if len(conflicts) > 0 else "", ", ".join(conflicts) if len(conflicts) > 0 else "None")

				if temp["required"] == [] or set(temp["required"]).intersection(set(self.templates)):
					button = """<button class="w3-margin-top w3-green w3-button" onclick="addAccessTemplate('{}', '{}')">Add Template</button>""".format(template, self.id)
				else:
					button = "<span class=\"w3-text-orange\">To use this template, one of the following templates is required: {}</span>".format(", ".join(temp["required"]))

				card = """
					<div class="w3-third">
						<div class="w3-card w3-margin w3-padding">
							<h4>{0}</h4>
							<h5>Description:</h5>
							{1}<br>
							<h5>Conflicting Attributes:</h5>
							{2}<br>
							{3}
						</div>
					</div>
				""".format(temp["name"], temp["description"], conflcit_span, button)

				if counter == 0:
					html = html + "<div class='w3-row'>"

				counter = counter + 1
				html = html + card

				if counter == 3:
					html = html + "</div>"
					counter = 0

		html = html + "{}<b>Please note</b> that in case there are conflicting attributes, they will automatically be deleted.".format("</div>" if not counter == 0 else "") # Closing div, in case there are less than 3 cards in the last row

		return html + "</div>"


	def get_as_html(self):
		content = ""

		#### TBD: Fehlende Attrbiute weil durch neues Template entfernt

		# We generate the header for the interface with the interface and type values
		header = """
				<div class="w3-card w3-margin w3-padding">
					<h3>Interface Settings</h3>
					<div class="w3-padding">
						Parent Interface: <code>{1}</code><br>
						Protocol Type: <code>{0}</code>
					</div>
					""".format(self.attributes["type"], self.attributes["interface"])

		table = """<div class="w3-padding w3-card w3-responsive"><h4>Attributes</h4><table class="w3-table" style="table-layout: fixed">"""

		colored_row = True

		for key in self.templates.keys():
			# For each template, we display the fields grouped together so that the user can see, why each value is beeing selected
			template = self.templates[key]
			color_string = "class=\"w3-white\"" if colored_row else ""
			colored_row = not colored_row

			# We add a header Row
			section = """<tr {}><td colspan="2"><h5>{}</h5></td></tr>""".format(color_string, template["name"])

			# Now we go through the attributes
			for attribute in template["attributes"]:
				if not attribute in self.attributes:
					section = section + "<tr><td colspan='2' class='w3-red w3-margin w3-round'>The attribute <code>'{}'</code> is missing for this template. It most likely got removed by another template. Please delete the template and re-add if necessary.</td></tr>".format(attribute)
				else:
					attr = self.attributes[attribute]
					value = attr["value"]

					# We format an input field for the use case
					if attr["type"] == "integer":
						input_field = """<input type="text" class="w3-input" numeric value="{0}" placeholder="{3}" id="{1}_{2}" onfocusout="updateAccessAttributeValue('{1}_{2}')">""".format( value, self.id, attribute, attr["name"])
					elif attr["type"] == "ipv4" or attr["type"] == "ipv6":
						input_field = """<input type="text" class="w3-input" value="{0}" placeholder="{3}" id="{1}_{2}" onfocusout="updateAccessAttributeValue('{1}_{2}')">""".format( value, self.id, attribute, attr["name"])
					elif attr["type"] == "select":
						# We create the options first
						options = ""
						for option in attr["values"]:
							options = options + """<option value="{}" {}>{}</option>""".format(option["value"], ("selected" if value == option["value"] else ""), option["nice"])
						input_field = """
											<select class="w3-select" id="{1}_{2}" onfocusout="updateAccessAttributeValue('{1}_{2}')" value="{3}">
												{0}
											</select>
										""".format(options, self.id, attribute, value)
					else:
						input_field = """<input type="text" class="w3-input" value="{0}" placeholder="{3}" id="{1}_{2}" onfocusout="updateAccessAttributeValue('{1}_{2}')">""".format( value, self.id, attribute, attr["name"])


					default = "" if not "default" in attr else "<i>Default:</i> " + str(attr["default"])
					val_from_between = " Between " if not "range-include" in attr or not attr["range-include"] else " From "
					val_range ="" if not "range" in attr else " <i>Range:</i>" + val_from_between + attr["range"]


					section = section + """
										<tr {3}>
											<td {4}><h6>{0}</h6>{1}</td>
											<td>{2}</td>
										</tr>
									""".format(attribute, attr["description"] + "<br>" + default + val_range, input_field, color_string, "style=\"max-width: 600px;\"")

			section = section + "<tr {}><td><button class='w3-orange w3-button' onclick=\"deleteAccessTemplate('{}', '{}')\">Delete Template</button></td><td></td></tr>".format(color_string, self.id, key)

			table = table + section

		table = table + "</table></div>"

		buttons = """
					<button class="w3-green w3-button w3-margin-top" onclick="showAddAccessTemplate('{}')">Add Template</button>
				""".format(self.id)

		return header + table + buttons + "</div></div>"


	def set_attribute_value(self, attribute, value):
		# We check if the attribute exists currently
		print(attribute)
		if not attribute in self.attributes:
			return "915"

		# We now save the value as the type it is (defaulting to string)
		if self.attributes[attribute]["type"] == "integer":
			# We firstly need to check if the value is inside the boundaries of the range command (if set).
			if "range" in self.attributes[attribute]:
				ranges = self.attributes[attribute]["range"].split("-")
				# if the range-include is true, we add / substrac 1 from the limits, else not
				range_include = 0 if not "range-include" in self.attributes[attribute] or not self.attributes[attribute]["range-include"] else 1
				if not (int(value) > int(ranges[0]) - range_include and int(value) < int(ranges[1]) + range_include):
					# The value ist the wrong size
					return "916"

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
					return "917"
			except ValueError:
				return "917"
		else:
			self.attributes[attribute]["value"] = value

		return "200"


	def __str__(self):
		return "Interface for {} on parent interface {}".format(self.attributes["type"], self.attributes["interface"])

	def json_interface(self):
		interface = {}
		for key in self.attributes.keys():
			if key in ["interface", "type"]:
				interface[key] = self.attributes[key]
				continue

			# We check if the value field is empty. If yes and there is no data in the default field, we ignore the attribute
			if not "value" in self.attributes[key] or self.attributes[key] == "":
				if "default" in self.attributes[key]:
					interface[key] = self.attributes[key]["default"]
			else:
				interface[key] = self.attributes[key]["value"]

			# We now do some type checking
			if interface[key] == "false" or interface[key] == "true":
				interface[key] = bool(interface[key])

		return interface