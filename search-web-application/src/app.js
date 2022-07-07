import { init_algolia } from "./algolia";
// IMPORTANT: Algolia specific code is contained in 'algolia.js'
// This JS file is responsible for checking if a user has configured the application with an Algolia AppId, SearchKey and IndexName.
// If the app is not configured, it shows the search form. 
// If the app is configured, it initializes Algolia by calling init_algolia() which is contained in algolia.js

const DEFAULT_APP_ID = 'XZOLQ7O0XC';
const DEFAULT_SEARCH_KEY = 'f484aba5fb5ebb9b4317e81328f638a9';
const DEFAULT_INDEX_NAME = 'test_index';

const setupContainer = document.getElementById('setup-container');
const algoliaContainer = document.getElementById('algolia-container');
const setupLink = document.getElementById('setup-link');

const setupAppIdElement = document.getElementById('setup-app-id');
const setupSearchKeyAppIdElement = document.getElementById('setup-search-key');
const setupIndexNameElement = document.getElementById('setup-index-name');
const setupSubmitButton = document.getElementById('setup-continue');
const setupErrorMessage = document.getElementById('setup-error-message');

function initApp() {
  const appId = localStorage.getItem('algolia_appId');
  const searchKey = localStorage.getItem('algolia_searchKey');
  const indexName = localStorage.getItem('algolia_indexName');

  // if any of the required properties is not configured, show setup form
  if (!appId || !searchKey || !indexName) {
   showSetup();
  } else {
    // if all required properties are configured
    setupContainer.style.display = 'none';
    algoliaContainer.style.display = 'grid';
    setupLink.style.display = 'initial';
    try {
      init_algolia(appId, searchKey, indexName);
    }
    catch (e) {
      console.log('asd', e)
    }
  }
}
function showSetup(errorMessage) {
  setupLink.style.display = 'none';
  setupContainer.style.display = 'block';
  algoliaContainer.style.display = 'none';
  setupAppIdElement.value = localStorage.getItem('algolia_appId');
  setupSearchKeyAppIdElement.value = localStorage.getItem('algolia_searchKey');
  setupIndexNameElement.value = localStorage.getItem('algolia_indexName');
  setupErrorMessage.innerText = errorMessage || '';
  canSetupContinue();
  return false; // needed to prevent link tag from navigating
}

function canSetupContinue() {
  const canContinue = setupAppIdElement.value && setupSearchKeyAppIdElement.value && setupIndexNameElement.value;
  if (canContinue) {
    setupSubmitButton.removeAttribute('disabled');
  } else {
    setupSubmitButton.setAttribute('disabled', true);
  }
  return canContinue;
}

function setupDefaults() {
  setupAppIdElement.value = DEFAULT_APP_ID;
  setupSearchKeyAppIdElement.value = DEFAULT_SEARCH_KEY;
  setupIndexNameElement.value = DEFAULT_INDEX_NAME;
  submitSetup();
}


function submitSetup() {
  localStorage.setItem('algolia_appId', setupAppIdElement.value);
  localStorage.setItem('algolia_searchKey', setupSearchKeyAppIdElement.value);
  localStorage.setItem('algolia_indexName', setupIndexNameElement.value);
  // reload the page instead of calling initApp() to bypass issues with Google Map
  setTimeout(function(){
    window.location.reload();
  });
}




initApp();

window.showSetup = showSetup;
window.canSetupContinue = canSetupContinue;
window.setupDefaults = setupDefaults;
window.submitSetup = submitSetup;