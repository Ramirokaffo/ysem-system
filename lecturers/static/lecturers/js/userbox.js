(function () {
    'use strict';

    var box = document.querySelector('[data-userbox]');
    if (!box) return;

    var btn = box.querySelector('[data-userbtn]');
    var menu = box.querySelector('.lec-usermenu');
    if (!btn || !menu) return;

    function isOpen() {
        return !menu.hidden;
    }

    function openMenu() {
        menu.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
        box.classList.add('is-open');
    }

    function closeMenu() {
        menu.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
        box.classList.remove('is-open');
    }

    btn.addEventListener('click', function (event) {
        event.stopPropagation();
        if (isOpen()) {
            closeMenu();
        } else {
            openMenu();
        }
    });

    document.addEventListener('click', function (event) {
        if (!isOpen()) return;
        if (!box.contains(event.target)) {
            closeMenu();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && isOpen()) {
            closeMenu();
            btn.focus();
        }
    });
})();
