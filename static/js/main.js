// Main JavaScript for Resto 2.0

// DOM Elements
const themeToggle = document.getElementById('theme-toggle');
const cartBtn = document.getElementById('cart-btn');
const cartModal = document.getElementById('cart-modal');
const closeCartBtn = document.querySelector('.close');
const cartItemsContainer = document.getElementById('cart-items');
const cartCount = document.getElementById('cart-count');
const cartTotalPrice = document.getElementById('cart-total-price');
const clearCartBtn = document.getElementById('clear-cart');
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');
const navActions = document.querySelector('.nav-actions');
const languageSelector = document.getElementById('language');

// Initialize cart from localStorage
let cart = JSON.parse(localStorage.getItem('cart')) || [];

// Update cart count badge
function updateCartCount() {
    const totalItems = cart.reduce((total, item) => total + item.quantity, 0);
    cartCount.textContent = totalItems;
}

// Calculate cart total
function calculateCartTotal() {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
}

// Format price in rupees
function formatPrice(price) {
    return '₹' + price.toFixed(0);
}

// Update cart display
function updateCartDisplay() {
    // Update count badge
    updateCartCount();
    
    // Update cart modal content
    if (cartItemsContainer) {
        if (cart.length === 0) {
            cartItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
            cartTotalPrice.textContent = '₹0';
        } else {
            let cartHTML = '';
            cart.forEach(item => {
                const itemTotal = item.price * item.quantity;
                cartHTML += `
                    <div class="cart-item" data-id="${item.id}">
                        <div class="cart-item-details">
                            <div class="cart-item-name">${item.name}</div>
                            <div class="cart-item-price">₹${Math.round(item.price)} × ${item.quantity}</div>
                            <div class="cart-item-total">Total: ₹${Math.round(itemTotal)}</div>
                        </div>
                        <div class="cart-item-quantity">
                            <button class="quantity-btn decrease">-</button>
                            <span>${item.quantity}</span>
                            <button class="quantity-btn increase">+</button>
                        </div>
                        <div class="cart-item-remove">
                            <i class="fas fa-trash"></i>
                        </div>
                    </div>
                `;
            });
            cartItemsContainer.innerHTML = cartHTML;
            cartTotalPrice.textContent = `₹${Math.round(calculateCartTotal())}`;
            
            // Add event listeners to quantity buttons and remove buttons
            document.querySelectorAll('.quantity-btn.decrease').forEach(btn => {
                btn.addEventListener('click', decreaseQuantity);
            });
            
            document.querySelectorAll('.quantity-btn.increase').forEach(btn => {
                btn.addEventListener('click', increaseQuantity);
            });
            
            document.querySelectorAll('.cart-item-remove').forEach(btn => {
                btn.addEventListener('click', removeCartItem);
            });
        }
    }
    
    // Update order page cart if on order page
    updateOrderPageCart();
    
    // Save cart to localStorage
    localStorage.setItem('cart', JSON.stringify(cart));
}

// Add item to cart
function addToCart(e) {
    const button = e.target;
    const id = button.dataset.id;
    const name = button.dataset.name;
    const price = parseFloat(button.dataset.price);
    
    // Check if item already in cart
    const existingItemIndex = cart.findIndex(item => item.id === id);
    
    if (existingItemIndex > -1) {
        // Increase quantity
        cart[existingItemIndex].quantity += 1;
    } else {
        // Add new item
        cart.push({
            id,
            name,
            price,
            quantity: 1
        });
    }
    
    // Show quick feedback
    const originalText = button.textContent;
    button.textContent = 'Added!';
    button.disabled = true;
    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
    }, 1000);
    
    // Update cart
    updateCartDisplay();
}

// Decrease item quantity
function decreaseQuantity(e) {
    const cartItem = e.target.closest('.cart-item');
    const id = cartItem.dataset.id;
    const itemIndex = cart.findIndex(item => item.id === id);
    
    if (itemIndex > -1) {
        if (cart[itemIndex].quantity > 1) {
            cart[itemIndex].quantity -= 1;
        } else {
            cart.splice(itemIndex, 1);
        }
        updateCartDisplay();
    }
}

