document.addEventListener('DOMContentLoaded', function() {
    const uhccWorkbookSelect = document.getElementById('uhccWorkbook');

    if (!uhccWorkbookSelect) {
        console.error('UHCC Workbook select element not found in the DOM');
        return;
    }

    fetch('./list_of_excel_workbooks.json')
        .then(response => response.json())
        .then(data => {
            // Clear existing options
            uhccWorkbookSelect.innerHTML = '';

            // Add new options based on the JSON data
            Object.keys(data).forEach(workbookName => {
                const option = document.createElement('option');
                option.value = workbookName;
                option.textContent = workbookName;
                uhccWorkbookSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching Excel workbook list:', error));
});