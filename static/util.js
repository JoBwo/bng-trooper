function placeMessage(title, message, severity = 0){
	//  severity = 0 -> Error; 1 -> success
	// We create a div which contains the title and the text and spawn it on the screen.

	let outside = document.createElement("div")
	outside.classList.add("w3-panel")
	outside.classList.add("w3-animate-bottom")
	outside.classList.add("w3-round")
	outside.classList.add(severity == 0 ? "w3-red" : "w3-green");
	let heading = document.createElement("h3")
	heading.innerHTML = title
	let text = document.createElement("p")
	text.innerHTML = message
	outside.appendChild(heading)
	outside.appendChild(text)

	DIV_ERROR_LIST.appendChild(outside)

	timeout = setTimeout(() => {removeMessage(outside)}, 5000)
	outside.onmouseover = function(){clearTimeout(timeout)}
	outside.onmouseout = function(){timeout = setTimeout(() => {removeMessage(outside)}, 5000); this.onmouseover = function(){clearTimeout(timeout)}}

}

function removeMessage(message){
	DIV_ERROR_LIST.removeChild(message)
}

function getFormData(data){
	var fd = new FormData();
    for(var i in data){
        fd.append(i,data[i]);
    }
    return fd;
}
