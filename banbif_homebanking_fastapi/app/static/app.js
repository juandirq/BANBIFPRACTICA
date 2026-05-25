document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const sidebar = document.getElementById("sidebar");
    const menuBtn = document.getElementById("menuBtn");
    const overlay = document.getElementById("overlay");
    const themeBtn = document.getElementById("themeBtn");
    const toast = document.getElementById("toast");

    const savedTheme = localStorage.getItem("banbif_theme");
    if (savedTheme === "dark") body.classList.add("dark");

    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            body.classList.toggle("dark");
            localStorage.setItem("banbif_theme", body.classList.contains("dark") ? "dark" : "light");
            showToast("Tema actualizado");
        });
    }

    if (menuBtn && sidebar && overlay) {
        menuBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
            overlay.classList.toggle("show");
        });

        overlay.addEventListener("click", () => {
            sidebar.classList.remove("open");
            overlay.classList.remove("show");
        });
    }

    const currentPath = window.location.pathname;
    document.querySelectorAll(".nav-item").forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }
    });

    const reveals = document.querySelectorAll(".reveal");
    const revealObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add("visible");
        });
    }, { threshold: 0.12 });

    reveals.forEach(item => revealObserver.observe(item));

    document.querySelectorAll(".counter").forEach(counter => {
        const target = Number(counter.dataset.target || 0);
        const isMoney = target % 1 !== 0 || target > 100;
        let current = 0;
        const step = Math.max(target / 50, 1);

        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }

            counter.textContent = isMoney
                ? "S/ " + current.toFixed(2)
                : Math.round(current);
        }, 20);
    });

    const passwordInput = document.getElementById("passwordInput");
    const togglePassword = document.getElementById("togglePassword");

    if (passwordInput && togglePassword) {
        togglePassword.addEventListener("click", () => {
            const visible = passwordInput.type === "text";
            passwordInput.type = visible ? "password" : "text";
            togglePassword.textContent = visible ? "Ver" : "Ocultar";
        });
    }

    const slides = document.querySelectorAll(".slide");
    const dots = document.querySelectorAll(".dot");
    let currentSlide = 0;

    function showSlide(index) {
        slides.forEach(s => s.classList.remove("active"));
        dots.forEach(d => d.classList.remove("active"));

        if (slides[index]) slides[index].classList.add("active");
        if (dots[index]) dots[index].classList.add("active");
        currentSlide = index;
    }

    if (slides.length > 0) {
        dots.forEach(dot => {
            dot.addEventListener("click", () => {
                showSlide(Number(dot.dataset.dot));
            });
        });

        setInterval(() => {
            const next = (currentSlide + 1) % slides.length;
            showSlide(next);
        }, 4200);
    }

    document.querySelectorAll("[data-amount]").forEach(btn => {
        btn.addEventListener("click", () => {
            const amountInput = document.getElementById("depositAmount");
            if (amountInput) {
                amountInput.value = btn.dataset.amount;
                showToast("Monto seleccionado: S/ " + btn.dataset.amount);
            }
        });
    });

    const filter = document.getElementById("movementFilter");
    const table = document.getElementById("movementTable");

    if (filter && table) {
        filter.addEventListener("input", () => {
            const term = filter.value.toLowerCase();
            Array.from(table.querySelectorAll("tr")).slice(1).forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(term) ? "" : "none";
            });
        });
    }

    const globalSearch = document.getElementById("globalSearch");
    if (globalSearch) {
        globalSearch.addEventListener("keydown", e => {
            if (e.key !== "Enter") return;

            const value = globalSearch.value.toLowerCase();

            if (value.includes("ahorro")) window.location.href = "/ahorros";
            else if (value.includes("credito")) window.location.href = "/creditos";
            else if (value.includes("transfer")) window.location.href = "/transferencias";
            else if (value.includes("perfil")) window.location.href = "/perfil";
            else if (value.includes("core")) window.location.href = "/core";
            else showToast("Modulo no encontrado");
        });
    }

    document.querySelectorAll("[data-toast]").forEach(btn => {
        btn.addEventListener("click", () => showToast(btn.dataset.toast));
    });

    const notifyBtn = document.getElementById("notifyBtn");
    if (notifyBtn) {
        notifyBtn.addEventListener("click", () => {
            showToast("No tienes notificaciones pendientes");
        });
    }

    function showToast(message) {
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add("show");

        setTimeout(() => {
            toast.classList.remove("show");
        }, 2300);
    }
});

// ================================
// BANBIF NEXT LEVEL INTERACTION
// ================================

window.addEventListener("load", () => {
    const loader = document.getElementById("screenLoader");
    if (loader) {
        setTimeout(() => {
            loader.classList.add("hide");
        }, 650);
    }
});

document.addEventListener("mousemove", (e) => {
    const glow = document.getElementById("cursorGlow");
    if (glow) {
        glow.style.left = e.clientX + "px";
        glow.style.top = e.clientY + "px";
    }
});

document.querySelectorAll(".tilt-card").forEach(card => {
    card.addEventListener("mousemove", (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((y - centerY) / centerY) * -6;
        const rotateY = ((x - centerX) / centerX) * 6;

        card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
    });

    card.addEventListener("mouseleave", () => {
        card.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg) translateY(0)";
    });
});

const registerPassword = document.getElementById("registerPassword");
const strengthBar = document.getElementById("strengthBar");
const strengthText = document.getElementById("strengthText");

if (registerPassword && strengthBar && strengthText) {
    registerPassword.addEventListener("input", () => {
        const value = registerPassword.value;
        let score = 0;

        if (value.length >= 6) score += 25;
        if (value.length >= 10) score += 25;
        if (/[A-Z]/.test(value)) score += 15;
        if (/[0-9]/.test(value)) score += 20;
        if (/[^A-Za-z0-9]/.test(value)) score += 15;

        strengthBar.style.width = score + "%";

        if (score === 0) {
            strengthText.textContent = "Pendiente";
        } else if (score < 40) {
            strengthText.textContent = "Debil";
        } else if (score < 75) {
            strengthText.textContent = "Media";
        } else {
            strengthText.textContent = "Fuerte";
        }
    });
}

const toggleRegisterPassword = document.getElementById("toggleRegisterPassword");

if (toggleRegisterPassword && registerPassword) {
    toggleRegisterPassword.addEventListener("click", () => {
        const visible = registerPassword.type === "text";
        registerPassword.type = visible ? "password" : "text";
        toggleRegisterPassword.textContent = visible ? "Ver" : "Ocultar";
    });
}

document.querySelectorAll(".magnetic").forEach(btn => {
    btn.addEventListener("mousemove", (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;

        btn.style.transform = `translate(${x * .08}px, ${y * .15}px)`;
    });

    btn.addEventListener("mouseleave", () => {
        btn.style.transform = "translate(0,0)";
    });
});
