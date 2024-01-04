DIV_INTERFACE_LIST = document.getElementById("interface-list")
DIV_STREAM_LIST = document.getElementById("stream-list")
DIV_NEW_INTERFACE = document.getElementById("new-interface")
DIV_NEW_STREAM = document.getElementById("new-stream")
DIV_DELETE_STREAM = document.getElementById("delete-stream")
DIV_NEW_STREAM_ATTRIBUTE = document.getElementById("new-stream-attribute")
DIV_HEALTH_CHECK = document.getElementById("healthcheck-result")
DIV_CONTROL_BUTTONS = document.getElementById("control-buttons")
DIV_BLASTER_OUTPUT = document.getElementById("blaster-output")
DIV_DOWNLOAD_SERVER = document.getElementById("download-server")
DIV_OPTIONS_FIELD = document.getElementById("options-field")
DIV_CLOSE_PROJECT = document.getElementById("close-project")
TA_FORMATTED_TEXT = document.getElementById("formatted-json")
DIV_ERROR_LIST = document.getElementById("error-list")
DIV_NEW_ACCESS = document.getElementById("new-access")
DIV_NEW_ACCESS_SELECTS = document.getElementById("access-selects")
DIV_ACCESS_LIST = document.getElementById("access-list")
DIV_ADD_ACCESS_TEMPLATE = document.getElementById("access-templates")


let api = "/api/";
let current_stream_delete = "";

setTimeout(loadInterfaces, 100);

function toggleCards(id){
	var cards = document.getElementsByClassName("add-interface-details");
	for (var i = 0; i < cards.length; i++){
		cards.item(i).classList.add("w3-hide");
	}
	document.getElementById(id).classList.toggle("w3-hide")
}

function checkRegex(field, strict = false){
	if(document.getElementById(field).tagName.toLowerCase() == "select"){
		return true;
	}
	var pattern = document.getElementById(field).getAttribute("pattern");
	var data = document.getElementById(field).value;
	if (data == "" && !strict){
		return true;
	}else if (data == "" && strict){
		return false;
	}
	var re = new RegExp(pattern);
	return re.test(data);
}

function hideAddInterface(){
	DIV_NEW_INTERFACE.style.display = "none";
	loadInterfaces();
}

function hideAddStreamAttribute(){
	DIV_NEW_STREAM_ATTRIBUTE.style.display = "none";
	loadStreams();
}

function changePage(suffix){
	// This function removes the visibility for all subpages and sets it for the desired page
	var containers = document.getElementsByClassName("content-container");
	for (var i = 0; i < containers.length; i++){
		containers.item(i).classList.add("w3-hide");
	}
	var toggles = document.getElementsByClassName("content-toggle");
	for (var i = 0; i < toggles.length; i++){
		toggles.item(i).classList.remove("w3-green");
	}

	// Before hiding, we want to load the content
	if(suffix == "interfaces"){
		loadInterfaces();
	}else if(suffix == "streams"){
		loadStreams();
	}else if(suffix == "control"){
		loadControlButtons();
		loadLog();
	}else if(suffix == "output"){
		generateTextVersion();
	}else if(suffix == "options"){
		loadOptions();
	}else if(suffix == "access"){
		loadAccess();
	} 


	document.getElementById(suffix).classList.remove("w3-hide")
	document.getElementById("page-" + suffix).classList.add("w3-green")
}

function showAddInterfaceResult(text){
	DIV_NEW_INTERFACE.style.display = "block";
	DIV_NEW_INTERFACE.innerHTML = text
}

function showAddInterface(){
	// This Function toggels the visibility for the new-interface div and, prior to that, loads all available interfaces from the server

	fetch(api + "project/interfaces", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "available"})
	})
	   .then(response => response.text())
	   .then(response => showAddInterfaceResult(response))
	
}

function showAddStream(){
	DIV_NEW_STREAM.style.display = "block";
	document.getElementById("new-stream-name").value = ""
}

function hideAddStream(){
	DIV_NEW_STREAM.style.display = "none";
}

function hideDeleteStream(){
	current_stream_delete = "";
	DIV_DELETE_STREAM.style.display = "none";
}

function showDeleteStream(stream_id){
	current_stream_delete = stream_id;
	DIV_DELETE_STREAM.style.display = "block";
}

