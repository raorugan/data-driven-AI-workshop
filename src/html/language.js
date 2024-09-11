document.getElementById('language-button').addEventListener('click', function() {
    var menu = document.getElementById('language-menu');
    menu.classList.toggle('hidden');
  });

function loadTranslations(lang) {
fetch('translations.json')
    .then(response => response.json())
    .then(translations => {
    document.querySelectorAll('[data-translate-key]').forEach(element => {
        const key = element.getAttribute('data-translate-key');
        if (translations[lang][key]) {
            element.textContent = translations[lang][key];
        }
    });
    })
    .catch(error => console.error('Error loading translations:', error));
}

document.querySelectorAll('#language-menu a').forEach(link => {
link.addEventListener('click', function(event) {
    event.preventDefault();
    const lang = this.getAttribute('data-lang');
    loadTranslations(lang);
    // Save the selected language in local storage
    localStorage.setItem('language', lang);
    document.getElementById('language-menu').classList.add('hidden');
});
});

// Load the selected language from local storage
const lang = localStorage.getItem('language') || 'en';
loadTranslations(lang);