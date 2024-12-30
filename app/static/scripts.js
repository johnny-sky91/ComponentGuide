function copyStringToClipboard(string) {
    const textarea = document.createElement('textarea');
    textarea.value = string;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    console.log('Text copied to clipboard');
}

  function toggleTable(tableId, textId) {
    var table = document.getElementById(tableId);
    var text = document.getElementById(textId);
    if (table.style.display === "none") {
        table.style.display = "table";
        text.innerHTML = "Hide the table";
    } else {
        table.style.display = "none";
        text.innerHTML = "Show the table";
    }
}