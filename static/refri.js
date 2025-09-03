function navigateTo(page) {
    window.location.href = "/" + page.replace(".html", "");
}


document.addEventListener("DOMContentLoaded", loadNotes);

function addNote() {
    let noteInput = document.getElementById("noteInput");
    let noteText = noteInput.value.trim();
    if (noteText === "") return;

    createNoteElement(noteText);

    saveNoteToLocalStorage(noteText);
    noteInput.value = "";
}

function createNoteElement(text) {
    let notesContainer = document.getElementById("notesContainer");

    let noteDiv = document.createElement("div");
    noteDiv.classList.add("note");
    noteDiv.innerHTML = `
        <p>${text}</p>
        <button class="delete-btn" onclick="deleteNote(this)">X</button>
    `;

    notesContainer.appendChild(noteDiv);
}
function deleteNote(btn) {
    let note = btn.parentElement;
    let noteText = note.querySelector("p").innerText; // Get the exact note text
    note.remove(); // Remove from UI

    // Remove from localStorage
    let notes = JSON.parse(localStorage.getItem("notes")) || [];
    notes = notes.filter(n => n !== noteText);
    localStorage.setItem("notes", JSON.stringify(notes));
}




function saveNoteToLocalStorage(note) {
    let notes = JSON.parse(localStorage.getItem("notes")) || [];
    notes.push(note);
    localStorage.setItem("notes", JSON.stringify(notes));
}

function removeNoteFromLocalStorage(noteText) {
    let notes = JSON.parse(localStorage.getItem("notes")) || [];
    notes = notes.filter(note => note !== noteText);
    localStorage.setItem("notes", JSON.stringify(notes));
}

function loadNotes() {
    let notes = JSON.parse(localStorage.getItem("notes")) || [];
    notes.forEach(createNoteElement);
}
fetch('/shoppinglist')
    .then(response => response.text())
    .then(data => {
        let lines = data.split("\n"); // Split text file into lines
        let listContainer = document.getElementById("fileContent");
        listContainer.innerHTML = ""; // Clear previous content to prevent duplication

        let listHTML = "";
        lines.forEach(line => {
            if (line.trim() !== "") { // Ignore empty lines
                listHTML += `<li>${line}</li>`;
            }
        });

        // If there's an existing <ul> in HTML, just append items
        let existingList = document.querySelector(".ingredients-list ul");
        if (existingList) {
            existingList.innerHTML = listHTML; // Update existing list
        } else {
            listContainer.innerHTML = `<ul>${listHTML}</ul>`; // Create a new list
        }
    })
    .catch(error => console.error("Error loading file:", error));
