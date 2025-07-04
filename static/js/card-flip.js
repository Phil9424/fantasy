document.addEventListener('DOMContentLoaded', function() {
    // Получаем все карточки
    const cardWrappers = document.querySelectorAll('.fifa-card-wrapper');
    
    // Создаем уникальный ключ для текущего пака
    const packId = window.location.pathname.split('/').pop() || 'default';
    const openedCardsKey = 'openedCards_' + packId;
    
    // Проверяем, есть ли сохраненные открытые карты в localStorage
    const openedCards = JSON.parse(localStorage.getItem(openedCardsKey) || '[]');
    
    // Функция для открытия карты
    function flipCard(cardWrapper) {
        const card = cardWrapper.querySelector('.fifa-card');
        const cardId = cardWrapper.getAttribute('data-card-id');
        
        // Добавляем класс для переворота карты
        card.classList.add('flipped');
        
        // Сохраняем ID открытой карты в localStorage
        if (!openedCards.includes(cardId)) {
            openedCards.push(cardId);
            localStorage.setItem(openedCardsKey, JSON.stringify(openedCards));
        }
    }
    
    // Открываем ранее открытые карты
    cardWrappers.forEach(wrapper => {
        const cardId = wrapper.getAttribute('data-card-id');
        if (openedCards.includes(cardId)) {
            flipCard(wrapper);
        }
    });
    
    // Добавляем обработчик клика для каждой карты
    cardWrappers.forEach(wrapper => {
        wrapper.addEventListener('click', function() {
            const card = this.querySelector('.fifa-card');
            
            // Открываем карту только если она еще не открыта
            if (!card.classList.contains('flipped')) {
                flipCard(this);
                
                // Добавляем звуковой эффект
                try {
                    const flipSound = new Audio('/static/sounds/card_flip.mp3');
                    flipSound.play().catch(e => console.log('Звук не может быть воспроизведен:', e));
                } catch (e) {
                    console.log('Ошибка при создании звука:', e);
                }
            }
        });
    });
});
