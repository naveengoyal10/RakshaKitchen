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

function getCardItemKey(card) {
  const addButton = card.querySelector('.add-item');
  const variantSelect = card.querySelector('.food-variant');
  return `${addButton.dataset.itemName}:${variantSelect?.value || 'standard'}`;
}

function getCardItem(card) {
  return basket.find((item) => item.key === getCardItemKey(card));
}

function syncCardQuantities() {
  document.querySelectorAll('[data-food-card]').forEach((card) => {
    const addButton = card.querySelector('.add-item');
    if (!addButton) return;
    let controls = card.querySelector('.dish-quantity-controls');
    if (!controls) {
      controls = document.createElement('div');
      controls.className = 'dish-quantity-controls';
      controls.innerHTML = '<button type="button" data-card-decrement aria-label="Decrease quantity">−</button><span class="dish-quantity" aria-live="polite">0</span><button type="button" data-card-increment aria-label="Increase quantity">+</button>';
      addButton.before(controls);
    }
    const item = getCardItem(card);
    controls.querySelector('.dish-quantity').textContent = item?.quantity || '0';
    controls.classList.toggle('has-items', Boolean(item));
  });
}

function addCardItem(card) {
  const button = card.querySelector('.add-item');
  const variantSelect = card.querySelector('.food-variant');
  const selectedVariant = variantSelect?.selectedOptions[0];
  const variantId = variantSelect?.value ? Number(variantSelect.value) : null;
  const variantName = variantSelect?.value ? selectedVariant.textContent.split(' · ')[0] : '';
  const itemKey = getCardItemKey(card);
  const existing = basket.find((item) => item.key === itemKey);
  if (existing) existing.quantity += 1;
  else basket.push({key: itemKey, food_item_id: Number(button.dataset.foodItemId), variant_id: variantId, variant_name: variantName, name: button.dataset.itemName, price: selectedVariant?.dataset.variantPrice || button.dataset.itemPrice, quantity: 1});
  saveBasket();
  renderBasket();
}

function updateWhatsAppLink() {
  document.querySelectorAll('.whatsapp-order').forEach((link) => {
    const message = basket.length
      ? `Hello Raksha Kitchen, I would like to enquire about:\n${basket.map((item) => `${item.name} x ${item.quantity}`).join('\n')}`
      : 'Hello Raksha Kitchen, I would like to enquire about placing an order.';
    link.href = `https://wa.me/${document.body.dataset.whatsappNumber}?text=${encodeURIComponent(message)}`;
  });
}

function syncMenuPricing() {
  const pricingUrl = document.body.dataset.menuPricingUrl;
  if (!pricingUrl || !document.querySelector('.premium-menu-item')) return;
  fetch(pricingUrl)
    .then((response) => response.ok ? response.json() : {})
    .then((pricing) => {
      const itemPricing = pricing.items || {};
      const variantPricing = pricing.variants || {};
      document.querySelectorAll('.premium-menu-item').forEach((card) => {
        const itemId = card.querySelector('.add-item')?.dataset.foodItemId;
        const item = itemPricing[itemId];
        const price = card.querySelector('.menu-item-action strong');
        if (!item || !price) return;
        const unitName = item.unit === 'gram' ? 'grams' : 'pieces';
        price.dataset.mainPrice = `₹${item.price} per ${item.unit_quantity} ${unitName}`;
        price.classList.add('unit-price-display');
        updateSelectedVariantPrice(card, price.dataset.mainPrice);
          const baseOption = card.querySelector('.food-variant option[value=""]');
          if (baseOption) baseOption.textContent = `${item.base_option_name || 'Standard'} · ${price.dataset.mainPrice}`;
        card.querySelectorAll('.food-variant option[value]').forEach((option) => {
          const variant = variantPricing[option.value];
          if (!variant) return;
          const variantUnit = variant.unit === 'gram' ? 'grams' : 'pieces';
          const variantName = option.textContent.split(' · ')[0];
          option.dataset.displayPrice = `₹${variant.price} per ${variant.unit_quantity} ${variantUnit}`;
          option.textContent = `${variantName} · ${option.dataset.displayPrice}`;
        });
      });
    })
    .catch(() => {});
}

function updateSelectedVariantPrice(card, fallbackPrice) {
  const price = card.querySelector('.food-meta strong, .menu-item-action strong');
  const select = card.querySelector('.food-variant');
  if (!price || !select) return;
  const selected = select.selectedOptions[0];
  price.textContent = selected?.value ? selected.dataset.displayPrice || selected.dataset.variantPrice : fallbackPrice || price.dataset.mainPrice || price.textContent;
}

function renderBasket() {
  document.querySelectorAll('.basket-count').forEach((count) => {
    count.textContent = basket.reduce((total, item) => total + item.quantity, 0);
  });
  syncCardQuantities();
  updateWhatsAppLink();

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
    addCardItem(button.closest('[data-food-card]'));
    button.innerHTML = 'Added <span>✓</span>';
    window.setTimeout(() => { button.innerHTML = 'Add <span>+</span>'; }, 1200);
  });
});

document.addEventListener('click', (event) => {
  const cardQuantityButton = event.target.closest('[data-card-increment], [data-card-decrement]');
  if (cardQuantityButton) {
    const card = cardQuantityButton.closest('[data-food-card]');
    if (cardQuantityButton.hasAttribute('data-card-increment')) addCardItem(card);
    else {
      const item = getCardItem(card);
      if (item) {
        item.quantity -= 1;
        if (item.quantity <= 0) basket = basket.filter((basketItem) => basketItem.key !== item.key);
        saveBasket();
        renderBasket();
      }
    }
    return;
  }
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
  if (event.target.closest('.food-variant')) {
    const select = event.target.closest('.food-variant');
    updateSelectedVariantPrice(select.closest('[data-food-card]'), select.closest('[data-food-card]').querySelector('.food-meta strong, .menu-item-action strong')?.dataset.mainPrice);
    syncCardQuantities();
    return;
  }
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

document.querySelector('.whatsapp-order')?.addEventListener('click', updateWhatsAppLink);

renderBasket();
syncMenuPricing();