function showAddStreamAttributeResult(text){
	DIV_NEW_STREAM_ATTRIBUTE.style.display = "block";
	DIV_NEW_STREAM_ATTRIBUTE.innerHTML = text
}

function showAddStreamAttribute(stream_id){
	// This Function load the attributes that each stream can receive
	fetch(api + "project/streams", {
	    method: 'POST',
	    body: getFormData({id: project_id, stream: stream_id, mode: "get-attributes"})
	})
	   .then(response => response.text())
	   .then(response => showAddStreamAttributeResult(response))
}

function addNewStreamResult(response){
	if(response == "906"){
		placeMessage("Error", "The chosen name for the stream already exists. Please choose another name");
		return;
	}

	hideAddStream();
	loadStreams();
}

function hideAddAccess(){
	DIV_NEW_ACCESS.style.display = "none";
	DIV_NEW_ACCESS_SELECTS.innerHTML = "";
	loadAccess();
}

function showAddAccessResult(response){
	DIV_NEW_ACCESS.style.display = "block";
	DIV_NEW_ACCESS_SELECTS.innerHTML = response;
}

function showAddAccess(){
	// This Function loads the available Interfaces for Access Protocols and displays a context dialog for choosing the right combination
	fetch(api + "project/access", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "get-interfaces"})
	})
	   .then(response => response.text())
	   .then(response => showAddAccessResult(response))
}

function hideAddAccessTemplate(){
	DIV_ADD_ACCESS_TEMPLATE.style.display = "none";
	DIV_ADD_ACCESS_TEMPLATE.innerHTML = ""
}

function showAddAccessTemplateResult(response){
	if(response == "914"){
		placeMessage("Error", "The Access Protocol could not be found.")
		return;
	}
	DIV_ADD_ACCESS_TEMPLATE.style.display = "block";
	DIV_ADD_ACCESS_TEMPLATE.innerHTML = response
}

function showAddAccessTemplate(id){
	fetch(api + "project/access", {
	    method: 'POST',
	    body: getFormData({id: project_id, access_id: id, mode: "get-templates"})
	})
	   .then(response => response.text())
	   .then(response => showAddAccessTemplateResult(response))
}

function deleteAccessTemplateResult(response){
	if(response == "914"){
		placeMessage("Error", "The Access Protocol could not be found.")
	}else if(response == "915"){
		placeMessage("Error", "The Template could not be found.")
	}
	loadAccess();
}

function deleteAccessTemplate(access_id, template){
	fetch(api + "project/access", {
	    method: 'POST',
	    body: getFormData({id: project_id, access_id: access_id, mode: "remove-template", template: template})
	})
	   .then(response => response.text())
	   .then(response => deleteAccessTemplateResult(response))
}

function addAccessTemplateResult(response){
	// Error handling
	if(response == "914"){
		placeMessage("Error", "The Access Protocol could not be found.")
	}
	hideAddAccessTemplate()
	loadAccess();
}

function addAccessTemplate(template, access_id){
	fetch(api + "project/access", {
	    method: 'POST',
	    body: getFormData({id: project_id, access_id: access_id, mode: "add-template", template: template})
	})
	   .then(response => response.text())
	   .then(response => addAccessTemplateResult(response))
}

function addAccessResult(response){
	if(response == "912"){
		placeMessage("Error", "The interface could not be found.")
	}else if(response == "913"){
		placeMessage("Error", "The interface cannot be used for Access Protocols")
	}
	hideAddAccess();
	loadAccess();
}

function addAccess(){
	interface = document.getElementById("access-interface-select").value
	type = document.getElementById("access-type-select").value

	if(interface == ""){
		placeMessage("Error", "No Interface selected.")
		return;
	}else if(type == ""){
		placeMessage("Error", "No Type selected.")
		return;
	}

	fetch(api + "project/access", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "add-access", interface: interface, type: type})
	})
	   .then(response => response.text())
	   .then(response => addAccessResult(response))
}

function loadAccessResult(response){
	if(response == "911"){
		placeMessage("Error", "We could not load any Access Protocols.")
		return
	}

	DIV_ACCESS_LIST.innerHTML = response
}

function loadAccess(){
	// This Function loads all Access Components from the server and places them inside the container.
	fetch(api + "project/access", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "get-access"})
	})
	   .then(response => response.text())
	   .then(response => loadAccessResult(response))
}

