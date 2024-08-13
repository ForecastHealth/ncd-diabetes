function generateApiPayload() {
    const modelSelect = document.getElementById('model');
    const countrySelect = document.getElementById('country');
    const startYearInput = document.getElementById('startYear');
    const endYearInput = document.getElementById('endYear');
    const entrypointsTable = document.getElementById('entrypointsTable');
    const resultsList = document.getElementById('resultsList');

    // Fetch the selected model
    return fetch(modelSelect.value)
        .then(response => response.json())
        .then(modelData => {
            // Update country
            const selectedCountry = countrySelect.value;
            const countryEntrypoint = modelData.entrypoints.find(entry => entry.id === "COUNTRY");
            if (countryEntrypoint) {
                countryEntrypoint.value = selectedCountry;
            }

            // Update start and end years
            modelData.runtime.startYear = parseInt(startYearInput.value);
            modelData.runtime.endYear = parseInt(endYearInput.value);

            // Update entrypoints
            const entrypointRows = entrypointsTable.querySelectorAll('tbody tr');
            entrypointRows.forEach(row => {
                const id = row.cells[0].textContent;
                const valueInput = row.cells[2].querySelector('input');
                const entrypoint = modelData.entrypoints.find(entry => entry.id === id);
                if (entrypoint && valueInput) {
                    // Convert to number if it's a valid number, otherwise keep as string
                    const numValue = parseFloat(valueInput.value);
                    entrypoint.value = isNaN(numValue) ? valueInput.value : numValue;
                }
            });

            // Collect selected results
            const selectedResults = Array.from(resultsList.querySelectorAll('input[type="checkbox"]:checked'))
                .map(checkbox => {
                    const resultData = JSON.parse(checkbox.dataset.result);
                    return {
                        label: resultData.label,
                        query: resultData.query
                    };
                });

            // Construct the final payload
            const payload = {
                botech: modelData,
                queries: selectedResults,
                environment: "standard"
            };

            return payload;
        });
}

function showMessage(message, statusUrl) {
    const messageArea = document.getElementById('messageArea');
    const messageText = document.getElementById('messageText');
    const statusLink = document.getElementById('statusLink');

    messageText.textContent = message;
    statusLink.href = statusUrl;
    messageArea.style.display = 'block';

    // Scroll to the message area
    messageArea.scrollIntoView({ behavior: 'smooth' });
}

function checkStatus(statusUrl) {
    fetch(statusUrl)
        .then(response => response.json())
        .then(data => {
            console.log('Received status:', data.status);
            if (data.status === "SUCCESS" && data.result && data.result.download_url) {
                console.log('Received successful status with download URL:', data.result.download_url);
                showDownloadButton(data.result.download_url);
            } else if (data.status === "PENDING" || data.status === "PROGRESS") {
                showMessage("Your job is still being processed. Please check again later.", "#");
            } else {
                showMessage("An error occurred or the job is not complete. Please try again later.", "#");
            }
        })
        .catch(error => {
            console.error('Error checking status:', error);
            showMessage("An error occurred while checking the status. Please try again.", "#");
        });
}

function showDownloadButton(downloadUrl) {
    console.log('Setting up download button with URL:', downloadUrl);
    const messageArea = document.getElementById('messageArea');
    const messageText = document.getElementById('messageText');
    const statusLink = document.getElementById('statusLink');

    messageText.textContent = "Your results are ready!";
    statusLink.textContent = "Download Results";
    statusLink.href = downloadUrl;
    statusLink.setAttribute('download', 'pipeline_results.zip');
    messageArea.style.display = 'block';

    // Remove any existing event listeners
    statusLink.removeEventListener('click', checkStatusHandler);
    
    // Add a new event listener for the download
    statusLink.addEventListener('click', function(event) {
        // Do not prevent default behavior for the download link
        console.log('Download link clicked');
    });
}

// Event listener for the generate button
const generateButton = document.getElementById('generate');
if (generateButton) {
    generateButton.addEventListener('click', function() {
        generateApiPayload()
            .then(payload => {
                console.log('API Payload:', payload);
                
                // Send the POST request to the API
                return fetch('https://api.forecasthealth.org/pipeline', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });
            })
            .then(response => response.json())
            .then(data => {
                console.log('API Response:', data);
                
                // Extract the task_id from the response
                const taskId = data.task_id;
                
                // Add the run to the RunList
                const modelName = document.getElementById('model').options[document.getElementById('model').selectedIndex].text;
                const countryName = document.getElementById('country').options[document.getElementById('country').selectedIndex].text;
                runList.addRun(taskId, modelName, countryName);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your request. Please try again.');
            });
    });
} else {
    console.error('Generate button not found in the DOM');
}
