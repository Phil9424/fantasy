document.addEventListener('DOMContentLoaded', function() {
    // Form Elements
    const nameInput = document.getElementById('name');
    const imageInput = document.getElementById('image');
    const photoPositionInput = document.getElementById('photo_position');
    const countryCodeInput = document.getElementById('country_code');

    // Preview Elements
    const previewName = document.getElementById('preview-name');
    const previewPhoto = document.getElementById('preview-photo');
    const previewFlag = document.getElementById('preview-flag');

    // --- Update Preview --- //
    function updateNamePreview() {
        if (previewName && nameInput) {
            previewName.textContent = nameInput.value || 'Имя Игрока';
        }
    }

    function updateRarityPreview() {
        const previewCard = document.getElementById('preview-card');
        const cardBody = document.querySelector('.user-card-item .card-body');
        if (!previewCard || !cardBody) return;
        
        const rarity = document.getElementById('rarity').value;
        let bgImage = 'card_bg_bronze.png';
        
        // Remove all rarity classes first
        previewCard.classList.remove('bronze', 'silver', 'gold', 'platinum');
        
        if (rarity === '2') {
            bgImage = 'card_bg_silver.png';
            previewCard.classList.add('silver');
        } else if (rarity === '3') {
            bgImage = 'card_bg_gold.png';
            previewCard.classList.add('gold');
        } else if (rarity === '4') {
            // For 4-star cards, use platinum class
            bgImage = 'platinum_shield.png';
            previewCard.classList.add('platinum');
        } else if (rarity === '5') {
            // For 5-star cards, you might want to add another special class
            bgImage = 'card_bg_gold.png';
            previewCard.classList.add('gold');
        } else {
            previewCard.classList.add('bronze');
        }
        
        if (rarity === '4') {
            // For platinum cards, we don't need to set the bg-image as it's handled by the CSS
            previewCard.style.removeProperty('--bg-image');
        } else {
            previewCard.style.setProperty('--bg-image', `url(${window.location.origin}/static/images/${bgImage})`);
        }
    }

    function updateImagePreview(event) {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                if (previewPhoto) {
                    previewPhoto.style.backgroundImage = `url(${e.target.result})`;
                    // Reset position when new image is loaded
                    previewPhoto.style.backgroundPosition = '50% 50%';
                    if (photoPositionInput) {
                        photoPositionInput.value = '50% 50%';
                    }
                }
            };
            reader.readAsDataURL(this.files[0]);
        }
    }

    // --- Draggable Photo Logic --- //
    let isDragging = false;
    let startX, startY;
    let startBgX, startBgY;

    if (previewPhoto) {
                previewPhoto.addEventListener('mousedown', function(e) {
            e.preventDefault();
            isDragging = true;
            this.style.cursor = 'grabbing';

            startX = e.clientX;
            startY = e.clientY;

            // Get the computed pixel values for the background position.
            // This correctly handles initial values in percentages (e.g., '50% 50%').
            const computedStyle = window.getComputedStyle(this);
            startBgX = parseFloat(computedStyle.backgroundPositionX);
            startBgY = parseFloat(computedStyle.backgroundPositionY);
        });

        document.addEventListener('mousemove', function(e) {
            if (isDragging) {
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;

                // Calculate new position in pixels
                const newBgX = startBgX + dx;
                const newBgY = startBgY + dy;

                const newPos = `${newBgX}px ${newBgY}px`;
                previewPhoto.style.backgroundPosition = newPos;
                
                if (photoPositionInput) {
                    photoPositionInput.value = newPos;
                }
            }
        });

        document.addEventListener('mouseup', function() {
            if (isDragging) {
                isDragging = false;
                previewPhoto.style.cursor = 'grab';
            }
        });

        previewPhoto.addEventListener('mouseleave', function() {
            if (isDragging) {
                isDragging = false;
                previewPhoto.style.cursor = 'grab';
            }
        });
    }

    // --- Event Listeners --- //
    if (nameInput) {
        nameInput.addEventListener('input', updateNamePreview);
    }
    
    // Add rarity change listener
    const rarityInput = document.getElementById('rarity');
    if (rarityInput) {
        rarityInput.addEventListener('change', updateRarityPreview);
        // Initialize preview on load
        updateRarityPreview();
    }
    if (imageInput) {
        imageInput.addEventListener('change', updateImagePreview);
    }

    // Update flag preview when country changes
    if (countryCodeInput && previewFlag) {
        countryCodeInput.addEventListener('change', function() {
            const countryCode = this.value.toLowerCase();
            previewFlag.src = `/static/images/flags/${countryCode}.png`;
            previewFlag.alt = this.value;
        });
    }

    // Initial call to set the name on page load
    updateNamePreview();
});