// Increase item quantity
function increaseQuantity(e) {
    const cartItem = e.target.closest('.cart-item');
    const id = cartItem.dataset.id;
    const itemIndex = cart.findIndex(item => item.id === id);
    
    if (itemIndex > -1) {
        cart[itemIndex].quantity += 1;
        updateCartDisplay();
    }
}

// Remove item from cart
function removeCartItem(e) {
    const cartItem = e.target.closest('.cart-item');
    const id = cartItem.dataset.id;
    cart = cart.filter(item => item.id !== id);
    updateCartDisplay();
}

// Clear cart
function clearCart() {
    // Clear cart
    cart = [];
    localStorage.setItem('cart', JSON.stringify([]));
    updateCartCount();
    updateCartDisplay();
    updateOrderPageCart();
    if (cartModal) {
        cartModal.style.display = 'none';
    }
}

// Toggle theme (dark/light mode)
function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    
    // Update icon
    if (document.body.classList.contains('dark-mode')) {
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        localStorage.setItem('theme', 'dark');
    } else {
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        localStorage.setItem('theme', 'light');
    }
}

// Toggle mobile menu
function toggleMobileMenu() {
    navLinks.classList.toggle('active');
    navActions.classList.toggle('active');
    hamburger.classList.toggle('active');
}

// Change language
function changeLanguage() {
    const lang = languageSelector.value;
    // In a real app, this would call an API to change the language
    console.log(`Language changed to ${lang}`);
    // For demo purposes, we'll just reload the page
    // window.location.reload();
}

// Initialize menu display
function initializeMenuFilters() {
    // Only run on menu page
    if (document.querySelector('.menu-items')) {
        // Show all menu items by default
        const menuSections = document.querySelectorAll('.category-section');
        menuSections.forEach(section => {
            section.style.display = 'block';
        });
        
        // Setup Add to Cart buttons
        const addToCartButtons = document.querySelectorAll('.add-to-cart');
        addToCartButtons.forEach(button => {
            button.addEventListener('click', addToCart);
        });
    }
}

// Initialize menu filters when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeMenuFilters();
    
    // Initialize cart display
    updateCartDisplay();
    
    // Setup order page navigation if on order page
    setupOrderNavigation();
    
    // Update order page cart if on order page
    updateOrderPageCart();
});

// Order Page Specific Functions
function updateOrderPageCart() {
    // Check if we're on the order page
    const orderCartItems = document.getElementById('order-cart-items');
    if (!orderCartItems) return;
    
    if (cart.length === 0) {
        orderCartItems.innerHTML = '<div class="empty-cart-message">Your cart is empty. <a href="/menu">Browse our menu</a> to add items.</div>';
        document.getElementById('cart-subtotal').textContent = '₹0';
        document.getElementById('cart-tax').textContent = '₹0';
        document.getElementById('order-total').textContent = '₹0';
        
        // Disable continue button
        const nextToDetailsBtn = document.getElementById('next-to-details');
        if (nextToDetailsBtn) {
            nextToDetailsBtn.disabled = true;
        }
    } else {
        let cartHTML = '';
        cart.forEach(item => {
            const itemTotal = Math.round(item.price * item.quantity);
            cartHTML += `
                <div class="cart-item" data-id="${item.id}">
                    <div class="cart-item-details">
                        <div class="cart-item-name">${item.name}</div>
                        <div class="cart-item-price">₹${Math.round(item.price)} × ${item.quantity}</div>
                    </div>
                    <div class="cart-item-total">₹${itemTotal}</div>
                </div>
            `;
        });
        orderCartItems.innerHTML = cartHTML;
        
        // Update totals
        const subtotal = calculateCartTotal();
        const tax = Math.round(subtotal * 0.1); // 10% tax
        const total = subtotal + tax;
        
        document.getElementById('cart-subtotal').textContent = `₹${Math.round(subtotal)}`;
        document.getElementById('cart-tax').textContent = `₹${tax}`;
        document.getElementById('order-total').textContent = `₹${Math.round(total)}`;
        
        // Enable continue button
        const nextToDetailsBtn = document.getElementById('next-to-details');
        if (nextToDetailsBtn) {
            nextToDetailsBtn.disabled = false;
        }
        
        // Also update payment section totals if they exist
        updatePaymentSummary(subtotal, tax, total);
    }
}

