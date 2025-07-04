// Функции для работы с уведомлениями

// Ключ для хранения уведомлений в localStorage
const NOTIFICATIONS_STORAGE_KEY = 'mafia_fantasy_notifications';
const READ_NOTIFICATIONS_STORAGE_KEY = 'mafia_fantasy_read_notifications';

// Получение уведомлений с сервера
async function fetchNotifications() {
    try {
        // Отправляем запрос к API для получения непрочитанных уведомлений
        const response = await fetch('/api/notifications/unread');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('Ошибка при получении уведомлений');
        }
        
        // Преобразуем данные в нужный формат
        const notifications = data.notifications.map(notification => ({
            id: notification.id,
            type: notification.type,
            title: notification.title,
            time: new Date(notification.created_at).toLocaleString('ru-RU'),
            read: notification.is_read,
            link: notification.link || '#',
            icon: notification.icon || getIconForType(notification.type)
        }));
        
        return notifications;
    } catch (error) {
        console.error('Ошибка при получении уведомлений:', error);
        return [];
    }
}

// Получение иконки в зависимости от типа уведомления
function getIconForType(type) {
    switch (type) {
        case 'card':
            return 'bi-trophy-fill text-warning';
        case 'coins':
            return 'bi-coin text-success';
        case 'market_listing':
            return 'bi-tag-fill text-info';
        case 'market_sale':
            return 'bi-cart-check-fill text-primary';
        case 'market_purchase':
            return 'bi-bag-check-fill text-primary';
        case 'pack':
            return 'bi-box-seam-fill text-danger';
        case 'transfer':
            return 'bi-arrow-left-right text-success';
        case 'daily_bonus':
            return 'bi-calendar-check-fill text-success';
        case 'system':
            return 'bi-bell-fill text-secondary';
        default:
            return 'bi-bell-fill text-secondary';
    }
}

// Обновление счетчика непрочитанных уведомлений
function updateNotificationCount(count) {
    const countElement = document.getElementById('notifications-count');
    if (countElement) {
        countElement.textContent = count;
        if (count > 0) {
            countElement.classList.remove('d-none');
        } else {
            countElement.classList.add('d-none');
        }
    }
}

