function generateApiPayload() {
    const modelSelect = document.getElementById('model');
    const countrySelect = document.getElementById('country');
    const allCountriesCheckbox = document.getElementById('allCountries');
    const startYearInput = document.getElementById('startYear');
    const endYearInput = document.getElementById('endYear');
    const entrypointsTable = document.getElementById('entrypointsTable');
    const resultsList = document.getElementById('resultsList');

    // Fetch the selected model
    return fetch(modelSelect.value)
        .then(response => response.json())
        .then(modelData => {
            // Determine if we're running for all countries or a single country
            const runAllCountries = allCountriesCheckbox.checked;
            const selectedCountry = countrySelect.value;

            // Function to generate payload for a single country
            function generateCountryPayload(country) {
                const payload = JSON.parse(JSON.stringify(modelData)); // Deep clone the model data

                // Update country
                const countryEntrypoint = payload.entrypoints.find(entry => entry.id === "COUNTRY");
                if (countryEntrypoint) {
                    countryEntrypoint.value = country;
                }

                // Update start and end years
                payload.runtime.startYear = parseInt(startYearInput.value);
                payload.runtime.endYear = parseInt(endYearInput.value);

                // Update entrypoints
                const entrypointRows = entrypointsTable.querySelectorAll('tbody tr');
                entrypointRows.forEach(row => {
                    const id = row.cells[0].textContent;
                    const valueInput = row.cells[2].querySelector('input');
                    const entrypoint = payload.entrypoints.find(entry => entry.id === id);
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
                return {
                    botech: payload,
                    queries: selectedResults,
                    environment: "standard"
                };
            }

            if (runAllCountries) {
                // Fetch the list of all countries
                return fetch('./list_of_countries.json')
                    .then(response => response.json())
                    .then(data => {
                        const countries = data.countries.map(country => country.iso3);
                        return countries.map(country => generateCountryPayload(country));
                    });
            } else {
                // Generate payload for the selected country
                return [generateCountryPayload(selectedCountry)];
            }
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
            .then(payloads => {
                console.log('API Payloads:', payloads);
                
                // Send the POST request to the API for each payload
                return Promise.all(payloads.map(payload => 
                    fetch('https://api.forecasthealth.org/pipeline', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(payload),
                    })
                    .then(response => response.json())
                    .then(data => ({
                        response: data,
                        payload: payload
                    }))
                ));
            })
            .then(results => {
                console.log('API Responses:', results);
                
                // Process each response
                results.forEach(({ response, payload }) => {
                    // Extract the task_id from the response
                    const taskId = response.task_id;
                    
                    // Add the run to the RunList
                    const modelName = document.getElementById('model').options[document.getElementById('model').selectedIndex].text;
                    const countryName = payload.botech.entrypoints.find(entry => entry.id === "COUNTRY").value;
                    const scenarioName = document.getElementById('scenario').options[document.getElementById('scenario').selectedIndex].text;
                    runList.addRun(taskId, modelName, countryName, scenarioName);
                });

                console.log(`Started ${results.length} run(s). Check the Run List for status updates.`);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your request. Please try again.');
            });
    });
} else {
    console.error('Generate button not found in the DOM');
}
