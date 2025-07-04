// Utility functions for card generation and display

/**
 * Generates HTML for a small card (135x198px) used in pack openings
 * @param {Object} card - Card data object
 * @returns {string} HTML string for the card
 */
function generateSmallCard(card) {
    const rarityClass = getRarityClass(card.rarity);
    const bgImage = getRarityBackground(card.rarity);
    
    // Ensure image paths are properly formatted
    const playerImage = card.image ? 
        (card.image.startsWith('/static/') ? card.image : `/static/${card.image}`) : 
        '/static/images/default_player.png';
    
    // Get photo position from card data or use default
    let photoPosition = '50% 50%';
    if (card.photo_position) {
        console.log(`Original photo position: ${card.photo_position}`);
        // Use the position as is, but ensure it's properly formatted
        const positions = card.photo_position.trim().split(/\s+/);
        if (positions.length === 2) {
            photoPosition = positions.join(' ');
            console.log(`Using photo position: ${photoPosition}`);
        }
    }
    
    // Разделяем позицию на x и y
    const [posX, posY] = photoPosition.split(' ');
    
    return `
    <div class="card small-card ${rarityClass}" style="--bg-image: url('${bgImage}');">
        <div class="card-header">
            <div class="card-photo" 
                 style="--player-photo-vertical: ${posY || '50%'}; 
                        background-image: url('${playerImage}');
                        background-position: center ${posY || '50%'};
                        background-position-x: center !important;
                        background-position-y: ${posY || '50%'} !important;">
            </div>
            <img class="card-logo" src="/static/images/logo_new_pa.png" alt="Logo">
        </div>
        <div class="card-body">
            <div class="card-title">${card.title || ''}</div>
            <div class="card-name">${card.name || 'Игрок'}</div>
            ${card.is_prime ? '<div class="card-top-player">Топовый игрок</div>' : ''}
            ${card.country_code ? `<img class="card-flag" src="/static/images/flags/${card.country_code.toLowerCase()}.png" alt="${card.country_code}">` : ''}
        </div>
    </div>`;
}

/**
 * Returns the appropriate CSS class for the card's rarity
 * @param {number} rarity - The card's rarity (1-5)
 * @returns {string} CSS class name
 */
function getRarityClass(rarity) {
    if (rarity >= 4) return 'platinum';
    if (rarity === 3) return 'gold';
    if (rarity === 2) return 'silver';
    return 'bronze';
}

/**
 * Returns the background image path for the card's rarity
 * @param {number} rarity - The card's rarity (1-5)
 * @returns {string} Path to the background image
 */
function getRarityBackground(rarity) {
    if (rarity >= 4) return '/static/images/card_bg_gold.png'; // Using gold background for platinum for now
    if (rarity === 3) return '/static/images/card_bg_gold.png';
    if (rarity === 2) return '/static/images/card_bg_silver.png';
    return '/static/images/card_bg_bronze.png';
}

// Export functions for use in other modules
export {
    generateSmallCard,
    getRarityClass,
    getRarityBackground
};
