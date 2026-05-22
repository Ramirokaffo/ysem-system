(function () {
    'use strict';

    var modal = document.getElementById('course-modal');
    if (!modal) return;

    var codeEl = document.getElementById('course-modal-code');
    var subjectEl = document.getElementById('course-modal-subject');
    var titleEl = document.getElementById('course-modal-title');
    var levelEl = document.getElementById('course-modal-level');
    var creditsEl = document.getElementById('course-modal-credits');
    var descEl = document.getElementById('course-modal-description');
    var lastFocus = null;

    function setOptionalText(el, value) {
        if (!el) return;
        var v = (value || '').trim();
        if (v) {
            el.textContent = v;
            el.hidden = false;
        } else {
            el.textContent = '';
            el.hidden = true;
        }
    }

    function fillModal(btn) {
        var data = btn.dataset;
        if (codeEl) codeEl.textContent = data.courseCode || '—';
        if (subjectEl) subjectEl.textContent = data.courseSubject || '—';
        if (titleEl) titleEl.textContent = data.courseLabel || '—';
        setOptionalText(levelEl, data.courseLevel);
        setOptionalText(creditsEl, data.courseCredits ? data.courseCredits + ' crédit' + (parseInt(data.courseCredits, 10) > 1 ? 's' : '') : '');
        var description = (data.courseDescription || '').trim();
        if (description) {
            descEl.innerHTML = '';
            var p = document.createElement('p');
            p.className = 'course-modal__text';
            p.textContent = description;
            descEl.appendChild(p);
        } else {
            descEl.innerHTML = '<p class="course-modal__empty">Aucune description disponible pour ce cours.</p>';
        }
    }

    function openModal(btn) {
        lastFocus = btn;
        fillModal(btn);
        modal.hidden = false;
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('has-open-modal');
        var closeBtn = modal.querySelector('.course-modal__close');
        if (closeBtn) closeBtn.focus();
    }

    function closeModal() {
        modal.hidden = true;
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('has-open-modal');
        if (lastFocus && typeof lastFocus.focus === 'function') {
            lastFocus.focus();
        }
    }

    document.addEventListener('click', function (event) {
        var openBtn = event.target.closest('[data-action="open-course-modal"]');
        if (openBtn) {
            event.preventDefault();
            openModal(openBtn);
            return;
        }
        var closeBtn = event.target.closest('[data-action="close-course-modal"]');
        if (closeBtn && modal.contains(closeBtn)) {
            event.preventDefault();
            closeModal();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !modal.hidden) {
            closeModal();
        }
    });
})();
