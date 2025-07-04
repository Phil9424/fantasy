// Основной JavaScript файл для Фэнтези Лиги Мафии

// Инициализация Bootstrap тултипов и попоперов
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация тултипов
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Инициализация попоперов
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Анимация для карточек
    animateCards();

    // Обработчики для карточек команды
    setupTeamCardHandlers();

    // Инициализация модальных окон
    setupModals();
});

// Функция для анимации карточек при прокрутке
function animateCards() {
    const cards = document.querySelectorAll('.card-appear');
    
    if (cards.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
}

// Функция для обработки карточек команды
function setupTeamCardHandlers() {
    const teamCards = document.querySelectorAll('.team-card');
    const teamSlots = document.querySelectorAll('.team-slot');
    
    if (teamCards.length === 0 || teamSlots.length === 0) return;

    // Drag and drop для карточек
    teamCards.forEach(card => {
        card.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('text/plain', this.dataset.cardId);
            this.classList.add('dragging');
        });

        card.addEventListener('dragend', function() {
            this.classList.remove('dragging');
        });
    });

    // Обработка слотов команды
    teamSlots.forEach(slot => {
        slot.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });

        slot.addEventListener('dragleave', function() {
            this.classList.remove('drag-over');
        });

        slot.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            
            const cardId = e.dataTransfer.getData('text/plain');
            const card = document.querySelector(`[data-card-id="${cardId}"]`);
            
            if (card && this.children.length === 0) {
                // Клонируем карточку для слота
                const cardClone = card.cloneNode(true);
                cardClone.classList.add('team-slot-card');
                
                // Очищаем слот и добавляем карточку
                this.innerHTML = '';
                this.appendChild(cardClone);
                this.classList.add('filled');
                
                // Обновляем скрытое поле формы
                const slotInput = document.getElementById(`slot-${this.dataset.slotId}`);
                if (slotInput) {
                    slotInput.value = cardId;
                }
            }
        });
    });
}

// Функция для настройки модальных окон
function setupModals() {
    // Инициализация модального окна открытия пака
    const packOpenModal = document.getElementById('packOpenModal');
    
    if (packOpenModal) {
        packOpenModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            if (!button) return;
            
            const packType = button.getAttribute('data-pack-type');
            const packName = button.getAttribute('data-pack-name');
            const packPrice = button.getAttribute('data-pack-price');
            
            const modalTitle = packOpenModal.querySelector('.modal-title');
            const modalPrice = packOpenModal.querySelector('.pack-price');
            const confirmButton = packOpenModal.querySelector('.btn-buy-pack');
            
            if (modalTitle && packName) modalTitle.textContent = `Открыть ${packName}`;
            if (modalPrice && packPrice) modalPrice.textContent = `${packPrice} монет`;
            if (confirmButton && packType) confirmButton.setAttribute('data-pack-type', packType);
        });
    }
}

