const btn = document.querySelector('#toggle-dark');
console.log(btn);

if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark');
}

btn.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    const theme = document.body.classList.contains('dark') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
});