
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

                // Close dropdown when clicking on one of its items
                userDropdownMenu.querySelectorAll('.dropdown-item').forEach(function(item) {
                    item.addEventListener('click', function() {
                        userDropdownMenu.classList.remove('show');
                    });
                });
            }
        });