function updatePaymentSummary(subtotal, tax, total) {
    const paymentItemsCount = document.getElementById('payment-items-count');
    const paymentSubtotal = document.getElementById('payment-subtotal');
    const paymentTax = document.getElementById('payment-tax');
    const paymentTotal = document.getElementById('payment-total');
    
    if (paymentItemsCount && paymentSubtotal && paymentTax && paymentTotal) {
        const totalItems = cart.reduce((total, item) => total + item.quantity, 0);
        paymentItemsCount.textContent = totalItems;
        paymentSubtotal.textContent = `₹${Math.round(subtotal)}`;
        paymentTax.textContent = `₹${Math.round(tax)}`;
        paymentTotal.textContent = `₹${Math.round(total)}`;
    }
}

// Order process navigation
function setupOrderNavigation() {
    // Check if we're on the order page
    if (!document.querySelector('.order-steps')) return;
    
    const steps = document.querySelectorAll('.step');
    const sections = document.querySelectorAll('.order-section');
    
    // Next to details
    const nextToDetailsBtn = document.getElementById('next-to-details');
    if (nextToDetailsBtn) {
        nextToDetailsBtn.addEventListener('click', () => {
            sections[0].classList.remove('active');
            sections[1].classList.add('active');
            steps[0].classList.remove('active');
            steps[1].classList.add('active');
            window.scrollTo(0, 0);
        });
    }
    
    // Back to cart
    const backToCartBtn = document.getElementById('back-to-cart');
    if (backToCartBtn) {
        backToCartBtn.addEventListener('click', () => {
            sections[1].classList.remove('active');
            sections[0].classList.add('active');
            steps[1].classList.remove('active');
            steps[0].classList.add('active');
            window.scrollTo(0, 0);
        });
    }
    
    // Next to payment
    const nextToPaymentBtn = document.getElementById('next-to-payment');
    if (nextToPaymentBtn) {
        nextToPaymentBtn.addEventListener('click', () => {
            // Validate form
            const customerName = document.getElementById('customer-name');
            const customerEmail = document.getElementById('customer-email');
            const customerPhone = document.getElementById('customer-phone');
            
            if (!customerName.value || !customerEmail.value || !customerPhone.value) {
                alert('Please fill in all required fields.');
                return;
            }
            
            sections[1].classList.remove('active');
            sections[2].classList.add('active');
            steps[1].classList.remove('active');
            steps[2].classList.add('active');
            window.scrollTo(0, 0);
        });
    }
    
    // Back to details
    const backToDetailsBtn = document.getElementById('back-to-details');
    if (backToDetailsBtn) {
        backToDetailsBtn.addEventListener('click', () => {
            sections[2].classList.remove('active');
            sections[1].classList.add('active');
            steps[2].classList.remove('active');
            steps[1].classList.add('active');
            window.scrollTo(0, 0);
        });
    }
    
    // Place order
    const placeOrderBtn = document.getElementById('place-order');
    if (placeOrderBtn) {
        placeOrderBtn.addEventListener('click', () => {
            // In a real app, this would submit the order to the server
            // For demo purposes, we'll just show the confirmation
            sections[2].classList.remove('active');
            sections[3].classList.add('active');
            steps[2].classList.remove('active');
            steps[3].classList.add('active');
            window.scrollTo(0, 0);
            
            // Save current cart for bill
            const orderItems = [...cart];
            const subtotal = calculateCartTotal();
            const tax = Math.round(subtotal * 0.1);
            const total = subtotal + tax;
            
            // Generate order number and update confirmation
            const orderNumber = Math.floor(100000 + Math.random() * 900000);
            document.getElementById('order-number').textContent = orderNumber;
            document.getElementById('bill-order-number').textContent = orderNumber;
            
            // Set current date on bill
            const today = new Date();
            const dateString = today.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            document.getElementById('bill-date').textContent = dateString;
            
            // Set customer name on bill
            const customerName = document.getElementById('customer-name').value;
            document.getElementById('bill-customer-name').textContent = customerName;
            
            // Save order details for bill
            const lastOrder = {
                orderNumber,
                date: dateString,
                customerName,
                items: orderItems.map(item => ({
                    name: item.name,
                    quantity: item.quantity,
                    price: item.price
                })),
                subtotal,
                tax,
                total
            };
            localStorage.setItem('lastOrder', JSON.stringify(lastOrder));
            
            // Update bill content immediately
            updateBillContent();
            
            // Clear cart after successful order
            cart = [];
            localStorage.removeItem('cart');
        });
    }
    
    // Order type radio buttons
    const orderTypeRadios = document.querySelectorAll('input[name="order-type"]');
    const dineInDetails = document.getElementById('dine-in-details');
    const deliveryDetails = document.getElementById('delivery-details');
    
    orderTypeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'dine-in') {
                dineInDetails.classList.remove('hidden');
                deliveryDetails.classList.add('hidden');
            } else if (radio.value === 'delivery') {
                dineInDetails.classList.add('hidden');
                deliveryDetails.classList.remove('hidden');
            } else {
                dineInDetails.classList.add('hidden');
                deliveryDetails.classList.add('hidden');
            }
        });
    });
    
    // Payment method radio buttons
    const paymentMethodRadios = document.querySelectorAll('input[name="payment-method"]');
    const cardPaymentForm = document.getElementById('card-payment-form');
    const upiPaymentForm = document.getElementById('upi-payment-form');
    const paypalPaymentForm = document.getElementById('paypal-payment-form');
    const cashPaymentForm = document.getElementById('cash-payment-form');
    
    paymentMethodRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            // Hide all forms
            cardPaymentForm.classList.add('hidden');
            upiPaymentForm.classList.add('hidden');
            paypalPaymentForm.classList.add('hidden');
            cashPaymentForm.classList.add('hidden');
            
            // Show selected form
            if (radio.value === 'card') {
                cardPaymentForm.classList.remove('hidden');
            } else if (radio.value === 'upi') {
                upiPaymentForm.classList.remove('hidden');
            } else if (radio.value === 'paypal') {
                paypalPaymentForm.classList.remove('hidden');
            } else if (radio.value === 'cash') {
                cashPaymentForm.classList.remove('hidden');
            }
        });
    });
}