function addNewStream(){
	// This Function creates a new stream and activates its helper function

	// First, it needs to check if the input is empty or not

	if (document.getElementById("new-stream-name").value == ""){
		placeMessage("Error", "You need to enter a name for the new stream");
		return;
	}

	fetch(api + "project/streams", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "add", name: document.getElementById("new-stream-name").value})
	})
	   .then(response => response.text())
	   .then(response => addNewStreamResult(response))
}

function addStreamAttributeResult(response, stream_id){
	// We return if we do not want to refresh the streams and close the modal
	if(response == "903"){
		placeMessage("Error", "The attribute already got added to the stream.");
		showAddStreamAttribute(stream_id);
		return;
	}else if (response == "904"){
		placeMessage("Error", "The attribute does not exist.")
		showAddStreamAttribute(stream_id);
		return;
	}

	hideAddStreamAttribute();
	loadStreams();
}

function addStreamAttribute(attribute, stream_id){
	// This Function sends a request to the server to add a new attribute to the stream. The Response Code is evaluated afterwards

	fetch(api + "project/streams", {
	    method: 'POST',
	    body: getFormData({id: project_id, stream: stream_id, mode: "add-attribute", attribute: attribute})
	})
	   .then(response => response.text())
	   .then(response => addStreamAttributeResult(response, stream_id))
}

function updateAttributeValueResult(response){
	if(response == "905"){
		placeMessage("Error", "The specified attribute does not exist for the stream");
	}else if(response == "908"){
		placeMessage("Error", "The specified value is outside the value boundaries.");
	}else if(response == "909"){
		placeMessage("Error", "The specified value is not a valid IP-Address for the field");
	}

	loadStreams();
}

function updateAttributeValue(field){
	let value = document.getElementById(field).value
	let parts = field.split("_");
	let stream_id = parts[0]
	let attribute = parts[1]

	fetch(api + "project/streams", {
	    method: 'POST',
	    body: getFormData({id: project_id, stream: stream_id, mode: "set-attribute", attribute: attribute, value: value})
	})
	   .then(response => response.text())
	   .then(response => updateAttributeValueResult(response))
}

function changeStreamActiveResult(respone){
	if(respone == "907"){
		placeMessage("Error", "The specified Stream does not exist")
		return;
	}

	loadStreams();
}

function changeStreamActive(id, mode){
	// This function sets the active state of the stream

	fetch(api + "project/streams", {
	    method: 'POST',
	    body: getFormData({id: project_id, stream: id, mode: "set-state", state: mode})
	})
	   .then(response => response.text())
	   .then(response => changeStreamActiveResult(response))
}

function doActivateStream(id){
	changeStreamActive(id, 1)
}

function doDeactivateStream(id){
	changeStreamActive(id, 0)
}

function removeStreamResult(respone){
	if(respone != "200"){
		placeMessage("Error", "Error during stream deletion");
		return;
	}
	loadStreams();
	hideDeleteStream();
	current_stream_delete = "";
}

function removeStream(){
	// This Function deletes a Stream from the project
	fetch(api + "project/streams", {
	    method: 'POST',
	    body: getFormData({id: project_id, stream: current_stream_delete, mode: "delete"})
	})
	   .then(response => response.text())
	   .then(response => removeStreamResult(response))
}

function removeAttributeFromStreamResult(respone){
	loadStreams();
}

function removeAttributeFromStream(stream_id, key){
	// This function removes attribute key from stream_id

	fetch(api + "project/streams", {
	    method: 'POST',
	    body: getFormData({id: project_id, stream: stream_id, mode: "delete-attribute", key: key})
	})
	   .then(response => response.text())
	   .then(response => removeAttributeFromStreamResult(response))
}	

function loadStreams(){
	fetch(api + "project/streams", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "get-streams"})
	})
	   .then(response => response.text())
	   .then(response => DIV_STREAM_LIST.innerHTML = response)
}


function loadInterfaces(){
	// This function loads all current interfaces as HTML an places them inside their respective Containers
	fetch(api + "project/interfaces", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "get"})
	})
	   .then(response => response.text())
	   .then(response => DIV_INTERFACE_LIST.innerHTML = response)
}

