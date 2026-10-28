document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".dashboard-card, .card, .job-card, .role-card, .role").forEach((el, i) => {
    el.style.animationDelay = `${Math.min(i * 70, 560)}ms`;
  });

  // Tiny intersection reveal for sections/cards without adding libraries.
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("cp-visible");
        observer.unobserve(entry.target);
      }
    });
  }, {threshold: .08});
  document.querySelectorAll(".feature, .dashboard-card, .recommendation-card, .job-card, .step").forEach(el => observer.observe(el));
});
