// main.js — students will add JavaScript here as features are built

// "See how it works" video modal
(function () {
    var openBtn = document.getElementById("how-it-works-btn");
    var overlay = document.getElementById("how-it-works-modal");
    var closeBtn = document.getElementById("how-it-works-close");
    var iframe = document.getElementById("how-it-works-iframe");

    if (!openBtn || !overlay || !closeBtn || !iframe) return;

    var videoSrc = "https://www.youtube.com/embed/dQw4w9WgXcQ";

    function openModal(event) {
        event.preventDefault();
        iframe.src = videoSrc + "?autoplay=1";
        overlay.classList.add("is-open");
    }

    function closeModal() {
        overlay.classList.remove("is-open");
        iframe.src = "";
    }

    openBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);
    overlay.addEventListener("click", function (event) {
        if (event.target === overlay) closeModal();
    });
})();
