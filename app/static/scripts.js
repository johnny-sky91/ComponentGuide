function copyListToClipboard(list) {
    const textarea = document.createElement('textarea');
    const textToCopy = JSON.parse(list).join('\n')
    console.log(textToCopy)
    textarea.value = textToCopy;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
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