// Bill modal
function setupBillModal() {
    const viewBillBtn = document.getElementById('view-bill');
    const downloadBillBtn = document.getElementById('download-bill');
    const billModal = document.getElementById('bill-modal');
    const closeBillBtn = billModal ? billModal.querySelector('.close') : null;
    
    // Remove any existing event listeners
    if (viewBillBtn) {
        viewBillBtn.replaceWith(viewBillBtn.cloneNode(true));
    }
    if (downloadBillBtn) {
        downloadBillBtn.replaceWith(downloadBillBtn.cloneNode(true));
    }
    if (closeBillBtn) {
        closeBillBtn.replaceWith(closeBillBtn.cloneNode(true));
    }
    
    // Get fresh references after replacing elements
    const newViewBillBtn = document.getElementById('view-bill');
    const newDownloadBillBtn = document.getElementById('download-bill');
    const newCloseBillBtn = billModal ? billModal.querySelector('.close') : null;
    
    if (newViewBillBtn && billModal) {
        newViewBillBtn.addEventListener('click', () => {
            updateBillContent();
            billModal.style.display = 'block';
        });
    }
    
    if (newDownloadBillBtn) {
        newDownloadBillBtn.addEventListener('click', generatePDF);
    }
    
    if (newCloseBillBtn && billModal) {
        newCloseBillBtn.addEventListener('click', () => {
            billModal.style.display = 'none';
        });
    }
    
    if (billModal) {
        window.addEventListener('click', (e) => {
            if (e.target === billModal) {
                billModal.style.display = 'none';
            }
        });
    }
}

