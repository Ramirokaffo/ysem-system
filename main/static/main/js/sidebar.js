
// Sidebar collapse/expand functionality
        function initSidebarToggle() {
            const sidebar = document.getElementById('sidebar');
            const toggleBtn = document.getElementById('sidebarToggleBtn');
            const mainContent = document.querySelector('.main-content');
            const header = document.querySelector('.header');



            // Restore sidebar state from localStorage
            const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (sidebarCollapsed) {
                sidebar.classList.add('collapsed');
                updateToggleIcon();
                header.style.left = sidebar.classList.contains('collapsed') ? '80px' : '280px';

            }

            // Toggle sidebar on button click
            toggleBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
                updateToggleIcon();
                header.style.left = sidebar.classList.contains('collapsed') ? '80px' : '280px';
                // mainContent.style.marginLeft = sidebar.classList.contains('collapsed') ? '80px' : '280px';
            });

            function updateToggleIcon() {
                const icon = toggleBtn.querySelector('i');
                if (sidebar.classList.contains('collapsed')) {
                    icon.classList.remove('fa-chevron-left');
                    icon.classList.add('fa-chevron-right');
                } else {
                    icon.classList.remove('fa-chevron-right');
                    icon.classList.add('fa-chevron-left');
                }
            }
        }


        // Update current date
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize sidebar toggle
            initSidebarToggle();
        });


        // Mobile Sidebar Toggle
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('show');
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            const sidebar = document.getElementById('sidebar');
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isMenuButton = event.target.closest('.btn');

            if (!isClickInsideSidebar && !isMenuButton && window.innerWidth <= 768) {
                sidebar.classList.remove('show');
            }
        });