// Import card utilities
import { generateSmallCard } from './card_utils.js';

document.addEventListener('DOMContentLoaded', function() {
    const packContainer = document.querySelector('.pack-container');
    if (!packContainer) return;

    // Check for saved opened cards in localStorage
    const packId = document.querySelector('#pack-id')?.value || 'default';
    const openedCardsKey = 'openedCards_' + packId;
    let openedCards = [];
    
    try {
        openedCards = JSON.parse(localStorage.getItem(openedCardsKey) || '[]');
    } catch (e) {
        console.error('Error reading from localStorage:', e);
    }
    
    // Get all card wrappers
    const cardWrappers = document.querySelectorAll('.card-wrapper');
    
    // Function to flip a card
    function flipCard(cardWrapper) {
        const cardId = cardWrapper.getAttribute('data-card-id');
        const cardBack = cardWrapper.querySelector('.card-back');
        const cardFront = cardWrapper.querySelector('.card-front');
        
        if (cardBack && cardFront) {
            // Add flip animation class
            cardWrapper.classList.add('flipped');
            
            // Add opened card to localStorage
            if (!openedCards.includes(cardId)) {
                openedCards.push(cardId);
                try {
                    localStorage.setItem(openedCardsKey, JSON.stringify(openedCards));
                } catch (e) {
                    console.error('Error writing to localStorage:', e);
                }
            }
            
            // Play flip sound
            try {
                const flipSound = new Audio('/static/sounds/card_flip.mp3');
                flipSound.play().catch(e => console.log('Audio play failed:', e));
            } catch (e) {
                console.log('Could not play sound:', e);
            }
        }
    }
    
    // Initialize cards
    cardWrappers.forEach(wrapper => {
        const cardId = wrapper.getAttribute('data-card-id');
        let cardData;
        
        try {
            const cardJson = wrapper.getAttribute('data-card');
            cardData = JSON.parse(cardJson);
            
            // Debug: Log the card data and photo position
            console.log('Card data:', cardData);
            console.log('Photo position:', cardData.photo_position || 'default (50% 50%)');
            
            // Ensure photo_position is set and properly formatted
            if (!cardData.photo_position) {
                cardData.photo_position = '50% 50%';
            } else if (cardData.photo_position.includes(' ')) {
                // Ensure proper formatting of photo position
                const [x, y] = cardData.photo_position.split(' ');
                cardData.photo_position = `${x.trim()} ${y.trim()}`;
            }
        } catch (e) {
            console.error('Error parsing card data:', e);
            console.error('Raw data:', wrapper.getAttribute('data-card'));
            return;
        }
        
        // Create card back (shirt)
        const cardBack = document.createElement('div');
        cardBack.className = 'card-back';
        cardBack.innerHTML = `
            <div class="card-back-content">
                <div class="card-back-icon">
                    <i class="bi bi-question-diamond"></i>
                </div>
                <div class="card-back-text">Нажмите,<br>чтобы открыть</div>
            </div>
        `;
        
        // Create card front with the actual card
        const cardFront = document.createElement('div');
        cardFront.className = 'card-front';
        
        // Ensure the card data has all required fields
        const cardDataWithDefaults = {
            ...cardData,
            rarity: cardData.rarity || 1,
            title: cardData.title || '',
            name: cardData.name || 'Игрок',
            image: cardData.image || '/static/images/default_player.png',
            photo_position: cardData.photo_position || '50% 50%',
            is_prime: cardData.is_prime || false,
            country_code: cardData.country_code || ''
        };
        
        cardFront.innerHTML = generateSmallCard(cardDataWithDefaults);
        
        // Clear wrapper and append new elements
        wrapper.innerHTML = '';
        wrapper.appendChild(cardBack);
        wrapper.appendChild(cardFront);
        
        // Add prime class if card is prime
        if (cardData.is_prime) {
            wrapper.classList.add('is-prime');
        }
        
        // Show card if it was previously opened
        if (openedCards.includes(cardId)) {
            wrapper.classList.add('flipped');
        } else {
            // Add click handler for unopened cards
            wrapper.style.cursor = 'pointer';
            wrapper.addEventListener('click', function() {
                if (!wrapper.classList.contains('flipped')) {
                    flipCard(wrapper);
                }
            });
        }
    });
});
