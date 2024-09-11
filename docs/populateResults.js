document.addEventListener('DOMContentLoaded', function() {
    const resultsList = document.getElementById('resultsList');

    function fetchAndPopulateResults() {
        fetch('./list_of_results.json')
            .then(response => response.json())
            .then(data => {
                resultsList.innerHTML = ''; // Clear existing items
                Object.entries(data).forEach(([key, result]) => {
                    const li = document.createElement('li');
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.id = key;
                    checkbox.name = key;
                    checkbox.dataset.result = JSON.stringify(result);
                    
                    const label = document.createElement('label');
                    label.htmlFor = key;
                    label.textContent = result.label;
                    
                    const description = document.createElement('p');
                    description.textContent = result.description;
                    description.style.marginLeft = '20px';
                    description.style.fontSize = '0.9em';
                    description.style.color = '#666';

                    li.appendChild(checkbox);
                    li.appendChild(label);
                    li.appendChild(description);
                    resultsList.appendChild(li);
                });
            })
            .catch(error => console.error('Error fetching results list:', error));
    }

    fetchAndPopulateResults();
});
