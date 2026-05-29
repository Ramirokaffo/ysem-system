
        // Update current date
        document.addEventListener('DOMContentLoaded', function() {
            const now = new Date();
            const currentDateElement = document.getElementById('current-date');
            if (currentDateElement) {
                currentDateElement.textContent = now.toLocaleDateString('fr-FR', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            }

            // Initialize sidebar toggle
        });