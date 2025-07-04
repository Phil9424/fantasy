// Примеры использования уведомлений для разных операций

// Функция для создания примеров уведомлений
function createNotificationExamples() {
    // Проверяем, что функция addNotification доступна
    if (typeof window.addNotification !== 'function') {
        console.error('Функция addNotification не найдена');
        return;
    }

    // Пример уведомления о покупке пака
    document.getElementById('example-pack-btn').addEventListener('click', async () => {
        await window.addNotification(
            'pack',
            'Вы открыли пак "Премиум" и получили 5 новых карт',
            `${new Date().toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`,
            '/dashboard#cards'
        );
        
        // Показываем сообщение об успешном создании уведомления
        showToast('Уведомление о паке создано!');
    });
    
    // Пример уведомления о продаже карты
    document.getElementById('example-market-sell-btn').addEventListener('click', async () => {
        await window.addNotification(
            'market',
            'Ваша карта "Майкл Корлеоне" продана за 250 монет',
            `${new Date().toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`,
            '/market'
        );
        
        // Показываем сообщение об успешном создании уведомления
        showToast('Уведомление о продаже карты создано!');
    });
    
    // Пример уведомления о выставлении карты на продажу
    document.getElementById('example-market-list-btn').addEventListener('click', async () => {
        await window.addNotification(
            'market',
            'Вы выставили карту "Вито Корлеоне" на продажу за 300 монет',
            `${new Date().toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`,
            '/market'
        );
        
        // Показываем сообщение об успешном создании уведомления
        showToast('Уведомление о выставлении карты создано!');
    });
    
    // Пример уведомления о переводе монет
    document.getElementById('example-coins-transfer-btn').addEventListener('click', async () => {
        await window.addNotification(
            'transfer',
            'Вы перевели 150 монет пользователю MafiaGod',
            `${new Date().toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`,
            '/dashboard'
        );
        
        // Показываем сообщение об успешном создании уведомления
        showToast('Уведомление о переводе монет создано!');
    });
    
    // Пример уведомления о получении монет
    document.getElementById('example-coins-receive-btn').addEventListener('click', async () => {
        await window.addNotification(
            'coins',
            'Вы получили 100 монет от пользователя GodFather',
            `${new Date().toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit' })}`,
            '/dashboard'
        );
        
        // Показываем сообщение об успешном создании уведомления
        showToast('Уведомление о получении монет создано!');
    });
}

// Функция для отображения всплывающего сообщения
function showToast(message) {
    const toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) {
        // Создаем контейнер для тостов, если его нет
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    // Создаем элемент toast
    const toastId = `toast-${Date.now()}`;
    const toastElement = document.createElement('div');
    toastElement.className = 'toast show';
    toastElement.id = toastId;
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    
    toastElement.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">Уведомление</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Закрыть"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Добавляем toast в контейнер
    document.getElementById('toast-container').appendChild(toastElement);
    
    // Автоматически скрываем через 3 секунды
    setTimeout(() => {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.remove();
        }
    }, 3000);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    createNotificationExamples();
});
