
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

        

        // Logout function
        function logout() {
            if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
                // Rediriger vers la page de déconnexion personnalisée
                window.location.href = '{% url "authentication:logout" %}';
            }
        }

        // Alert dismissible functionality
        document.addEventListener('DOMContentLoaded', function() {

            // User dropdown functionality
            const userDropdown = document.getElementById('userDropdown');
            const userDropdownMenu = document.querySelector('.user-dropdown-menu');

            if (userDropdown && userDropdownMenu) {
                // Toggle dropdown on click
                userDropdown.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();

                    // Fermer tous les autres dropdowns ouverts
                    document.querySelectorAll('.user-dropdown-menu.show').forEach(function(menu) {
                        if (menu !== userDropdownMenu) {
                            menu.classList.remove('show');
                        }
                    });

                    // Toggle le dropdown actuel
                    userDropdownMenu.classList.toggle('show');
                });

                // Close dropdown when clicking outside
                document.addEventListener('click', function(e) {
                    if (!e.target.closest('.user-profile')) {
                        userDropdownMenu.classList.remove('show');
                    }
                });

                // Close dropdown when pressing Escape
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        userDropdownMenu.classList.remove('show');
                    }
                });

                // Prevent dropdown from closing when clicking inside it
                userDropdownMenu.addEventListener('click', function(e) {
                    e.stopPropagation();
                });
            }
        });