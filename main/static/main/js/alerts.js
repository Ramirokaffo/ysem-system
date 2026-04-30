

        // Alert dismissible functionality
        document.addEventListener('DOMContentLoaded', function() {
            // Gérer la fermeture des alerts
            document.querySelectorAll('.alert .btn-close').forEach(function(closeBtn) {
                closeBtn.addEventListener('click', function() {
                    const alert = this.closest('.alert');
                    alert.style.opacity = '0';
                    alert.style.transform = 'translateY(-10px)';
                    setTimeout(() => {
                        alert.remove();
                    }, 300);
                });
            });

            // Auto-dismiss des alerts après 5 secondes (optionnel)
            document.querySelectorAll('.alert[data-auto-dismiss="true"]').forEach(function(alert) {
                setTimeout(() => {
                    const closeBtn = alert.querySelector('.btn-close');
                    if (closeBtn) {
                        closeBtn.click();
                    }
                }, 5000);
            });

        });