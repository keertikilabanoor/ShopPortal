// Update cart and wishlist counts
function updateCounts() {
  fetch('/api/cart/count').then(r => r.json()).then(d => {
    document.querySelectorAll('#cartCount').forEach(el => el.textContent = d.count);
  }).catch(() => {});
  fetch('/api/wishlist/count').then(r => r.json()).then(d => {
    document.querySelectorAll('#wishlistCount').forEach(el => el.textContent = d.count);
  }).catch(() => {});
}
updateCounts();

// Auto-dismiss alerts
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(a => {
    let bsAlert = bootstrap.Alert.getOrCreateInstance(a);
    bsAlert.close();
  });
}, 4000);

// Product image thumbnails
document.querySelectorAll('.thumbnail-img').forEach(img => {
  img.addEventListener('click', function () {
    document.querySelectorAll('.thumbnail-img').forEach(i => i.classList.remove('active'));
    this.classList.add('active');
    const main = document.getElementById('mainProductImg');
    if (main) main.src = this.src;
  });
});

// Rating stars
document.querySelectorAll('.star-rating .star').forEach(star => {
  star.addEventListener('click', function () {
    const val = this.dataset.val;
    document.getElementById('ratingInput').value = val;
    document.querySelectorAll('.star-rating .star').forEach(s => {
      s.classList.toggle('text-warning', parseInt(s.dataset.val) <= parseInt(val));
    });
  });
});

// Quantity controls
document.querySelectorAll('.qty-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    const input = this.closest('.qty-group').querySelector('input[type=number]');
    if (!input) return;
    let val = parseInt(input.value) || 1;
    if (this.dataset.action === 'inc') input.value = val + 1;
    else if (val > 1) input.value = val - 1;
  });
});

// Navbar scroll effect
window.addEventListener('scroll', () => {
  const nav = document.getElementById('mainNav');
  if (nav) nav.style.boxShadow = window.scrollY > 50 ? '0 4px 30px rgba(0,0,0,0.4)' : '0 2px 20px rgba(0,0,0,0.3)';
});

// Subcategory dynamic loader
const catSelect = document.getElementById('category_id');
if (catSelect) {
  catSelect.addEventListener('change', function () {
    const subSelect = document.getElementById('subcategory_id');
    if (!subSelect) return;
    fetch('/api/subcategories/' + this.value)
      .then(r => r.json()).then(subs => {
        subSelect.innerHTML = '<option value="">-- Select Subcategory --</option>';
        subs.forEach(s => subSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`);
      });
  });
}
