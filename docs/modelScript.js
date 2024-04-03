import {
    DISEASE_NAME,
    INTERVENTIONS,
    DEFAULT_COVERAGE,
    NULL_COVERAGE_CHANGES,
    CR2_COVERAGE_CHANGES,
    CR4_COVERAGE_CHANGES,
    RESULTS_QUERY
} from './constants.js'


function populateCoverageOptions() {
    const coverageOptions = document.getElementById('coverageOptions');
    INTERVENTIONS.forEach(intervention => {
        const div = document.createElement('div');
        div.classList.add('form-group');
        
        const label = document.createElement('label');
        label.textContent = intervention;
        div.appendChild(label);

        const starting_input = document.createElement('input');
        starting_input.type = 'number';
        starting_input.classList.add('form-control', 'coverage-value');
        starting_input.id = `${intervention}-starting`;
        starting_input.value = DEFAULT_COVERAGE;
        starting_input.step = "0.01";
        starting_input.min = "0";
        starting_input.max = "1";
        starting_input.readOnly = true;
        div.appendChild(starting_input);

        const target_input = document.createElement('input');
        target_input.type = 'number';
        target_input.classList.add('form-control', 'coverage-value');
        target_input.id = `${intervention}-target`;
        target_input.value = DEFAULT_COVERAGE;
        target_input.step = "0.01";
        target_input.min = "0";
        target_input.max = "1";
        target_input.readOnly = true;
        div.appendChild(target_input);

        coverageOptions.appendChild(div);
    });
}


function handleInterventionChange() {
    const interventionSelection = document.querySelector('input[name="interventionOptions"]:checked').value;
    resetCoverages();
    if (interventionSelection == "NULL") {
        applyCoverageChanges(NULL_COVERAGE_CHANGES);
    } else if (interventionSelection === 'CR2') {
        applyCoverageChanges(CR2_COVERAGE_CHANGES);
    } else if (interventionSelection === 'CR4') {
        applyCoverageChanges(CR4_COVERAGE_CHANGES);
    };
    toggleFormDisable();
}

function toggleFormDisable(){
    const interventionSelection = document.querySelector('input[name="interventionOptions"]:checked').value;
    INTERVENTIONS.forEach(intervention => {
        const startId = `${intervention}-starting`
        const targetId = `${intervention}-target`
        if (interventionSelection === 'custom') {
            document.getElementById(startId).readOnly = false
            document.getElementById(targetId).readOnly = false
        } else {
            document.getElementById(startId).readOnly = true
            document.getElementById(targetId).readOnly = true
        }
    });
};


function resetCoverages() {
    INTERVENTIONS.forEach(intervention => {
        const targetNode = `${intervention}-target`;
        document.getElementById(targetNode).value = DEFAULT_COVERAGE;
    });
}

function applyCoverageChanges(changes) {
    Object.keys(changes).forEach(intervention => {
        const interventionID = `${intervention}-target`;
        document.getElementById(interventionID).value = changes[intervention];
    });
}

window.runModel = function() {
    const iso3 = document.getElementById('selectCountry').value
    fetch('copd_baseline.json')
        .then(response => response.json())
        .then(data => {
            const botech = data;
            updateTimeHorizon(botech)
            changeCountry(botech, iso3)
            updateCoverages(botech)
            postBotech(botech)
        })
}

function updateTimeHorizon(botech){
    let startTime = document.getElementById("startTime").value
    let endTime = document.getElementById("endTime").value
    startTime = parseInt(startTime, 10)
    endTime = parseInt(endTime, 10)
    botech.runtime.startYear = startTime
    botech.runtime.endYear = endTime
};

function changeCountry(modelData, newCountryISO3) {
    if (modelData.nodes) {
        modelData.nodes.forEach(node => {
            if (node.generate_array && node.generate_array.parameters) {
                if ('country' in node.generate_array.parameters) {
                    node.generate_array.parameters.country = newCountryISO3;
                }
            }
        });
    }

    if (modelData.links) {
        modelData.links.forEach(link => {
            if (link.generate_array && link.generate_array.parameters) {
                if ('country' in link.generate_array.parameters) {
                    link.generate_array.parameters.country = newCountryISO3;
                }
            }
        });
    }
}


