// Toastr configuration
toastr.options = {
    "closeButton": true,
    "progressBar": true,
    "positionClass": "toast-top-right",
    "timeOut": "3000"
};

// Platform preview interaction
document.querySelectorAll('.platform-card').forEach(card => {
    card.addEventListener('click', function() {
        document.querySelectorAll('.platform-card').forEach(c => c.classList.remove('active'));
        this.classList.add('active');
    });
});

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('carouselForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            const topic = document.getElementById('topic').value.trim();
            if (!topic) {
                e.preventDefault();
                toastr.error('Please enter a topic');
                document.getElementById('topic').focus();
                return false;
            }
        });
    }
});

// Range input display
const slideCount = document.getElementById('slide_count');
if (slideCount) {
    const slideCountValue = document.getElementById('slideCountValue');
    slideCount.addEventListener('input', function() {
        slideCountValue.textContent = this.value;
    });
}