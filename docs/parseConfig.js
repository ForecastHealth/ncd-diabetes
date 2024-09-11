// Function to fetch and parse JSON config
async function fetchConfig() {
  try {
    const response = await fetch('pages_config.json');
    const config = await response.json();
    return config;
  } catch (error) {
    console.error('Error fetching or parsing config:', error);
    return null;
  }
}

// Function to update HTML elements with config values
function updatePageContent(config) {
  if (!config) return;

  // Update title
  if (config.title) {
    document.title = config.title;
    document.getElementById('pageTitle').textContent = config.title;
  }

  // Update main header
  if (config.mainHeader) {
    document.getElementById('mainHeader').textContent = config.mainHeader;
  }

  // Update meta description
  if (config.metaDescription) {
    document.getElementById('pageMetaDescription').setAttribute('content', config.metaDescription);
  }

  // Update page description
  if (config.pageDescription) {
    document.getElementById('pageDescription').textContent = config.pageDescription;
  }

  // You can add more configurable elements here as needed
}

// Main function to initialize the page
async function initPage() {
  const config = await fetchConfig();
  updatePageContent(config);
}

// Run the initialization when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initPage);