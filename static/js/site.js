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
  const mergedBasket = new Map();
  basket.forEach((item) => {
    item.key = item.food_item_id
      ? `${Number(item.food_item_id)}:${item.variant_id ? Number(item.variant_id) : 'base'}`
      : item.key || `${item.name}:${item.variant_id || 'base'}`;
    const existing = mergedBasket.get(item.key);
    if (existing) existing.quantity += item.quantity;
    else mergedBasket.set(item.key, item);
  });
  basket = [...mergedBasket.values()];
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
  const addButton = card.querySelector('.add-to-cart');
  const variantSelect = card.querySelector('.food-variant');
  return `${Number(addButton.dataset.foodItemId)}:${variantSelect?.value || 'base'}`;
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
  const button = card.querySelector('.add-to-cart');
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

function showCartToast(message) {
  const toast = document.querySelector('.cart-toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('is-visible');
  window.clearTimeout(showCartToast.timeout);
  showCartToast.timeout = window.setTimeout(() => toast.classList.remove('is-visible'), 1800);
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
  if (!pricingUrl || !document.querySelector('.menu-item-action')) return;
  fetch(`${pricingUrl}?v=unit-pricing-4`, {cache: 'no-store'})
    .then((response) => response.ok ? response.json() : {})
    .then((pricing) => {
      const itemPricing = pricing.items || {};
      const variantPricing = pricing.variants || {};
      document.querySelectorAll('.menu-item-action').forEach((action) => {
        const card = action.closest('[data-food-card]');
        const itemId = card.querySelector('.add-item')?.dataset.foodItemId;
        const item = itemPricing[itemId];
        const price = action.querySelector('strong');
        if (!item || !price) return;
        const unitText = formatUnitText(item.unit, item.unit_quantity);
        price.dataset.mainPrice = `₹${item.price} for ${unitText}`;
        price.classList.add('unit-price-display');
        updateSelectedVariantPrice(card, price.dataset.mainPrice);
          const baseOption = card.querySelector('.food-variant option[value=""]');
          if (baseOption) baseOption.textContent = `${item.base_option_name || 'Standard'} · ${price.dataset.mainPrice}`;
        card.querySelectorAll('.food-variant option[value]').forEach((option) => {
          const variant = variantPricing[option.value];
          if (!variant) return;
          const variantUnitText = formatUnitText(variant.unit, variant.unit_quantity);
          const variantName = option.textContent.split(' · ')[0];
          option.dataset.displayPrice = `₹${variant.price} for ${variantUnitText}`;
          option.textContent = `${variantName} · ${option.dataset.displayPrice}`;
        });
      });
    })
    .catch(() => {});
}

function formatUnitText(unit, quantity) {
  if (unit === 'plate') return 'plate';
  const label = unit === 'gram' ? 'gram' : 'piece';
  return `${quantity} ${quantity === 1 ? label : `${label}s`}`;
}

function updateSelectedVariantPrice(card, fallbackPrice) {
  const price = card.querySelector('.food-meta strong, .menu-item-action strong');
  const select = card.querySelector('.food-variant');
  if (!price || !select) return;
  const selected = select.selectedOptions[0];
  price.textContent = selected?.value ? selected.dataset.displayPrice || selected.dataset.variantPrice : fallbackPrice || price.dataset.mainPrice || price.textContent;
}

function normalizePlateLabels() {
  document.querySelectorAll('.menu-item-action strong, .food-meta strong, .food-variant option').forEach((element) => {
    element.textContent = element.textContent.replace(/per\s+/gi, 'for ').replace(/for\s+1\s+plate(s)?/gi, 'for plate');
  });
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
  container.innerHTML = basket.length ? basket.map((item) => { const label = item.variant_name ? `${item.name} · ${item.variant_name}` : item.name; const safeName = escapeHtml(label); const itemKey = encodeURIComponent(item.key); return `<div class="basket-line"><span>${safeName}</span><div class="basket-line-controls"><button type="button" data-decrement-item="${itemKey}" aria-label="Decrease ${safeName} quantity">−</button><input type="number" min="1" max="999" value="${item.quantity}" data-quantity-item="${itemKey}" aria-label="${safeName} quantity"><button type="button" data-increment-item="${itemKey}" aria-label="Increase ${safeName} quantity">+</button></div><strong>₹${(Number(item.price) * item.quantity).toFixed(2)} <button type="button" data-remove-item="${itemKey}" aria-label="Remove ${safeName}">×</button></strong></div>`; }).join('') : `<p class="basket-empty">Your cart is empty. Add dishes from the <a href="${menuUrl}">menu</a>.</p>`;
  const total = basket.reduce((sum, item) => sum + Number(item.price) * item.quantity, 0);
  const totalElement = document.querySelector('.basket-total strong span');
  if (totalElement) totalElement.textContent = total.toFixed(2);
  const selectedInput = document.querySelector('[name="selected_items"]');
  if (selectedInput) selectedInput.value = basket.map((item) => `${item.name} x ${item.quantity}`).join('\n');
  const cartInput = document.querySelector('[name="cart_data"]');
  if (cartInput) cartInput.value = JSON.stringify(basket.map((item) => ({food_item_id: item.food_item_id || null, name: item.name, variant_id: item.variant_id, quantity: item.quantity})));
}

document.addEventListener('click', (event) => {
  const addButton = event.target.closest('.add-to-cart');
  if (addButton) {
    addCardItem(addButton.closest('[data-food-card]'));
    showCartToast('Added to cart');
    return;
  }
  const buyButton = event.target.closest('.buy-now');
  if (buyButton) {
    addCardItem(buyButton.closest('[data-food-card]'));
    window.location.assign(document.body.dataset.orderUrl);
    return;
  }
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
    const itemKey = decodeURIComponent(quantityButton.dataset.incrementItem || quantityButton.dataset.decrementItem);
    const item = basket.find((basketItem) => basketItem.key === itemKey);
    if (item) {
      item.quantity = Math.min(999, Math.max(1, item.quantity + (quantityButton.dataset.incrementItem ? 1 : -1)));
      saveBasket();
      renderBasket();
    }
    return;
  }
  const removeButton = event.target.closest('[data-remove-item]');
  if (!removeButton) return;
  basket = basket.filter((item) => item.key !== decodeURIComponent(removeButton.dataset.removeItem));
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
  const item = basket.find((basketItem) => basketItem.key === decodeURIComponent(quantityInput.dataset.quantityItem));
  if (item) {
    item.quantity = Math.min(999, Math.max(1, Number.parseInt(quantityInput.value, 10) || 1));
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
normalizePlateLabels();
