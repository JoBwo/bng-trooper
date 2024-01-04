import uuid
import json
import copy
import ipaddress

class Access:

	# We define the fields the same way as in stream.Stream, but dont define any required fields but rather templates/rules, that comprise of different fields
	ATTRIBUTES = {
		"outer-vlan-min": {"name": "outer-vlan-min", "type": "integer", "default": 0, "range": "0-4095", "range-include": True, "description": "Outer VLAN minimum value."},
		"outer-vlan-max": {"name": "outer-vlan-max", "type": "integer", "default": 0, "range": "0-4095", "range-include": True, "description": "Outer VLAN maximum value."},
		"outer-vlan-step": {"name": "outer-vlan-step", "type": "integer", "default": 1, "range": "0-4095", "range-include": False, "description": "Outer VLAN step (iterator)."},
		"outer-vlan": {"name": "outer-vlan", "type": "integer", "range": "1-4095", "range-include": True, "description": "Set outer-vlan-min/max equally."},

		"inner-vlan-min": {"name": "inner-vlan-min", "type": "integer", "default": 0, "range": "0-4095", "range-include": True, "description": "Inner VLAN minimum value."},
		"inner-vlan-max": {"name": "inner-vlan-max", "type": "integer", "default": 0, "range": "0-4095", "range-include": True, "description": "Inner VLAN maximum value."},
		"inner-vlan-step": {"name": "inner-vlan-step", "type": "integer", "default": 1, "range": "0-4095", "range-include": False, "description": "Inner VLAN step (iterator)."},
		"inner-vlan": {"name": "inner-vlan", "type": "integer", "range": "1-4095", "range-include": True, "description": "Set inner-vlan-min/max equally."},

	}

	TEMPLATES = {
		"outer-vlan-range": {"name": "VLAN range as outer VLAN", "description": "Specify that the outer VLAN should count up between two boundary VLAN IDs", "attributes": ["outer-vlan-min", "outer-vlan-max", "outer-vlan-step"], "conflicting": ["outer-vlan"]},
		"outer-vlan-static": {"name": "Static VLAN as outer VLAN", "description": "Specify that the outer VLAN should be a static value", "attributes": ["outer-vlan"], "conflicting": ["outer-vlan-min", "outer-vlan-max", "outer-vlan-step"]}

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
					print("Remoing {}".format(attribute))
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

				conflicts = []

				# We now check the attributes list, if there is an attribute which conflicts with the template
				for attr in temp["conflicting"]:
					if attr in self.attributes:
						conflicts.append(attr)

				conflcit_span = """<span class="{}">{}</span>""".format("w3-text-orange" if len(conflicts) > 0 else "", ", ".join(conflicts) if len(conflicts) > 0 else "None")

				card = """
					<div class="w3-third">
						<div class="w3-card w3-margin w3-padding">
							<h4>{0}</h4>
							<h5>Description:</h5>
							{1}<br>
							<h5>Conflicting Attributes:</h5>
							{2}<br>
							<button class="w3-margin-top w3-green w3-button" onclick="addAccessTemplate('{3}', '{4}')">Add Template</button>
						</div>
					</div>
				""".format(temp["name"], temp["description"], conflcit_span, template, self.id)

				if counter == 0:
					html = html + "<div class='w3-row'>" + card

				counter = counter + 1

				if counter == 2:
					html = html + card + "</div>"
					counter = 0

		html = html + "<b>Please note</b> that in case there are conflicting attributes, they will automatically be deleted"

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

		table = """<div class="w3-padding"><table class="w3-table">"""

		for key in self.templates.keys():
			# For each template, we display the fields grouped together so that the user can see, why each value is beeing selected
			template = self.templates[key]

			# We add a header Row
			section = """<tr><td colspan="2"><b>{}</b></td></tr>""".format(template["name"])

			# Now we go through the attributes
			for attribute in template["attributes"]:
				if not attribute in self.attributes:
					section = section + "<tr><td colspan='2' class='w3-red w3-margin w3-round'>The attribute <code>'{}'</code> is missing for this template. It most likely got removed by another template. Please delete the template and re-add if necessary.</td></tr>".format(attribute)
				else:
					section = section + """
										<tr>
											<td>{0}</td>
											<td>{1}</td>
										</tr>
									""".format(self.attributes[attribute]["name"], self.attributes[attribute]["value"])

			section = section + "<tr><td><button class='w3-orange w3-button' onclick=\"deleteAccessTemplate('{}', '{}')\">Delete Template</button></td><td></td></tr>".format(self.id, key)

			table = table + section

		table = table + "</table></div>"

		buttons = """
					<button class="w3-green w3-button" onclick="showAddAccessTemplate('{}')">Add Template</button>
				""".format(self.id)

		return header + table + buttons + "</div></div>"


	def __str__(self):
		return "Interface for {} on parent interface {}".format(self.attributes["type"], self.attributes["interface"])