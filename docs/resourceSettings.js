document.addEventListener('DOMContentLoaded', function() {
    const attachResourceCheckbox = document.getElementById('attachResource');
    const resourceOptions = document.getElementById('resourceOptions');
    const uhccWorkbookSelect = document.getElementById('uhccWorkbook');
    const customWorkbookInput = document.getElementById('customWorkbook');
    const uploadedFileInfo = document.getElementById('uploadedFileInfo');
    const uploadedFileName = document.getElementById('uploadedFileName');
    const removeUploadedFileButton = document.getElementById('removeUploadedFile');

    if (attachResourceCheckbox && resourceOptions) {
        attachResourceCheckbox.addEventListener('change', function() {
            resourceOptions.style.display = this.checked ? 'block' : 'none';
        });
    }

    if (customWorkbookInput) {
        customWorkbookInput.addEventListener('change', function(event) {
            if (event.target.files.length > 0) {
                const file = event.target.files[0];
                uploadedFileName.textContent = file.name;
                uploadedFileInfo.style.display = 'block';
                uhccWorkbookSelect.disabled = true;
            }
        });
    }

    if (removeUploadedFileButton) {
        removeUploadedFileButton.addEventListener('click', function() {
            customWorkbookInput.value = '';
            uploadedFileInfo.style.display = 'none';
            uhccWorkbookSelect.disabled = false;
        });
    }
});
