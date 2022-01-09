document.addEventListener('DOMContentLoaded', function() {

    if (window.location.pathname != "/") {
        document.querySelectorAll('.nav-link').forEach(function(nav_link) {
            if (window.location.pathname === nav_link.getAttribute("href").substring(2).substring(nav_link.getAttribute("href").substring(2).indexOf("/"))) {
                nav_link.className += " active";
                nav_link.setAttribute("aria-current", "page");
                nav_link.style.textDecoration = "underline"; 
            }
        });
    }

    if (window.location.pathname.split("/")[1] === "ai") {
        document.querySelector(".navbar").className = document.querySelector(".navbar").className.replace("bg-teal", "bg-danger")
    }

    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl)
    })
});