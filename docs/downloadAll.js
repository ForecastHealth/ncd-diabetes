function downloadAll() {
    const downloadButtons = document.querySelectorAll('#runList .download-btn');
    
    downloadButtons.forEach(button => {
        // Extract the download URL and filename from the onclick attribute
        const onclickAttr = button.getAttribute('onclick');
        const match = onclickAttr.match(/runList\.downloadFile\('([^']+)',\s*'([^']+)'\)/);
        
        if (match) {
            const [, url, fileName] = match;
            runList.downloadFile(url, fileName);
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const downloadAllButton = document.getElementById('downloadAll');
    if (downloadAllButton) {
        downloadAllButton.addEventListener('click', downloadAll);
    }
});