function addNewVLANInterfaceResult(response){
	if(response == "901"){
		// VLAN does already exist in the project
		placeMessage("Error", "The specified VLAN already exists. Please select another value")
	}else if(response == "902"){
		// VLAN does already exist in the project
		placeMessage("Error", "The specified interface was not available anymore.")
	}else{
		loadInterfaces();
		// We need to clean up and remove the add dialog
		DIV_NEW_INTERFACE.style.display = "none";
		DIV_NEW_INTERFACE.innerHTML = ""
	}
}


function addNewVLANInterface(name, vlan_interface){
	// This Function creates a new VLAN Interface based on the parent interface and VLAN information.
	// The server could reply with a message, that the vlan already exists. We need to check that.

	let value = document.getElementById(vlan_interface).value

	if(!checkRegex(vlan_interface, true)){
		// The Regex Check went wrong and the value is not acceptable. We print an error
		placeMessage("Error", "The value '" + value + "' is out of the acceptable VLAN range. Please correct");
		return;
	}

	fetch(api + "project/interfaces", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "add-vlan", parent: name, vlan: value})
	})
	   .then(response => response.text())
	   .then(response => addNewVLANInterfaceResult(response))
}


function addNewAccessInterfaceResult(respone){
	if(respone == "902"){
		placeMessage("Error", "The specified interface was not available anymore.")
	}else{
		loadInterfaces();
		// We need to clean up and remove the add dialog
		DIV_NEW_INTERFACE.style.display = "none";
		DIV_NEW_INTERFACE.innerHTML = ""
	}
}

function addNewAccessInterface(name){
	// This Function simply adds a new interface as an access interface

	fetch(api + "project/interfaces", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "add-access", parent: name})
	})
	   .then(response => response.text())
	   .then(response => addNewAccessInterfaceResult(response))
}

function updateInterfaceValueResult(result){
	if(result != "200"){
		placeMessage("Error", "Could not save value change to the server")
		loadInterfaces()
	}
}

function updateInterfaceValue(field){
	// This Function gets called everytime an interface fields loses focus in order to save the change to the server.
	// the answer will reload the interfaces, if not equal to 200 and display an error in the console

	// we generate the id, the field value and the field name
	parts = field.split("_", 1)
	id = parts[0]
	name = field.replace(id + "_", "")
	value = document.getElementById(field).value

	if(!checkRegex(field)){
		// The Regex Check went wrong and the value is not acceptable. We print an error
		placeMessage("Error", "The value '" + value + "' does not comply with the regex. Not saving to server.");
		loadInterfaces();
		return;
	}

	fetch(api + "project/interfaces", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "update", ifid: id, value: value, field: name})
	})
	   .then(response => response.text())
	   .then(response => updateInterfaceValueResult(response))

}

function deleteInterfaceResult(response){
	if(response == "910"){
		placeMessage("Error", "The interface could not be deleted because it was not found.")
	}else if(response == "200"){
		placeMessage("Success", "Successfully deleted interface.", 1)
	}
	loadInterfaces();
}

function deleteInterface(ifid){
	// This function deletes the interface with ifid

	fetch(api + "project/interfaces", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "delete", ifid: ifid})
	})
	   .then(response => response.text())
	   .then(response => deleteInterfaceResult(response))
}

function generateTextVersion(){
	// This function requests the JSON version of the project file and puts it inside the text-box

	fetch(api + "project", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "json"})
	})
	   .then(response => response.text())
	   .then(response => TA_FORMATTED_TEXT.innerHTML = response)
}

function doHealthCheck(){
	// This function requests a health Check and sets the result

	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "healthcheck"})
	})
	   .then(response => response.text())
	   .then(response => DIV_HEALTH_CHECK.innerHTML = response)
}

function loadControlButtons(){
	// This function returns the buttons for the server control and disables all unavailable buttons

	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "control"})
	})
	   .then(response => response.text())
	   .then(response => DIV_CONTROL_BUTTONS.innerHTML = response)
}

function disableControlButtons(){
	var containers = document.getElementsByClassName("control-button");
	for (var i = 0; i < containers.length; i++){
		containers.item(i).disabled = true;
	}
	
}

function uploadToServerResult(response){
	loadControlButtons();
	placeMessage("Success", "Successfully push the configuration to the BNG Blaster.", 1)
}

function uploadToServer(){
	// This Function will upload the current project to the server and reload the buttons
	disableControlButtons();
	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "upload"})
	})
	   .then(response => response.text())
	   .then(response => uploadToServerResult(response))
}