function updateBillContent() {
    try {
        // Get bill elements
        const billOrderNumber = document.getElementById('bill-order-number');
        const billDate = document.getElementById('bill-date');
        const billCustomerName = document.getElementById('bill-customer-name');
        const billItemsList = document.getElementById('bill-items-list');
        const billSubtotal = document.getElementById('bill-subtotal');
        const billTax = document.getElementById('bill-tax');
        const billTotal = document.getElementById('bill-total');
        
        if (!billOrderNumber || !billDate || !billCustomerName || !billItemsList || 
            !billSubtotal || !billTax || !billTotal) {
            console.error('Required bill elements not found');
            return;
        }
        
        // Get saved order details
        const lastOrder = JSON.parse(localStorage.getItem('lastOrder'));
        if (!lastOrder) {
            console.error('No order details found');
            return;
        }
        
        // Update bill header information
        billOrderNumber.textContent = lastOrder.orderNumber;
        billDate.textContent = lastOrder.date;
        billCustomerName.textContent = lastOrder.customerName;
        
        // Update bill items
        let billItemsHTML = '';
        if (lastOrder.items.length === 0) {
            billItemsHTML = `
                <tr>
                    <td colspan="4" style="text-align: center;">No items in order</td>
                </tr>
            `;
        } else {
            lastOrder.items.forEach(item => {
                if (item && item.name && item.price && item.quantity) {
                    const itemTotal = Math.round(item.price * item.quantity);
                    billItemsHTML += `
                        <tr>
                            <td>${item.name}</td>
                            <td>${item.quantity}</td>
                            <td>₹${Math.round(item.price)}</td>
                            <td>₹${itemTotal}</td>
                        </tr>
                    `;
                }
            });
        }
        billItemsList.innerHTML = billItemsHTML;
        
        // Update bill totals
        billSubtotal.textContent = `₹${Math.round(lastOrder.subtotal)}`;
        billTax.textContent = `₹${lastOrder.tax}`;
        billTotal.textContent = `₹${Math.round(lastOrder.total)}`;
    } catch (error) {
        console.error('Error updating bill content:', error);
    }
}

