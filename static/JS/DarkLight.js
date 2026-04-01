const THEMES = {
    dark: {
        css: 'https://cdn.jsdelivr.net/npm/bootswatch@5.3.0/dist/darkly/bootstrap.min.css',
        btnClass: 'bg-dark-subtle border-dark-subtle text-dark-emphasis',
        btnText: '🔆 Light Mode',
        bodyClass: 'theme-dark',
    },
    light: {
        css: 'https://cdn.jsdelivr.net/npm/bootswatch@5.3.0/dist/flatly/bootstrap.min.css',
        btnClass: 'bg-light border-secondary text-dark',
        btnText: '🌑 Dark Mode',
        bodyClass: 'theme-light',
    }
};

function applyTheme(mode) {
    const theme = THEMES[mode];
    const themeLink = document.getElementById('bootswatch-theme');
    const btn = document.getElementById('theme-toggle');

    themeLink.href = theme.css;

    btn.className = `badge border rounded-pill position-absolute bottom-0 end-0 mb-4 me-4 py-3 ${theme.btnClass}`;
    btn.textContent = theme.btnText;

    document.body.classList.remove('theme-dark', 'theme-light');
    document.body.classList.add(theme.bodyClass);

    localStorage.setItem('theme', mode);
}

function toggleTheme() {
    const current = localStorage.getItem('theme') || 'dark';
    applyTheme(current === 'dark' ? 'light' : 'dark');
}

const savedTheme = localStorage.getItem('theme') || 'dark';
applyTheme(savedTheme);