function updateCoverages(botech) {
    INTERVENTIONS.forEach(
        function(element) {

            const sourceLabel = `${element}-starting`;
            let sourceValue = document.getElementById(sourceLabel).value
            sourceValue = parseInt(sourceValue, 10)
            const sourceNodeLabel = `${element}_StartingCoverage`

            const targetLabel = `${element}-target`;
            let targetValue = document.getElementById(targetLabel).value
            targetValue = parseInt(targetValue, 10)
            const targetNodeLabel = `${element}_Coverage`

            botech.nodes.forEach(
                function(node) {
                    if (node.label == sourceNodeLabel) {
                        node.generate_array.parameters.value = sourceValue;
                    } else if (node.label == targetNodeLabel) {
                        node.generate_array.parameters.value = targetValue;
                    }
                }
            )
        }
    )
};

function generateFileID() {
    const iso3 = document.getElementById('selectCountry').value
    const scenario = document.querySelector('input[name="interventionOptions"]:checked').value;
    const fileID = `${DISEASE_NAME}-${scenario}-${iso3}`
    return fileID
};



function postBotech(botech) {
  const file_id = generateFileID();
  const run_url = "https://api.forecasthealth.org/run/appendix_3";
  const query_url = "https://api.forecasthealth.org/query";
  const runModelButton = document.querySelector('button[onclick="runModel()"]');
  const requestBody = {
    data: botech,
    store: false,
    file_id: file_id
  };

  const spinner = document.createElement('div');
  spinner.className = 'spinner-border text-secondary';
  spinner.setAttribute('role', 'status');
  const spinnerText = document.createElement('span');
  spinnerText.className = 'sr-only';
  spinnerText.textContent = 'Loading...';
  spinner.appendChild(spinnerText);
  if (runModelButton) {
    runModelButton.insertAdjacentElement('afterend', spinner); // Insert right after the "Run Model" button
  } else {
    console.error('Run Model button not found');
  }

  fetch(run_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(requestBody)
  })
  .then(response => {
    if (response.ok) {
      return response.text();
    }
    throw new Error('Network response was not ok.');
  })
  .then(csvText => {
    const queryRequestBody = {
      results: csvText,
      query: RESULTS_QUERY
    };

    return fetch(query_url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(queryRequestBody)
    });
  })
  .then(response => {
    if (response.ok) {
      return response.text();
    }
    throw new Error('Query API response was not ok.');
  })
.then(queryResponseCsv => {
  console.log('Query API CSV response:', queryResponseCsv);
  const blob = new Blob([queryResponseCsv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  
  let button = document.getElementById('downloadResultsButton'); // Check if button exists
  if (!button) {
    button = document.createElement('button');
    button.id = 'downloadResultsButton'; // Assign an ID to the button
    button.className = 'btn btn-primary ml-2'; // Add margin-left for spacing
    button.textContent = 'Download Results';

    const a = document.createElement('a');
    a.id = 'downloadResultsLink'; // Assign an ID to the link
    a.style.display = 'none';

    button.appendChild(a);
    button.addEventListener('click', () => a.click());

    if (runModelButton) {
      runModelButton.insertAdjacentElement('afterend', button); // Insert right after the "Run Model" button
    } else {
      console.error('Run Model button not found');
    }
  }

  // Update the link's href attribute
  const a = document.getElementById('downloadResultsLink');
  a.href = url;
  a.download = "Results.csv";

  // Remove spinner
  spinner.remove();
})
}


fetch('metadata.json')
.then(response => response.json())
.then(data => {
    const selectCountry = document.getElementById('selectCountry');
    data.forEach(country => {
        let option = new Option(country.name, country.code);
        selectCountry.add(option);
    });
});

document.addEventListener('DOMContentLoaded', function () {
    populateCoverageOptions();
    document.querySelectorAll('input[type=radio]').forEach(input => {
        input.addEventListener('change', handleInterventionChange);
    });
});


