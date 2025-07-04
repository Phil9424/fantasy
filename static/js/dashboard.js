document.addEventListener('DOMContentLoaded', function() {
    // Обработка нажатий на карточки
    initCardActions();
    
    // Обработка кнопки "Посмотреть все карты"
    const showMoreBtn = document.getElementById('showMoreBtn');
    const cardsContainer = document.getElementById('cardsContainer');
    
    if (showMoreBtn && cardsContainer) {
        showMoreBtn.addEventListener('click', function() {
            // Скрыть кнопку
            showMoreBtn.style.display = 'none';
            
            // Загрузить все карты через AJAX
            fetch('/api/user_cards')
                .then(response => response.json())
                .then(data => {
                    // Получить контейнер для карточек
                    const cardsGrid = cardsContainer.querySelector('div');
                    
                    // Добавить все карты
                    data.forEach(card => {
                        // Пропустить карты, которые уже отображаются (первые 8)
                        if (document.querySelector(`[data-card-id="${card.id}"]`)) {
                            return;
                        }
                        
                        const cardWrapper = document.createElement('div');
                        cardWrapper.className = 'fifa-card-wrapper';
                        cardWrapper.dataset.cardId = card.id;
                        cardWrapper.style.display = 'inline-block';
                        
                        const isPrime = card.is_prime ? '<span class="prime-badge">ПРАЙМ</span>' : '';
                        const inTeam = card.in_team ? '<span class="team-badge">В КОМАНДЕ</span>' : '';
                        const onMarket = card.on_market ? '<span class="market-badge">РЫНОК</span>' : '';
                        const stars = '★'.repeat(card.rarity);
                        
                        // Определяем кнопки действий в зависимости от того, на рынке ли карта
                        let actionButtons = '';
                        if (card.on_market) {
                            actionButtons = `
                                <button class="card-action-btn action-remove-market" data-action="remove-market" data-card-id="${card.id}">Снять с продажи</button>
                            `;
                        } else {
                            actionButtons = `
                                <button class="card-action-btn action-delete" data-action="delete" data-card-id="${card.id}">Удалить</button>
                                <button class="card-action-btn action-market" data-action="market" data-card-id="${card.id}">Выставить на рынок</button>
                                <button class="card-action-btn action-sell" data-action="sell" data-card-id="${card.id}" data-price="${card.base_points}">Продать (${Math.floor(card.base_points * 0.1)} монет)</button>
                            `;
                        }
                        
                        cardWrapper.innerHTML = `
                            <div class="fifa-card" data-rarity="${card.rarity}">
                                ${isPrime}
                                ${inTeam}
                                ${onMarket}
                                <div class="player-image-container">
                                    <img src="/static/uploads/${card.image}" 
                                         class="player-image"
                                         alt="${card.name}" 
                                         onerror="handleImageError(this)" 
                                         data-placeholder="/static/images/cards/placeholder.jpg">
                                </div>
                                <div class="card-overlay">
                                    <div class="player-name">${card.name}</div>
                                    <div class="card-rarity">
                                        <span class="stars">${stars}</span>
                                    </div>
                                    <div class="card-price">
                                        <div class="price-value">${card.base_points}</div>
                                        <div class="price-label">ЦЕНА</div>
                                    </div>
                                </div>
                                <div class="card-actions-menu">
                                    ${actionButtons}
                                </div>
                            </div>
                        `;
                        
                        cardsGrid.appendChild(cardWrapper);
                        
                        // Изменяем стиль контейнера для отображения всех карточек
                        cardsContainer.style.overflowX = 'visible';
                        cardsContainer.style.whiteSpace = 'normal';
                    });
                    
                    // Инициализируем обработчики для новых карточек
                    initCardActions();
                })
                .catch(error => {
                    console.error('Ошибка при загрузке карт:', error);
                    showToast('Не удалось загрузить карты', 'danger');
                });
        });
    }
});

// Инициализация обработчиков для карточек
function initCardActions() {
    // Обработка нажатий на карточки
    document.querySelectorAll('.fifa-card-wrapper').forEach(cardWrapper => {
        cardWrapper.addEventListener('click', function(e) {
            // Проверяем, не нажата ли кнопка в меню
            if (e.target.closest('.card-action-btn')) {
                return; // Не обрабатываем клик по карточке, если нажата кнопка
            }
            
            // Скрываем все открытые меню
            document.querySelectorAll('.fifa-card-wrapper.show-actions').forEach(card => {
                if (card !== this) {
                    card.classList.remove('show-actions');
                }
            });
            
            // Переключаем видимость меню для текущей карточки
            this.classList.toggle('show-actions');
        });
    });
    
    // Обработка нажатий на кнопки в меню карточки
    document.querySelectorAll('.card-action-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const action = this.dataset.action;
            const cardId = parseInt(this.dataset.cardId);
            const price = this.dataset.price ? parseInt(this.dataset.price) : 0;
            
            switch(action) {
                case 'delete':
                    if (confirm('Вы уверены, что хотите удалить эту карту? Это действие нельзя отменить.')) {
                        deleteCard(cardId);
                    }
                    break;
                case 'market':
                    putOnMarket(cardId);
                    break;
                case 'remove-market':
                    removeFromMarket(cardId);
                    break;
                case 'sell':
                    sellCard(cardId, price);
                    break;
            }
        });
    });
    
    // Закрытие меню при клике вне карточки
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.fifa-card-wrapper')) {
            document.querySelectorAll('.fifa-card-wrapper.show-actions').forEach(card => {
                card.classList.remove('show-actions');
            });
        }
    });
}

