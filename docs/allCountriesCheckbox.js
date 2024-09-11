document.addEventListener('DOMContentLoaded', function() {
    const allCountriesCheckbox = document.getElementById('allCountries');
    const countrySelect = document.getElementById('country');

    if (allCountriesCheckbox && countrySelect) {
        allCountriesCheckbox.addEventListener('change', function() {
            countrySelect.disabled = this.checked;
        });
    } else {
        console.error('All Countries checkbox or Country select not found in the DOM');
    }
});
