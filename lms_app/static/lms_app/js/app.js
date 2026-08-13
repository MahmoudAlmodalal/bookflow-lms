(() => {
    const sidebar = document.querySelector("#sidebar");
    const overlay = document.querySelector(".sidebar-overlay");
    const toggles = document.querySelectorAll("[data-sidebar-toggle]");

    const toggleSidebar = () => {
        sidebar?.classList.toggle("is-open");
        overlay?.classList.toggle("is-visible");
    };

    toggles.forEach((toggle) => toggle.addEventListener("click", toggleSidebar));

    const price = document.querySelector("#rental-price");
    const days = document.querySelector("#rental-days");
    const total = document.querySelector("#total-rental");

    const updateRentalTotal = () => {
        if (!price || !days || !total) return;
        const dailyPrice = Number.parseFloat(price.value) || 0;
        const rentalDays = Number.parseInt(days.value, 10) || 0;
        total.value = dailyPrice && rentalDays ? (dailyPrice * rentalDays).toFixed(2) : "";
    };

    price?.addEventListener("input", updateRentalTotal);
    days?.addEventListener("input", updateRentalTotal);
})();
