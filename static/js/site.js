const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.site-nav');
if (toggle) {
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', open);
  });
}

const basketKey = 'raksha-kitchen-enquiry-list';
let basket = [];
try {
  const storedBasket = JSON.parse(localStorage.getItem(basketKey) || '[]');
  basket = Array.isArray(storedBasket) ? storedBasket.filter((item) => item && Number.isInteger(item.quantity) && item.quantity > 0) : [];
} catch (error) {
  localStorage.removeItem(basketKey);
}

if (document.querySelector('[data-confirmation-page]')) {
  basket = [];
  localStorage.removeItem(basketKey);
}

function saveBasket() {
  localStorage.setItem(basketKey, JSON.stringify(basket));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  })[character]);
}

function renderBasket() {
  document.querySelectorAll('.basket-count').forEach((count) => {
    count.textContent = basket.reduce((total, item) => total + item.quantity, 0);
  });

  const container = document.querySelector('.basket-items');
  if (!container) return;
  const menuUrl = document.body.dataset.menuUrl;
  container.innerHTML = basket.length ? basket.map((item) => { const safeName = escapeHtml(item.name); const itemKey = encodeURIComponent(item.name); return `<div class="basket-line"><span>${safeName}</span><div class="basket-line-controls"><button type="button" data-decrement-item="${itemKey}" aria-label="Decrease ${safeName} quantity">−</button><input type="number" min="1" value="${item.quantity}" data-quantity-item="${itemKey}" aria-label="${safeName} quantity"><button type="button" data-increment-item="${itemKey}" aria-label="Increase ${safeName} quantity">+</button></div><strong>₹${(Number(item.price) * item.quantity).toFixed(2)} <button type="button" data-remove-item="${itemKey}" aria-label="Remove ${safeName}">×</button></strong></div>`; }).join('') : `<p class="basket-empty">Your list is empty. Add dishes from the <a href="${menuUrl}">menu</a>.</p>`;
  const total = basket.reduce((sum, item) => sum + Number(item.price) * item.quantity, 0);
  const totalElement = document.querySelector('.basket-total strong span');
  if (totalElement) totalElement.textContent = total.toFixed(2);
  const selectedInput = document.querySelector('[name="selected_items"]');
  if (selectedInput) selectedInput.value = basket.map((item) => `${item.name} x ${item.quantity}`).join('\n');
  const cartInput = document.querySelector('[name="cart_data"]');
  if (cartInput) cartInput.value = JSON.stringify(basket.map((item) => ({food_item_id: item.food_item_id || null, name: item.name, variant_id: item.variant_id, quantity: item.quantity})));
}

document.querySelectorAll('.add-item').forEach((button) => {
  button.addEventListener('click', () => {
    const variantSelect = button.closest('[data-food-card]')?.querySelector('.food-variant');
    const selectedVariant = variantSelect?.selectedOptions[0];
    const variantId = variantSelect?.value ? Number(variantSelect.value) : null;
    const variantName = variantSelect?.value ? selectedVariant.textContent.split(' · ')[0] : '';
    const itemKey = `${button.dataset.itemName}:${variantId || 'standard'}`;
    const existing = basket.find((item) => item.key === itemKey);
    if (existing) existing.quantity += 1;
    else basket.push({key: itemKey, food_item_id: Number(button.dataset.foodItemId), variant_id: variantId, variant_name: variantName, name: button.dataset.itemName, price: selectedVariant?.dataset.variantPrice || button.dataset.itemPrice, quantity: 1});
    saveBasket();
    renderBasket();
    button.innerHTML = 'Added <span>✓</span>';
    window.setTimeout(() => { button.innerHTML = 'Add <span>+</span>'; }, 1200);
  });
});

document.addEventListener('click', (event) => {
  const quantityButton = event.target.closest('[data-increment-item], [data-decrement-item]');
  if (quantityButton) {
    const itemName = decodeURIComponent(quantityButton.dataset.incrementItem || quantityButton.dataset.decrementItem);
    const item = basket.find((basketItem) => basketItem.name === itemName);
    if (item) {
      item.quantity = Math.max(1, item.quantity + (quantityButton.dataset.incrementItem ? 1 : -1));
      saveBasket();
      renderBasket();
    }
    return;
  }
  const removeButton = event.target.closest('[data-remove-item]');
  if (!removeButton) return;
  basket = basket.filter((item) => item.name !== decodeURIComponent(removeButton.dataset.removeItem));
  saveBasket();
  renderBasket();
});

document.addEventListener('change', (event) => {
  const quantityInput = event.target.closest('[data-quantity-item]');
  if (!quantityInput) return;
  const item = basket.find((basketItem) => basketItem.name === decodeURIComponent(quantityInput.dataset.quantityItem));
  if (item) {
    item.quantity = Math.max(1, Number.parseInt(quantityInput.value, 10) || 1);
    saveBasket();
    renderBasket();
  }
});

document.querySelector('.clear-list')?.addEventListener('click', () => {
  basket = [];
  saveBasket();
  renderBasket();
});

document.querySelector('[data-order-form]')?.addEventListener('submit', (event) => {
  if (!basket.length) return;
  const message = `Hello Raksha Kitchen, I would like to enquire about:\n${basket.map((item) => `${item.name} x ${item.quantity}`).join('\n')}`;
  document.querySelector('.whatsapp-order').href = `https://wa.me/${document.body.dataset.whatsappNumber}?text=${encodeURIComponent(message)}`;
});

renderBasket();
