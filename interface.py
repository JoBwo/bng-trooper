import uuid
import json
import copy
import ipaddress

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
