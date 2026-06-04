(function () {
    'use strict';

    var container = document.getElementById('subject-formset');
    if (!container) return;

    var totalInput = document.querySelector('[name="' + container.dataset.totalName + '"]');
    var template = document.getElementById('subject-empty-template');
    var list = container.querySelector('.formset-list');

    function addForm() {
        if (!template || !totalInput || !list) return null;
        var index = parseInt(totalInput.value, 10);
        var html = template.innerHTML.replace(/__prefix__/g, index);
        var wrapper = document.createElement('div');
        wrapper.innerHTML = html.trim();
        var node = wrapper.firstChild;
        list.appendChild(node);
        totalInput.value = index + 1;
        return node;
    }

    function setCoursesForSubject(subjectId, checked) {
        if (!subjectId) return;
        var boxes = document.querySelectorAll('.course-checkbox[data-subject-id="' + subjectId + '"]');
        boxes.forEach(function (cb) { cb.checked = checked; });
    }

    function isActive(block) {
        if (block.style.display === 'none') return false;
        var del = block.querySelector('input[type="checkbox"][name$="-DELETE"]');
        return !(del && del.checked);
    }

    function activeSubjectIds() {
        var ids = [];
        list.querySelectorAll('.formset-block').forEach(function (block) {
            if (!isActive(block)) return;
            var sel = block.querySelector('select[name$="-subject"]');
            if (sel && sel.value) ids.push(sel.value);
        });
        return ids;
    }

    function ensureSubject(subjectId) {
        if (!subjectId) return;
        if (activeSubjectIds().indexOf(subjectId) !== -1) return;

        // Réactiver un bloc précédemment supprimé pour cette matière, le cas échéant.
        var blocks = list.querySelectorAll('.formset-block');
        for (var i = 0; i < blocks.length; i++) {
            var sel = blocks[i].querySelector('select[name$="-subject"]');
            if (sel && sel.value === subjectId) {
                var del = blocks[i].querySelector('input[type="checkbox"][name$="-DELETE"]');
                if (del) del.checked = false;
                blocks[i].style.display = '';
                return;
            }
        }

        // Sinon, ajouter une nouvelle ligne de matière pré-remplie.
        var node = addForm();
        if (!node) return;
        var newSel = node.querySelector('select[name$="-subject"]');
        if (newSel) newSel.value = subjectId;
        node.querySelectorAll('input[type="number"]').forEach(function (inp) {
            if (!inp.value) inp.value = 0;
        });
    }

    function removeBlock(block) {
        var sel = block.querySelector('select[name$="-subject"]');
        if (sel && sel.value) setCoursesForSubject(sel.value, false);
        var del = block.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (del) {
            del.checked = true;
            block.style.display = 'none';
        } else {
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

    document.querySelectorAll('.course-checkbox').forEach(function (cb) {
        cb.addEventListener('change', function () {
            if (cb.checked) ensureSubject(cb.dataset.subjectId);
        });
    });

    // Cocher « Supprimer cette matière » doit aussi décocher les cours de cette
    // matière, sinon l'invariant métier la recrée automatiquement à la sauvegarde.
    list.querySelectorAll('input[type="checkbox"][name$="-DELETE"]').forEach(function (del) {
        del.addEventListener('change', function () {
            if (!del.checked) return;
            var block = del.closest('.formset-block');
            if (!block) return;
            var sel = block.querySelector('select[name$="-subject"]');
            if (sel && sel.value) setCoursesForSubject(sel.value, false);
        });
    });
})();
