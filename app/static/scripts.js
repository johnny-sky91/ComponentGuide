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
  