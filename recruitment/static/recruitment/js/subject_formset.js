(function () {
    'use strict';

    var container = document.getElementById('subject-formset');
    if (!container) return;

    var prefix = container.dataset.prefix;
    var totalInput = document.querySelector('[name="' + container.dataset.totalName + '"]');
    var template = document.getElementById('formset-empty-template');
    var list = container.querySelector('.formset-list');

    function addForm() {
        if (!template || !totalInput || !list) return;
        var index = parseInt(totalInput.value, 10);
        var html = template.innerHTML.replace(/__prefix__/g, index);
        var wrapper = document.createElement('div');
        wrapper.innerHTML = html.trim();
        list.appendChild(wrapper.firstChild);
        totalInput.value = index + 1;
    }

    function removeBlock(block) {
        var deleteInput = block.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteInput) {
            // Form déjà persistée → on marque pour suppression et on masque.
            deleteInput.checked = true;
            block.style.display = 'none';
        } else {
            // Form non persistée → on retire du DOM (le management form sera ajusté côté serveur).
            block.parentNode.removeChild(block);
        }
    }

    container.addEventListener('click', function (event) {
        var addBtn = event.target.closest('[data-action="add-subject"]');
        if (addBtn) {
            event.preventDefault();
            addForm();
            return;
        }
        var removeBtn = event.target.closest('[data-action="remove"]');
        if (removeBtn) {
            event.preventDefault();
            var block = removeBtn.closest('.formset-block');
            if (block) removeBlock(block);
        }
    });
})();