function generatePDF() {
    const billContent = document.querySelector('.bill-container').cloneNode(true);
    const style = `
        <style>
            .bill-container { font-family: Arial, sans-serif; padding: 20px; }
            .bill-header { text-align: center; margin-bottom: 20px; }
            .bill-info { margin-bottom: 20px; }
            .bill-row { display: flex; justify-content: space-between; margin: 5px 0; }
            .bill-items table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            .bill-items th, .bill-items td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .bill-totals { margin-top: 20px; }
            .bill-footer { text-align: center; margin-top: 20px; }
            .total { font-weight: bold; }
        </style>
    `;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write('<html><head><title>Bill - Resto 2.0</title>');
    printWindow.document.write(style);
    printWindow.document.write('</head><body>');
    printWindow.document.write(billContent.innerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    
    // Wait for content to load then print
    printWindow.onload = function() {
        printWindow.print();
        // printWindow.close();
    };
}

// Menu page functions
function setupMenuFilters() {
    // Check if we're on the menu page
    if (!document.querySelector('.category-tabs')) return;
    
    const categoryTabs = document.querySelectorAll('.category-tab');
    const menuItems = document.querySelectorAll('.menu-item');
    const searchInput = document.getElementById('menu-search');
    const priceFilter = document.getElementById('price-filter');
    const dietaryFilter = document.getElementById('dietary-filter');
    
    // Category filter
    categoryTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab
            categoryTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const category = tab.dataset.category;
            
            // Filter items
            menuItems.forEach(item => {
                if (category === 'all' || item.dataset.category === category) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
    
    // Search filter
    searchInput.addEventListener('input', filterMenuItems);
    
    // Price filter
    priceFilter.addEventListener('change', filterMenuItems);
    
    // Dietary filter
    dietaryFilter.addEventListener('change', filterMenuItems);
    
    function filterMenuItems() {
        const searchTerm = searchInput.value.toLowerCase();
        const priceRange = priceFilter.value;
        const dietary = dietaryFilter.value;
        
        menuItems.forEach(item => {
            const name = item.querySelector('h3').textContent.toLowerCase();
            const description = item.querySelector('p').textContent.toLowerCase();
            const price = parseFloat(item.dataset.price);
            const dietaryTags = item.dataset.dietary;
            
            // Check if matches search term
            const matchesSearch = name.includes(searchTerm) || description.includes(searchTerm);
            
            // Check if matches price range
            let matchesPrice = true;
            if (priceRange === 'low') {
                matchesPrice = price <= 10;
            } else if (priceRange === 'medium') {
                matchesPrice = price > 10 && price <= 20;
            } else if (priceRange === 'high') {
                matchesPrice = price > 20;
            }
            
            // Check if matches dietary preference
            let matchesDietary = true;
            if (dietary !== 'all') {
                matchesDietary = dietaryTags.includes(dietary);
            }
            
            // Show/hide based on all filters
            if (matchesSearch && matchesPrice && matchesDietary) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (themeToggle) {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }
    
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', addToCart);
    });
    
    // Theme toggle
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Cart modal
    if (cartBtn && cartModal) {
        cartBtn.addEventListener('click', () => {
            cartModal.style.display = 'block';
        });
        
        if (closeCartBtn) {
            closeCartBtn.addEventListener('click', () => {
                cartModal.style.display = 'none';
            });
        }
        
        window.addEventListener('click', (e) => {
            if (e.target === cartModal) {
                cartModal.style.display = 'none';
            }
        });
    }
    
    // Clear cart
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', clearCart);
    }
    
    // Mobile menu
    if (hamburger) {
        hamburger.addEventListener('click', toggleMobileMenu);
    }
    
    // Language selector
    if (languageSelector) {
        languageSelector.addEventListener('change', changeLanguage);
    }
    
    // Initialize cart display
    updateCartDisplay();
    
    // Setup order page navigation
    setupOrderNavigation();
    
    // Initialize menu display
    initializeMenuFilters();
    
    // Setup new interactive features
    setupInteractiveFeatures();
    
    // Setup bill modal with a slight delay to ensure DOM is fully loaded
    setTimeout(setupBillModal, 100);
});

// Interactive Features Functions

// QR Scanner Functions
function openQRScanner() {
    const modal = document.getElementById('qr-scanner-modal');
    modal.style.display = 'block';
    startQRScanner();
}

function closeQRScanner() {
    const modal = document.getElementById('qr-scanner-modal');
    modal.style.display = 'none';
    stopQRScanner();
}

function startQRScanner() {
    const video = document.getElementById('qr-video');
    const scannerContainer = document.getElementById('qr-scanner-container');
    const tableInfo = document.getElementById('table-info');
    
    // Request camera access
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(stream => {
            video.srcObject = stream;
            video.play();
            
            // Simulate QR code detection (in real app, use a QR library)
            setTimeout(() => {
                // Simulate successful scan
                const tableData = {
                    number: Math.floor(Math.random() * 20) + 1,
                    section: 'Main Hall',
                    capacity: 4
                };
                
                scannerContainer.style.display = 'none';
                tableInfo.style.display = 'block';
                document.getElementById('table-details').innerHTML = `
                    <strong>Table ${tableData.number}</strong><br>
                    Section: ${tableData.section}<br>
                    Capacity: ${tableData.capacity} people
                `;
                
                // Store table info for ordering
                sessionStorage.setItem('currentTable', JSON.stringify(tableData));
            }, 3000);
        })
        .catch(err => {
            console.error('Camera access denied:', err);
            alert('Camera access is required for QR scanning. Please enable camera permissions.');
        });
}

function stopQRScanner() {
    const video = document.getElementById('qr-video');
    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }
    
    // Reset scanner state
    document.getElementById('qr-scanner-container').style.display = 'block';
    document.getElementById('table-info').style.display = 'none';
}

function startTableOrder() {
    closeQRScanner();
    // Redirect to menu page with table info
    window.location.href = '/menu?table=' + JSON.parse(sessionStorage.getItem('currentTable')).number;
}

// Order Options Functions
function openOrderOptions() {
    const modal = document.getElementById('order-options-modal');
    modal.style.display = 'block';
}

function closeOrderOptions() {
    const modal = document.getElementById('order-options-modal');
    modal.style.display = 'none';
}

function selectOrderType(type) {
    closeOrderOptions();
    if (type === 'pickup') {
        window.location.href = '/menu?type=pickup';
    } else if (type === 'delivery') {
        window.location.href = '/menu?type=delivery';
    }
}

// Loyalty Dashboard Functions
function openLoyaltyDashboard() {
    const modal = document.getElementById('loyalty-modal');
    modal.style.display = 'block';
    loadLoyaltyData();
}

function closeLoyaltyDashboard() {
    const modal = document.getElementById('loyalty-modal');
    modal.style.display = 'none';
}

function loadLoyaltyData() {
    // Simulate loading user loyalty data
    const points = localStorage.getItem('userPoints') || 1250;
    document.getElementById('user-points').textContent = points;
}

function redeemReward(rewardType, pointsCost) {
    const currentPoints = parseInt(document.getElementById('user-points').textContent);
    
    if (currentPoints >= pointsCost) {
        const newPoints = currentPoints - pointsCost;
        localStorage.setItem('userPoints', newPoints);
        document.getElementById('user-points').textContent = newPoints;
        
        let rewardMessage = '';
        switch(rewardType) {
            case 'appetizer':
                rewardMessage = 'Free appetizer voucher added to your account!';
                break;
            case 'discount':
                rewardMessage = '₹200 discount voucher added to your account!';
                break;
            case 'dessert':
                rewardMessage = 'Free dessert voucher added to your account!';
                break;
        }
        
        alert(rewardMessage);
    } else {
        alert('Insufficient points for this reward.');
    }
}

// Order Tracker Functions
function openOrderTracker() {
    const modal = document.getElementById('order-tracker-modal');
    modal.style.display = 'block';
}

function closeOrderTracker() {
    const modal = document.getElementById('order-tracker-modal');
    modal.style.display = 'none';
    document.getElementById('order-status').style.display = 'none';
    document.getElementById('order-id').value = '';
}

function trackOrder() {
    const orderId = document.getElementById('order-id').value.trim();
    
    if (!orderId) {
        alert('Please enter a valid order ID');
        return;
    }
    
    // Simulate order tracking
    const orderStatus = document.getElementById('order-status');
    orderStatus.style.display = 'block';
    
    // Simulate real-time updates
    updateOrderStatus();
}

function updateOrderStatus() {
    // Simulate different order statuses
    const statuses = ['confirmed', 'preparing', 'out-for-delivery', 'delivered'];
    const currentStatus = Math.floor(Math.random() * statuses.length);
    
    const steps = document.querySelectorAll('.status-step');
    steps.forEach((step, index) => {
        step.classList.remove('active');
        if (index <= currentStatus) {
            step.classList.add('completed');
        } else if (index === currentStatus + 1) {
            step.classList.add('active');
        }
    });
    
    // Update estimated time
    const estimatedTimes = ['25-30 minutes', '20-25 minutes', '15-20 minutes', 'Delivered!'];
    document.getElementById('estimated-time').textContent = 
        currentStatus < 3 ? `Estimated delivery: ${estimatedTimes[currentStatus]}` : estimatedTimes[3];
}

// Setup function for all interactive features
function setupInteractiveFeatures() {
    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        const modals = [
            'qr-scanner-modal',
            'order-options-modal', 
            'loyalty-modal',
            'order-tracker-modal'
        ];
        
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (e.target === modal) {
                modal.style.display = 'none';
                
                // Special cleanup for QR scanner
                if (modalId === 'qr-scanner-modal') {
                    stopQRScanner();
                }
            }
        });
    });
    
    // Setup real-time order tracking updates (simulate)
    setInterval(() => {
        const orderModal = document.getElementById('order-tracker-modal');
        if (orderModal.style.display === 'block' && document.getElementById('order-status').style.display === 'block') {
            // Randomly update order status for demo
            if (Math.random() < 0.1) { // 10% chance every interval
                updateOrderStatus();
            }
        }
    }, 5000); // Check every 5 seconds
}

