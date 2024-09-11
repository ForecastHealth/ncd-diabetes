document.addEventListener('DOMContentLoaded', function() {
    fetch('./list_of_countries.json')
        .then(response => response.json())
        .then(data => {
            const countries = data.countries;
            const countrySelect = document.getElementById('country');
            countries.forEach(country => {
                const option = document.createElement('option');
                option.value = country.iso3;
                option.text = country.name;
                countrySelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching country list:', error));
});

document.getElementById('generate').addEventListener('click', function() {
    const countrySelect = document.getElementById('country');
    const selectedCountryCode = countrySelect.value;
});