// Удаление карты
function deleteCard(cardId) {
    if (confirm('Вы уверены, что хотите удалить эту карту? Это действие нельзя отменить.')) {
        // Get the CSRF token from the meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        
        if (!csrfToken) {
            console.error('CSRF token not found');
            showToast('Ошибка безопасности. Пожалуйста, обновите страницу.', 'danger');
            return;
        }
        
        // Include the CSRF token in the headers
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        };
        
        fetch(`/api/cards/${cardId}/delete`, {
            method: 'POST',
            headers: headers,
            credentials: 'same-origin'  // Important for including cookies
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Не удалось удалить карту');
                });
            }
            return response.json();
        })
        .then(() => {
            // Remove the card from DOM
            const cardElement = document.querySelector(`.fifa-card-wrapper[data-card-id="${cardId}"]`);
            if (cardElement) {
                cardElement.remove();
            }
            showToast('Карта успешно удалена', 'success');
        })
        .catch(error => {
            console.error('Error deleting card:', error);
            showToast(error.message || 'Не удалось удалить карту', 'danger');
        });
    }
}

// Выставление карты на рынок
function putOnMarket(cardId) {
    // Get the CSRF token from the meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    if (!csrfToken) {
        console.error('CSRF token not found');
        showToast('Ошибка безопасности. Пожалуйста, обновите страницу.', 'danger');
        return;
    }
    
    // Show loading state
    const cardElement = document.querySelector(`.fifa-card-wrapper[data-card-id="${cardId}"]`);
    if (cardElement) {
        cardElement.classList.add('updating');
    }

    // Get card base points for default price
    const cardPoints = cardElement?.querySelector('.price-value')?.textContent || 100;
    const price = parseInt(prompt(`Введите цену для продажи (текущая стоимость: ${cardPoints}):`, cardPoints));
    
    if (isNaN(price) || price <= 0) {
        showToast('Пожалуйста, введите корректную цену', 'warning');
        if (cardElement) cardElement.classList.remove('updating');
        return;
    }

    // Include the CSRF token in the headers
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
    };
    
    fetch(`/api/cards/${cardId}/market`, {
        method: 'POST',
        headers: headers,
        credentials: 'same-origin',
        body: JSON.stringify({ price: price })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Не удалось выставить карту на рынок');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Show success message
            showToast(data.message || 'Карта успешно выставлена на рынок', 'success');
            
            // Reload the page to show updated card status
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            throw new Error(data.error || 'Неизвестная ошибка');
        }
    })
    .catch(error => {
        console.error('Error putting card on market:', error);
        showToast(error.message || 'Не удалось выставить карту на рынок', 'danger');
        
        // Reset loading state
        if (cardElement) {
            cardElement.classList.remove('updating');
        }
    });
}

// Снятие карты с рынка
function removeFromMarket(cardId) {
    if (!confirm('Вы уверены, что хотите снять эту карту с продажи?')) {
        return;
    }

    // Get the CSRF token from the meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    if (!csrfToken) {
        console.error('CSRF token not found');
        showToast('Ошибка безопасности. Пожалуйста, обновите страницу.', 'danger');
        return;
    }
    
    // Show loading state
    const cardElement = document.querySelector(`.fifa-card-wrapper[data-card-id="${cardId}"]`);
    if (cardElement) {
        cardElement.classList.add('updating');
    }

    // Include the CSRF token in the headers
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
    };
    
    fetch(`/api/cards/${cardId}/remove_from_market`, {
        method: 'POST',
        headers: headers,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Не удалось снять карту с продажи');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Карта снята с продажи', 'success');
            // Reload the page to show updated card status
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            throw new Error(data.error || 'Неизвестная ошибка');
        }
    })
    .catch(error => {
        console.error('Error removing card from market:', error);
        showToast(error.message || 'Не удалось снять карту с продажи', 'danger');
        
        // Reset loading state
        if (cardElement) {
            cardElement.classList.remove('updating');
        }
    });
}

// Продажа карты
function sellCard(cardId, price) {
    const sellPrice = Math.floor(parseInt(price) * 0.1); // 10% от стоимости
    
    if (confirm(`Вы уверены, что хотите продать эту карту за ${sellPrice} монет?`)) {
        // Get the CSRF token from the meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        
        if (!csrfToken) {
            console.error('CSRF token not found');
            showToast('Ошибка безопасности. Пожалуйста, обновите страницу.', 'danger');
            return;
        }
        
        // Include the CSRF token in the headers
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        };
        
        fetch(`/api/cards/${cardId}/sell`, {
            method: 'POST',
            headers: headers,
            credentials: 'same-origin'  // Important for including cookies
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Не удалось продать карту');
                });
            }
            return response.json();
        })
        .then(data => {
            // Remove the card from DOM
            const cardElement = document.querySelector(`.fifa-card-wrapper[data-card-id="${cardId}"]`);
            if (cardElement) {
                cardElement.remove();
            }
            
            // Update coins in the UI
            const coinsElement = document.querySelector('.navbar-nav .dropdown-toggle');
            if (coinsElement && data.new_coins !== undefined) {
                const username = coinsElement.textContent.split('(')[0].trim();
                coinsElement.textContent = `${username} (${data.new_coins} монет)`;
            }
            
            showToast(`Карта успешно продана за ${sellPrice} монет`, 'success');
        })
        .catch(error => {
            console.error('Error selling card:', error);
            showToast(error.message || 'Не удалось продать карту', 'danger');
        });
    }
}

// Получение CSRF-токена
function getCSRFToken() {
    const tokenElement = document.querySelector('meta[name="csrf-token"]');
    return tokenElement ? tokenElement.getAttribute('content') : '';
}

// Отображение уведомления
function showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // Создаем контейнер для уведомлений, если его нет
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        toastContainer = container;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove toast after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 150);
    }, 5000);
}