function startInstanceResult(response){
	if(response == "200" || response == "204"){
		placeMessage("Success", "Successfully started instance.", 1)
	}else if(response == "404"){
		placeMessage("Error", "The instance does not exist on the server.")
	}
	else{
		placeMessage("Error", "The server encountered a problem. Please reload the page.")
	}
	loadLog();
}

function startInstance(){
	// This Function will start the current project on the server and reload the buttons
	disableControlButtons();
	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "start"})
	})
	   .then(response => response.text())
	   .then(response => startInstanceResult(response))
}

function loadLogResult(response){
	if(response == "990"){
		placeMessage("Error", "The BNG Blaster is currently unreachable!")
		return
	}
	DIV_BLASTER_OUTPUT.innerHTML = response
	loadControlButtons()
}

function loadLog(){
	// This Function will stop the current project on the server and reload the buttons
	disableControlButtons();
	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "log"})
	})
	   .then(response => response.text())
	   .then(response => loadLogResult(response))
}

function loadErrorLog(){
	// This Function will stop the current project on the server and reload the buttons
	disableControlButtons();
	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "error"})
	})
	   .then(response => response.text())
	   .then(response => loadLogResult(response))
}

function stopInstanceResult(response){
	placeMessage("Success", "Successfully stopped instance.", 1)
	setTimeout(() => {loadLog()}, 1000);
	setTimeout(() => {loadControlButtons()}, 1300);
}

function stopInstance(){
	// This Function will stop the current project on the server and reload the buttons
	disableControlButtons();
	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "stop"})
	})
	   .then(response => response.text())
	   .then(response => stopInstanceResult(response))
}


function killInstance(){
	// This Function will kill the current project on the server and reload the buttons
	disableControlButtons();
	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "kill"})
	})
	   .then(response => response.text())
	   .then(response => stopInstanceResult(response))
}

function hideOverwriteProject(){
	DIV_DOWNLOAD_SERVER.style.display = "none";
	DIV_DOWNLOAD_SERVER.innerHTML = "";
	loadControlButtons();
}

function proceedOverwriteProjectResult(response){
	loadControlButtons();
	hideOverwriteProject();
	placeMessage("Success", "Successfully overwrote the porject with the data from the BNG Blaster.", 1)
}

function proceedOverwriteProject(){
	// we now tell the server to overwrite the project. We only need to reload the buttons, everything else gets reloaded when needed.
	disableControlButtons();
	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "download"})
	})
	   .then(response => response.text())
	   .then(response => proceedOverwriteProjectResult(response))
}

function downloadFromServerResult(response){
	DIV_DOWNLOAD_SERVER.style.display = "block";
	DIV_DOWNLOAD_SERVER.innerHTML = response;
}

function downloadFromServer(){
	// This function retreives the config on the blaster and presents the user with the option to overwrite the current project or cancel

	disableControlButtons();
	fetch(api + "project/control", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "download-dry"})
	})
	   .then(response => response.text())
	   .then(response => downloadFromServerResult(response))
}

function loadOptionsResult(response){
	DIV_OPTIONS_FIELD.innerHTML = response
}

function loadOptions(){
	fetch(api + "project/options", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "get-options"})
	})
	   .then(response => response.text())
	   .then(response => loadOptionsResult(response))
}

function saveProjectResult(response){
	if(response == "200"){
		placeMessage("Success", "The project was permanently saved to the server.", 1)
	}else{
		placeMessage("Error", "The server encountered an error. Please reload the page.")
	}
}

function saveProject(){
	fetch(api + "project/options", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "save"})
	})
	   .then(response => response.text())
	   .then(response => saveProjectResult(response))
}

function hideCloseProject(){
	DIV_CLOSE_PROJECT.style.display = "none";
}


function closeProjectResult(response){
	if(response == "200"){
		window.location.href = "/";
	}else{
		placeMessage("Errpr", "The server encountered an error and the project was not closed. Please reload the page.")
		hideCloseProject();
	}
}

function doCloseProject(){
	// This function closes the project and if successful sends us to the main page.
	fetch(api + "project/options", {
	    method: 'POST',
	    body: getFormData({id: project_id, mode: "close"})
	})
	   .then(response => response.text())
	   .then(response => closeProjectResult(response))
}

function closeProject(){
	DIV_CLOSE_PROJECT.style.display = "block";
}