// Функция для анимации открытия пака
function animatePackOpening(cards) {
    const container = document.getElementById('pack-cards-container');
    
    if (!container || !cards || cards.length === 0) return;
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Добавляем карты с анимацией
    cards.forEach((card, index) => {
        setTimeout(() => {
            const cardElement = document.createElement('div');
            cardElement.className = 'col-md-4 mb-4 card-reveal';
            cardElement.innerHTML = `
                <div class="mafia-card">
                    <span class="mafia-card-rarity">${'★'.repeat(card.rarity)}${'☆'.repeat(5 - card.rarity)}</span>
                    <img src="/static/images/cards/${card.image}" class="mafia-card-image" alt="${card.name}">
                    <div class="mafia-card-content">
                        <h5>${card.name}</h5>
                        <div class="mafia-card-stats">
                            <div class="mafia-card-stat">АТК: ${card.attack}</div>
                            <div class="mafia-card-stat">ЗЩТ: ${card.defense}</div>
                            <div class="mafia-card-stat">УДЧ: ${card.luck}</div>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(cardElement);
            
            // Звуковой эффект
            playSound('card-reveal');
        }, index * 800);
    });
}

// Функция для воспроизведения звуков
function playSound(soundName) {
    const sounds = {
        'card-reveal': '/static/sounds/card-reveal.mp3',
        'pack-open': '/static/sounds/pack-open.mp3',
        'victory': '/static/sounds/victory.mp3',
        'coins': '/static/sounds/coins.mp3'
    };
    
    if (sounds[soundName]) {
        const audio = new Audio(sounds[soundName]);
        audio.play().catch(e => console.log('Ошибка воспроизведения звука:', e));
    }
}

// Функция для отображения уведомлений
function showNotification(message, type = 'info', duration = 3000) {
    const notificationContainer = document.getElementById('notification-container');
    
    if (!notificationContainer) {
        // Создаем контейнер, если его нет
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Добавляем в контейнер
    notificationContainer.appendChild(notification);
    
    // Автоматически скрываем через указанное время
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        
        // Удаляем из DOM после анимации
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
    
    // Обработчик для кнопки закрытия
    notification.querySelector('.btn-close').addEventListener('click', () => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
}

// Функция для обработки покупки пака
function buyPack(packType) {
    // Отправка запроса на сервер
    fetch(`/open_pack/${packType}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при открытии пака');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Воспроизводим звук открытия пака
            playSound('pack-open');
            
            // Анимируем карты
            animatePackOpening(data.cards);
            
            // Обновляем количество монет
            updateCoins(data.coins);
            
            // Показываем уведомление
            showNotification('Пак успешно открыт!', 'success');
        } else {
            showNotification(data.message || 'Ошибка при открытии пака', 'danger');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Произошла ошибка при открытии пака', 'danger');
    });
}

// Функция для обновления количества монет
function updateCoins(coins) {
    const coinsElement = document.getElementById('user-coins');
    if (coinsElement) {
        // Анимация изменения монет
        const currentCoins = parseInt(coinsElement.textContent);
        const diff = coins - currentCoins;
        
        if (diff !== 0) {
            // Создаем элемент для анимации
            const diffElement = document.createElement('span');
            diffElement.className = diff > 0 ? 'text-success' : 'text-danger';
            diffElement.textContent = diff > 0 ? `+${diff}` : diff;
            diffElement.style.position = 'absolute';
            diffElement.style.right = '0';
            diffElement.style.opacity = '0';
            diffElement.style.transform = 'translateY(0)';
            diffElement.style.transition = 'opacity 1s ease, transform 1s ease';
            
            coinsElement.parentNode.style.position = 'relative';
            coinsElement.parentNode.appendChild(diffElement);
            
            // Запускаем анимацию
            setTimeout(() => {
                diffElement.style.opacity = '1';
                diffElement.style.transform = 'translateY(-20px)';
                
                // Обновляем значение монет
                coinsElement.textContent = coins;
                
                // Воспроизводим звук
                playSound('coins');
                
                // Удаляем элемент после анимации
                setTimeout(() => {
                    diffElement.remove();
                }, 1000);
            }, 100);
        }
    }
}

// Функция для обновления команды
function updateTeam(formData) {
    fetch('/update_team', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при обновлении команды');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification('Команда успешно обновлена!', 'success');
            
            // Перезагружаем страницу или обновляем UI
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(data.message || 'Ошибка при обновлении команды', 'danger');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Произошла ошибка при обновлении команды', 'danger');
    });
}

// Функция для фильтрации карт в коллекции
function filterCards() {
    const searchInput = document.getElementById('card-search');
    const rarityFilter = document.getElementById('rarity-filter');
    const sortBy = document.getElementById('sort-by');
    
    if (!searchInput || !rarityFilter || !sortBy) return;
    
    const searchTerm = searchInput.value.toLowerCase();
    const rarity = rarityFilter.value;
    const sort = sortBy.value;
    
    const cards = document.querySelectorAll('.collection-card');
    
    cards.forEach(card => {
        const cardName = card.querySelector('.card-title').textContent.toLowerCase();
        const cardRarity = card.dataset.rarity;
        
        // Применяем фильтры
        const matchesSearch = cardName.includes(searchTerm);
        const matchesRarity = rarity === 'all' || cardRarity === rarity;
        
        // Показываем или скрываем карту
        if (matchesSearch && matchesRarity) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
    
    // Сортировка карт
    const cardsArray = Array.from(cards).filter(card => card.style.display !== 'none');
    
    if (sort === 'name-asc') {
        cardsArray.sort((a, b) => {
            const nameA = a.querySelector('.card-title').textContent;
            const nameB = b.querySelector('.card-title').textContent;
            return nameA.localeCompare(nameB);
        });
    } else if (sort === 'name-desc') {
        cardsArray.sort((a, b) => {
            const nameA = a.querySelector('.card-title').textContent;
            const nameB = b.querySelector('.card-title').textContent;
            return nameB.localeCompare(nameA);
        });
    } else if (sort === 'rarity-asc') {
        cardsArray.sort((a, b) => parseInt(a.dataset.rarity) - parseInt(b.dataset.rarity));
    } else if (sort === 'rarity-desc') {
        cardsArray.sort((a, b) => parseInt(b.dataset.rarity) - parseInt(a.dataset.rarity));
    }
    
    // Переупорядочиваем карты в DOM
    const container = cards[0].parentNode;
    cardsArray.forEach(card => container.appendChild(card));
}

// Обработчики событий для фильтров
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('card-search');
    const rarityFilter = document.getElementById('rarity-filter');
    const sortBy = document.getElementById('sort-by');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterCards);
    }
    
    if (rarityFilter) {
        rarityFilter.addEventListener('change', filterCards);
    }
    
    if (sortBy) {
        sortBy.addEventListener('change', filterCards);
    }
});
