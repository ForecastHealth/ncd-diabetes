function generateApiPayload() {
    const modelSelect = document.getElementById('model');
    const scenarioSelect = document.getElementById('scenario');
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
                return new Promise((resolve) => {
                    const payload = JSON.parse(JSON.stringify(modelData)); // Deep clone the model data
                    let appliedScenario = {};

                    // Always get values from the entrypoints table
                    const rows = entrypointsTable.querySelectorAll('tbody tr');
                    rows.forEach(row => {
                        const id = row.cells[0].textContent;
                        const value = row.querySelector('input').value;
                        // Convert to number if possible, otherwise keep as string
                        appliedScenario[id] = isNaN(parseFloat(value)) ? value : parseFloat(value);
                    });

                    resolve(finalizePayload(payload, country, appliedScenario));
                });
            }

            function finalizePayload(payload, country, appliedScenario) {
                // Update country
                const countryEntrypoint = payload.entrypoints.find(entry => entry.id === "COUNTRY");
                if (countryEntrypoint) {
                    countryEntrypoint.value = country;
                }

                // Update start and end years
                payload.runtime.startYear = parseInt(startYearInput.value);
                payload.runtime.endYear = parseInt(endYearInput.value);

                // Update entrypoints
                payload.entrypoints.forEach(entrypoint => {
                    if (appliedScenario.hasOwnProperty(entrypoint.id)) {
                        let value = appliedScenario[entrypoint.id];
                        // Convert to number if possible, otherwise keep as string
                        entrypoint.value = isNaN(parseFloat(value)) ? value : parseFloat(value);
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
                    environment: "appendix_3"
                };
            }

            if (runAllCountries) {
                // Fetch the list of all countries
                return fetch('./list_of_countries.json')
                    .then(response => response.json())
                    .then(data => {
                        const countries = data.countries.map(country => country.iso3);
                        return Promise.all(countries.map(country => generateCountryPayload(country)));
                    });
            } else {
                // Generate payload for the selected country
                return generateCountryPayload(selectedCountry).then(payload => [payload]);
            }
        });
}

function getAppliedScenario(scenarioData, country) {
    // Check country_overrides
    if (scenarioData.country_overrides && scenarioData.country_overrides[country]) {
        return { ...scenarioData.defaults, ...scenarioData.country_overrides[country] };
    }
    
    // Check scenario_groups
    for (const group in scenarioData.scenario_groups) {
        if (scenarioData.scenario_groups[group].countries.includes(country)) {
            return { ...scenarioData.defaults, ...scenarioData.scenario_groups[group].parameters };
        }
    }
    
    // Use defaults
    return scenarioData.defaults;
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
const attachResourceCheckbox = document.getElementById('attachResource');
const uhccWorkbookSelect = document.getElementById('uhccWorkbook');
if (generateButton) {
    generateButton.addEventListener('click', function() {
        generateApiPayload()
            .then(payloads => {
                console.log('API Payloads:', payloads);

                if (attachResourceCheckbox.checked) {
                    let workbookFile;
                    let workbookFileName;

                    const customWorkbookInput = document.getElementById('customWorkbook');
                    if (customWorkbookInput.files.length > 0) {
                        workbookFile = customWorkbookInput.files[0];
                        workbookFileName = workbookFile.name;
                    } else {
                        const selectedWorkbook = uhccWorkbookSelect.value;
                        const workbookPath = `./excel_workbooks/${selectedWorkbook}`;
                        workbookFileName = selectedWorkbook;

                        return fetch(workbookPath)
                            .then(response => response.arrayBuffer())
                            .then(buffer => {
                                workbookFile = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                                return sendPayloadWithWorkbook(payloads, workbookFile, workbookFileName);
                            });
                    }

                    return sendPayloadWithWorkbook(payloads, workbookFile, workbookFileName);
                } else {
                    // Original logic for non-resource case
                    return Promise.all(payloads.map(payload => 
                        fetch('https://api.forecasthealth.org/pipeline', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(payload),
                        }).then(response => response.json())
                    ));
                }
            })
            .then(results => {
                console.log('API Responses:', results);

                // Ensure results is always an array
                const responsesArray = Array.isArray(results) ? results : [results];

                // Process each response
                responsesArray.forEach((response) => {
                    // Extract the task_id from the response
                    const taskId = response.task_id;

                    // Add the run to the RunList
                    const modelName = document.getElementById('model').options[document.getElementById('model').selectedIndex].text;
                    const countryName = document.getElementById('country').value;
                    const scenarioName = document.getElementById('scenario').options[document.getElementById('scenario').selectedIndex].text;
                    runList.addRun(taskId, modelName, countryName, scenarioName);
                });

                console.log(`Started ${responsesArray.length} run(s). Check the Run List for status updates.`);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your request. Please try again.');
            });
    });
} else {
    console.error('Generate button not found in the DOM');
}

function sendPayloadWithWorkbook(payloads, workbookFile, workbookFileName) {
    const formData = new FormData();

    payloads.forEach((payload, index) => {
        // Create the kwargs dictionary
        const kwargs = {
            optimise_costs: false,
            exclude: [],
            start_with_trigger: true
        };

        // Check if Optimise Costs is selected
        const optimiseCostsCheckbox = document.getElementById('optimiseCosts');
        if (optimiseCostsCheckbox && optimiseCostsCheckbox.checked) {
            kwargs.optimise_costs = true;
        }

        // Check which resource types to exclude
        const excludeResourceTypes = document.querySelectorAll('input[name="excludeResourceTypes"]:checked');
        excludeResourceTypes.forEach(checkbox => {
            kwargs.exclude.push(checkbox.value.toLowerCase());
        });

        // Add kwargs to the payload
        payload.kwargs = kwargs;

        formData.append(`payload_${index}`, JSON.stringify(payload));
    });
    formData.append('workbook', workbookFile, workbookFileName);

    return fetch('https://api.forecasthealth.org/uhcc', {
        method: 'POST',
        body: formData
    }).then(response => response.json());
}
