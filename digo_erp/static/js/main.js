document.addEventListener("DOMContentLoaded", function() {
    // 1. Sidebar Toggle Logic
    const sidebar = document.getElementById("sidebar");
    const sidebarCollapseBtn = document.getElementById("sidebarCollapse");
    
    // Create Backdrop if it doesn't exist
    let backdrop = document.querySelector(".sidebar-backdrop");
    if (!backdrop) {
        backdrop = document.createElement("div");
        backdrop.className = "sidebar-backdrop";
        document.body.appendChild(backdrop);
    }

    if (sidebarCollapseBtn) {
        sidebarCollapseBtn.addEventListener("click", function() {
            sidebar.classList.toggle("active");
            
            // Show/hide backdrop on mobile screens
            if (window.innerWidth <= 991) {
                if (sidebar.classList.contains("active")) {
                    backdrop.classList.add("active");
                } else {
                    backdrop.classList.remove("active");
                }
            }
        });
    }

    // Close sidebar when clicking on backdrop
    backdrop.addEventListener("click", function() {
        sidebar.classList.remove("active");
        backdrop.classList.remove("active");
    });

    // Handle resize events to remove backdrop on desktop
    window.addEventListener("resize", function() {
        if (window.innerWidth > 991) {
            backdrop.classList.remove("active");
            if (sidebar.classList.contains("active")) {
                // Keep sidebar open or closed on desktop based on user preference, 
                // but usually desktop toggle just hides it, we can keep its state.
            }
        } else {
            // On mobile, if sidebar is not active, ensure backdrop is hidden
            if (!sidebar.classList.contains("active")) {
                backdrop.classList.remove("active");
            } else {
                backdrop.classList.add("active");
            }
        }
    });

    // 2. Theme Toggle Logic
    const themeToggleBtn = document.getElementById("themeToggle");
    const currentTheme = localStorage.getItem("theme") || "light";

    // Set initial theme
    if (currentTheme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
        document.documentElement.setAttribute("data-bs-theme", "dark");
        if (themeToggleBtn) {
            themeToggleBtn.innerHTML = '<i class="bi bi-sun-fill"></i>';
        }
    } else {
        document.documentElement.setAttribute("data-theme", "light");
        document.documentElement.setAttribute("data-bs-theme", "light");
        if (themeToggleBtn) {
            themeToggleBtn.innerHTML = '<i class="bi bi-moon-fill"></i>';
        }
    }

    // Toggle event
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", function() {
            let theme = document.documentElement.getAttribute("data-theme");
            
            if (theme === "dark") {
                document.documentElement.setAttribute("data-theme", "light");
                document.documentElement.setAttribute("data-bs-theme", "light");
                localStorage.setItem("theme", "light");
                themeToggleBtn.innerHTML = '<i class="bi bi-moon-fill"></i>';
                
                // Add micro-animation for the icon
                themeToggleBtn.firstElementChild.style.animation = "none";
                setTimeout(() => themeToggleBtn.firstElementChild.style.animation = "fadeIn 0.3s", 10);
            } else {
                document.documentElement.setAttribute("data-theme", "dark");
                document.documentElement.setAttribute("data-bs-theme", "dark");
                localStorage.setItem("theme", "dark");
                themeToggleBtn.innerHTML = '<i class="bi bi-sun-fill"></i>';
                
                // Add micro-animation for the icon
                themeToggleBtn.firstElementChild.style.animation = "none";
                setTimeout(() => themeToggleBtn.firstElementChild.style.animation = "fadeIn 0.3s", 10);
            }
        });
    }

    // 3. Optional: Add subtle entry animations to table rows
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(10px)';
        row.style.transition = 'all 0.3s ease-out';
        
        setTimeout(() => {
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, 50 + (index * 30)); // Staggered animation
    });
});
