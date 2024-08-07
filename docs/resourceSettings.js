document.addEventListener('DOMContentLoaded', function() {
    // Handle Resource and Cost Settings
    const attachResourceCheckbox = document.getElementById('attachResource');
    const resourceOptions = document.getElementById('resourceOptions');

    if (attachResourceCheckbox && resourceOptions) {
        attachResourceCheckbox.addEventListener('change', function() {
            resourceOptions.style.display = this.checked ? 'block' : 'none';
        });
    }
});