// Отметить уведомление как прочитанное
async function markAsRead(notificationId) {
    try {
        // Отправляем запрос на сервер для отметки уведомления как прочитанного
        const response = await fetch(`/api/notifications/read/${notificationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('Ошибка при отметке уведомления как прочитанного');
        }
        
        console.log(`Уведомление ${notificationId} отмечено как прочитанное`);
        
        // Скрываем элемент уведомления в интерфейсе
        const notificationItem = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
        if (notificationItem) {
            // Сохраняем ссылку для перехода
            const link = notificationItem.getAttribute('href');
            
            // Скрываем уведомление
            notificationItem.remove();
            
            // Переходим по ссылке, если она есть
            if (link && link !== '#') {
                window.location.href = link;
            }
        }
        
        // Обновляем список уведомлений
        loadNotifications();
    } catch (error) {
        console.error('Ошибка при отметке уведомления как прочитанного:', error);
    }
}

// Отметить все уведомления как прочитанные
async function markAllAsRead() {
    try {
        // Отправляем запрос на сервер для отметки всех уведомлений как прочитанных
        const response = await fetch('/api/notifications/read-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('Ошибка при отметке всех уведомлений как прочитанных');
        }
        
        console.log('Все уведомления отмечены как прочитанные');
        
        // Обновляем список уведомлений
        loadNotifications();
        
        // Переходим на страницу всех уведомлений
        window.location.href = '/notifications/all';
    } catch (error) {
        console.error('Ошибка при отметке всех уведомлений как прочитанных:', error);
    }
}

// Рендеринг уведомлений в выпадающем меню
function renderNotifications(notifications) {
    const container = document.getElementById('notifications-container');
    const loadingElement = document.getElementById('notifications-loading');
    const emptyElement = document.getElementById('notifications-empty');
    const template = document.getElementById('notification-template');
    
    // Скрываем индикатор загрузки
    if (loadingElement) {
        loadingElement.classList.add('d-none');
    }
    
    // Удаляем существующие уведомления (кроме служебных элементов)
    document.querySelectorAll('.notification-item').forEach(item => {
        item.remove();
    });
    
    // Фильтруем только непрочитанные уведомления
    const unreadNotifications = notifications.filter(n => !n.read);
    
    // Если нет непрочитанных уведомлений, показываем сообщение
    if (!unreadNotifications || unreadNotifications.length === 0) {
        if (emptyElement) {
            emptyElement.classList.remove('d-none');
        }
        return;
    }
    
    // Скрываем сообщение о пустом списке
    if (emptyElement) {
        emptyElement.classList.add('d-none');
    }
    
    // Создаем элементы уведомлений из шаблона только для непрочитанных
    unreadNotifications.forEach(notification => {
        if (template) {
            const clone = document.importNode(template.content, true);
            const notificationItem = clone.querySelector('.notification-item');
            const icon = clone.querySelector('.bi');
            const title = clone.querySelector('.notification-title');
            const time = clone.querySelector('.notification-time');
            
            notificationItem.dataset.id = notification.id;
            notificationItem.href = notification.link;
            
            icon.classList.add(...notification.icon.split(' '));
            title.textContent = notification.title;
            time.textContent = notification.time;
            
            container.appendChild(clone);
        }
    });
    
    // Добавляем обработчики событий для новых элементов
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', async (e) => {
            const notificationId = item.dataset.id;
            await markAsRead(notificationId);
        });
    });
}

// Добавление нового уведомления
async function addNotification(type, title, time, link, icon) {
    try {
        // Отправляем запрос на сервер для создания нового уведомления
        const response = await fetch('/api/notifications/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ 
                type, 
                title, 
                content: '', 
                link: link || '#', 
                icon: icon || getIconForType(type) 
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('Ошибка при создании уведомления');
        }
        
        // Обновляем список уведомлений в интерфейсе
        loadNotifications();
        
        console.log(`Добавлено новое уведомление: ${title}`);
        
        return data.notification;
    } catch (error) {
        console.error('Ошибка при добавлении уведомления:', error);
        return null;
    }
}

// Получение иконки для типа уведомления
function getIconForType(type) {
    switch (type) {
        case 'card':
            return 'bi-trophy-fill text-warning';
        case 'coins':
            return 'bi-coin text-success';
        case 'market':
            return 'bi-cart-check-fill text-primary';
        case 'pack':
            return 'bi-box-seam-fill text-danger';
        case 'transfer':
            return 'bi-arrow-left-right text-success';
        case 'sale':
            return 'bi-tag-fill text-info';
        default:
            return 'bi-bell-fill text-secondary';
    }
}

// Загрузка и отображение уведомлений
async function loadNotifications() {
    try {
        // Получаем уведомления с сервера
        const notifications = await fetchNotifications();
        
        // Отображаем уведомления в интерфейсе
        renderNotifications(notifications);
        
        // Обновляем счетчик непрочитанных уведомлений
        const unreadCount = notifications.filter(n => !n.read).length;
        updateNotificationCount(unreadCount);
        
        return notifications;
    } catch (error) {
        console.error('Ошибка при загрузке уведомлений:', error);
        return [];
    }
}

// Инициализация уведомлений при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    // Загружаем и отображаем уведомления
    await loadNotifications();
    
    // Обработка клика по колокольчику (обновление уведомлений)
    const notificationsDropdown = document.getElementById('notificationsDropdown');
    if (notificationsDropdown) {
        notificationsDropdown.addEventListener('click', async () => {
            // Обновляем уведомления при каждом клике по колокольчику
            await loadNotifications();
        });
    }
    
    // Обработчик клика по ссылке "Показать все уведомления"
    const showAllNotificationsLink = document.querySelector('.show-all-notifications');
    if (showAllNotificationsLink) {
        showAllNotificationsLink.addEventListener('click', function(e) {
            // Отмечаем все уведомления как прочитанные перед переходом
            markAllAsRead();
            // Не предотвращаем действие по умолчанию, чтобы произошел переход по ссылке
        });
    }
    
    // Добавляем функцию для глобального доступа
    window.addNotification = addNotification;
});
