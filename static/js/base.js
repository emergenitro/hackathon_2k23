const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelectorAll('.navbar .left a:not(.site-name), .navbar .right a:not(.get-started)');
const leftNav = document.querySelector('.navbar .left');

hamburger.addEventListener('click', () => {
    navLinks.forEach(link => {
        // Loop through all the links and toggle the active class
        link.classList.toggle('active');
        // Change the .navbar .left max height to 300px when the hamburger is clicked and make it 0 when it's clicked again
        leftNav.classList.toggle('active');
    });
});