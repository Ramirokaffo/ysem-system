/* Cropper de photo de profil (1:1) — script partagé, sans dépendance.
   À l'ouverture du DOM, attache automatiquement le cropper à chaque
   élément portant l'attribut [data-profile-photo-field]. */
(function () {
    'use strict';

    function buildCropperModal() {
        var root = document.createElement('div');
        root.className = 'photo-cropper-modal';
        root.hidden = true;
        root.innerHTML = ''
            + '<div class="photo-cropper-backdrop" data-cropper-cancel></div>'
            + '<div class="photo-cropper-dialog" role="dialog" aria-modal="true" aria-labelledby="photoCropperTitle">'
            + '  <header class="photo-cropper-header">'
            + '    <h2 class="photo-cropper-title" id="photoCropperTitle">Recadrer votre photo de profil</h2>'
            + '    <p class="photo-cropper-help">Positionnez et zoomez l\'image pour conserver un cadre carré.</p>'
            + '  </header>'
            + '  <div class="photo-cropper-viewport" data-cropper-viewport>'
            + '    <img alt="" data-cropper-image>'
            + '    <div class="photo-cropper-frame" aria-hidden="true"></div>'
            + '  </div>'
            + '  <div class="photo-cropper-controls">'
            + '    <label class="photo-cropper-zoom-label">'
            + '      <span>Zoom</span>'
            + '      <input type="range" data-cropper-zoom>'
            + '    </label>'
            + '  </div>'
            + '  <footer class="photo-cropper-actions">'
            + '    <button type="button" class="photo-cropper-btn" data-cropper-cancel>Annuler</button>'
            + '    <button type="button" class="photo-cropper-btn photo-cropper-btn--primary" data-cropper-confirm>Valider le recadrage</button>'
            + '  </footer>'
            + '</div>';
        return {
            root: root,
            img: root.querySelector('[data-cropper-image]'),
            viewport: root.querySelector('[data-cropper-viewport]'),
            zoom: root.querySelector('[data-cropper-zoom]'),
            confirm: root.querySelector('[data-cropper-confirm]'),
            cancels: root.querySelectorAll('[data-cropper-cancel]'),
        };
    }

    function initProfilePhotoCropper(field) {
        if (field.dataset.profilePhotoCropperReady === '1') return;
        field.dataset.profilePhotoCropperReady = '1';

        var input = field.querySelector('input[type="file"]');
        var wrapper = field.querySelector('[data-profile-photo-preview-wrapper]');
        var preview = field.querySelector('[data-profile-photo-preview]');
        var note = field.querySelector('[data-profile-photo-note]');
        if (!input || !wrapper || !preview) return;

        var hadInitialPhoto = !!preview.getAttribute('src');
        var modal = buildCropperModal();
        document.body.appendChild(modal.root);

        var VIEWPORT = 320;
        var OUTPUT_SIZE = 600;
        var state = {
            scale: 1, minScale: 1, maxScale: 4,
            offsetX: 0, offsetY: 0,
            dragging: false, pointerId: null,
            startX: 0, startY: 0, startOX: 0, startOY: 0,
            originalFile: null,
        };

        function clamp() {
            var w = modal.img.naturalWidth * state.scale;
            var h = modal.img.naturalHeight * state.scale;
            state.offsetX = Math.min(0, Math.max(VIEWPORT - w, state.offsetX));
            state.offsetY = Math.min(0, Math.max(VIEWPORT - h, state.offsetY));
        }
        function applyTransform() {
            clamp();
            modal.img.style.transform =
                'translate(' + state.offsetX + 'px,' + state.offsetY + 'px) scale(' + state.scale + ')';
        }
        function openModal() {
            modal.root.hidden = false;
            document.body.style.overflow = 'hidden';
        }
        function closeModal() {
            modal.root.hidden = true;
            document.body.style.overflow = '';
        }
        function restorePreviewAfterCancel() {
            input.value = '';
            if (hadInitialPhoto) {
                wrapper.hidden = false;
                if (note) note.textContent = "Photo enregistrée — laissez vide pour conserver, ou choisissez un nouveau fichier pour remplacer.";
            } else {
                wrapper.hidden = true;
                preview.removeAttribute('src');
                if (note) note.textContent = '';
            }
        }
        function loadFileIntoCropper(file) {
            var reader = new FileReader();
            reader.onload = function (e) {
                modal.img.onload = function () {
                    var nw = modal.img.naturalWidth;
                    var nh = modal.img.naturalHeight;
                    state.minScale = Math.max(VIEWPORT / nw, VIEWPORT / nh);
                    state.maxScale = state.minScale * 4;
                    state.scale = state.minScale;
                    state.offsetX = (VIEWPORT - nw * state.scale) / 2;
                    state.offsetY = (VIEWPORT - nh * state.scale) / 2;
                    modal.zoom.min = String(state.minScale);
                    modal.zoom.max = String(state.maxScale);
                    modal.zoom.step = String((state.maxScale - state.minScale) / 100 || 0.01);
                    modal.zoom.value = String(state.minScale);
                    applyTransform();
                    openModal();
                };
                modal.img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
        function confirmCrop() {
            var canvas = document.createElement('canvas');
            canvas.width = OUTPUT_SIZE;
            canvas.height = OUTPUT_SIZE;
            var ctx = canvas.getContext('2d');
            var srcX = -state.offsetX / state.scale;
            var srcY = -state.offsetY / state.scale;
            var srcSize = VIEWPORT / state.scale;
            ctx.drawImage(modal.img, srcX, srcY, srcSize, srcSize, 0, 0, OUTPUT_SIZE, OUTPUT_SIZE);
            canvas.toBlob(function (blob) {
                if (!blob) { restorePreviewAfterCancel(); closeModal(); return; }
                var baseName = (state.originalFile && state.originalFile.name || 'photo').replace(/\.[^.]+$/, '');
                var newFile = new File([blob], baseName + '.jpg', { type: 'image/jpeg' });
                try {
                    var dt = new DataTransfer();
                    dt.items.add(newFile);
                    input.files = dt.files;
                } catch (err) {
                    /* Navigateur sans DataTransfer : on conserve le fichier original. */
                }
                preview.setAttribute('src', canvas.toDataURL('image/jpeg', 0.92));
                wrapper.hidden = false;
                if (note) note.textContent = "Photo recadrée prête à être envoyée : " + newFile.name;
                closeModal();
            }, 'image/jpeg', 0.92);
        }
        function zoomAt(newScale, cx, cy) {
            newScale = Math.min(state.maxScale, Math.max(state.minScale, newScale));
            var imgX = (cx - state.offsetX) / state.scale;
            var imgY = (cy - state.offsetY) / state.scale;
            state.scale = newScale;
            state.offsetX = cx - imgX * state.scale;
            state.offsetY = cy - imgY * state.scale;
            applyTransform();
        }

        input.addEventListener('change', function () {
            var file = input.files && input.files[0];
            if (!file) { restorePreviewAfterCancel(); return; }
            if (!/^image\//.test(file.type)) { restorePreviewAfterCancel(); return; }
            state.originalFile = file;
            loadFileIntoCropper(file);
        });
        modal.viewport.addEventListener('pointerdown', function (e) {
            state.dragging = true;
            state.pointerId = e.pointerId;
            state.startX = e.clientX;
            state.startY = e.clientY;
            state.startOX = state.offsetX;
            state.startOY = state.offsetY;
            try { modal.viewport.setPointerCapture(e.pointerId); } catch (err) {}
        });
        modal.viewport.addEventListener('pointermove', function (e) {
            if (!state.dragging) return;
            state.offsetX = state.startOX + (e.clientX - state.startX);
            state.offsetY = state.startOY + (e.clientY - state.startY);
            applyTransform();
        });
        function endDrag(e) {
            if (!state.dragging) return;
            state.dragging = false;
            try { modal.viewport.releasePointerCapture(e.pointerId); } catch (err) {}
        }
        modal.viewport.addEventListener('pointerup', endDrag);
        modal.viewport.addEventListener('pointercancel', endDrag);
        modal.viewport.addEventListener('wheel', function (e) {
            e.preventDefault();
            var delta = -e.deltaY * 0.0015;
            zoomAt(state.scale * (1 + delta), VIEWPORT / 2, VIEWPORT / 2);
            modal.zoom.value = String(state.scale);
        }, { passive: false });
        modal.zoom.addEventListener('input', function () {
            zoomAt(parseFloat(modal.zoom.value), VIEWPORT / 2, VIEWPORT / 2);
        });
        modal.confirm.addEventListener('click', confirmCrop);
        Array.prototype.forEach.call(modal.cancels, function (el) {
            el.addEventListener('click', function () { restorePreviewAfterCancel(); closeModal(); });
        });
        document.addEventListener('keydown', function (e) {
            if (modal.root.hidden) return;
            if (e.key === 'Escape') { restorePreviewAfterCancel(); closeModal(); }
        });
    }

    function autoInit() {
        document.querySelectorAll('[data-profile-photo-field]').forEach(initProfilePhotoCropper);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInit);
    } else {
        autoInit();
    }
    window.YsemProfilePhotoCropper = { init: initProfilePhotoCropper };
})();
