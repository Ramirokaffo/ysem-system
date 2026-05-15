/* Wizard de pré-inscription — gestion dynamique des formsets.
   Ajout/suppression de blocs (diplômes du secondaire, niveaux universitaires).
   Aucune dépendance externe — vanilla JS uniquement. */
(function () {
    'use strict';

    function initFormset(section) {
        var prefix = section.dataset.prefix;
        var totalInput = document.querySelector('input[name="' + section.dataset.totalName + '"]');
        if (!totalInput) return;

        var list = section.querySelector('.formset-list');
        var template = section.querySelector('.formset-empty-tpl');
        var addBtn = section.querySelector('[data-action="add"]');

        function refreshCount() {
            totalInput.value = list.querySelectorAll('.formset-block').length;
        }

        function addBlock() {
            if (!template) return;
            var index = list.querySelectorAll('.formset-block').length;
            // Le <template> peut être soit un vrai <template> (content) soit un <div class="formset-empty-tpl">
            var html;
            if (template.content) {
                var wrapper = document.createElement('div');
                wrapper.appendChild(template.content.cloneNode(true));
                html = wrapper.innerHTML;
            } else {
                html = template.innerHTML;
            }
            html = html.replace(/__prefix__/g, index);
            var holder = document.createElement('div');
            holder.innerHTML = html.trim();
            var block = holder.firstElementChild;
            list.appendChild(block);
            refreshCount();
        }

        function removeBlock(btn) {
            var block = btn.closest('.formset-block');
            if (!block) return;
            // Si le bloc est lié à une instance en base (champ DELETE présent), on coche DELETE
            // sinon, on retire le bloc du DOM et on décrémente le compteur.
            var deleteInput = block.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteInput && deleteInput.dataset.hasInitial === '1') {
                deleteInput.checked = true;
                block.style.display = 'none';
                return;
            }
            block.remove();
            refreshCount();
        }

        if (addBtn) {
            addBtn.addEventListener('click', function (e) {
                e.preventDefault();
                addBlock();
            });
        }

        section.addEventListener('click', function (e) {
            var btn = e.target.closest('[data-action="remove"]');
            if (!btn) return;
            e.preventDefault();
            removeBlock(btn);
        });
    }

    function initSpecialiteFilter(section) {
        var url = section.dataset.specialitesUrl;
        var programmeField = section.dataset.programmeField;
        var specialiteFields = (section.dataset.specialiteFields || '').split(',');
        if (!url || !programmeField || !specialiteFields.length) return;

        var programmeSelect = document.getElementById(programmeField);
        if (!programmeSelect) return;

        var specialiteSelects = specialiteFields
            .map(function (id) { return document.getElementById(id.trim()); })
            .filter(Boolean);
        if (!specialiteSelects.length) return;

        function placeholderFor(select) {
            var first = select.options[0];
            return first && first.value === '' ? first.text : '---------';
        }

        function rebuild(items) {
            specialiteSelects.forEach(function (select) {
                var placeholder = placeholderFor(select);
                select.innerHTML = '';
                var empty = document.createElement('option');
                empty.value = '';
                empty.textContent = placeholder;
                select.appendChild(empty);
                items.forEach(function (item) {
                    var opt = document.createElement('option');
                    opt.value = item.id;
                    opt.textContent = item.name;
                    select.appendChild(opt);
                });
            });
        }

        function refresh() {
            var programmeId = programmeSelect.value;
            if (!programmeId) {
                rebuild([]);
                return;
            }
            fetch(url + '?programme=' + encodeURIComponent(programmeId), {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' },
            })
                .then(function (resp) { return resp.ok ? resp.json() : { items: [] }; })
                .then(function (data) { rebuild(data.items || []); })
                .catch(function () { rebuild([]); });
        }

        programmeSelect.addEventListener('change', refresh);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-prefix]').forEach(initFormset);
        document.querySelectorAll('[data-specialites-url]').forEach(initSpecialiteFilter);
        document.querySelectorAll('[data-profile-photo-field]').forEach(initProfilePhotoCropper);
    });
})();