// Vibration Alert Functions
function vibrateDevice(pattern = [200]) {
    // Check if vibration is supported and permission is granted
    if ('vibrate' in navigator) {
        try {
            navigator.vibrate(pattern);
        } catch (error) {
            console.log('Vibration failed:', error);
        }
    }
}

// Function to handle order placement vibration
function orderPlacedVibration() {
    // Short-Long-Short pattern for order placed
    vibrateDevice([100, 100, 200, 100, 100]);
}

// Function to handle order ready vibration
function orderReadyVibration() {
    // Three short pulses for order ready
    vibrateDevice([200, 100, 200, 100, 200]);
}

// Event listeners for order actions
document.addEventListener('DOMContentLoaded', function() {
    // Place Order button click handler
    const placeOrderBtn = document.querySelector('#place-order-btn');
    if (placeOrderBtn) {
        placeOrderBtn.addEventListener('click', function() {
            orderPlacedVibration();
        });
    }

    // Order status change handler
    function checkOrderStatus() {
        // This is a placeholder for order status checking logic
        // In a real implementation, this would check against the server
        const orderStatus = document.querySelector('#order-status');
        if (orderStatus && orderStatus.textContent.includes('Ready')) {
            orderReadyVibration();
        }
    }

    // Check order status periodically if on order tracking page
    if (window.location.pathname.includes('order')) {
        setInterval(checkOrderStatus, 30000); // Check every 30 seconds
    }
});