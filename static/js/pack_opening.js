// JavaScript для модального окна открытия пака
document.addEventListener('DOMContentLoaded', function() {
    // Обработчики для кнопок покупки паков
    document.querySelectorAll('.buy-pack-btn').forEach(button => {
        button.addEventListener('click', function() {
            const packId = this.dataset.packId;
            const packName = this.dataset.packName;
            const packPrice = this.dataset.packPrice;
            
            // Устанавливаем информацию о паке в модальном окне
            document.getElementById('packName').textContent = packName;
            document.getElementById('packPrice').textContent = packPrice;
            
            // Сохраняем id пака для подтверждения
            document.getElementById('confirmPurchaseBtn').dataset.packId = packId;
            
            // Показываем модальное окно
            const modal = new bootstrap.Modal(document.getElementById('confirmPurchaseModal'));
            modal.show();
        });
    });
    
    // Обработчик для кнопки подтверждения
    document.getElementById('confirmPurchaseBtn').addEventListener('click', function() {
        const packId = this.dataset.packId;
        
        // Закрываем модальное окно подтверждения
        bootstrap.Modal.getInstance(document.getElementById('confirmPurchaseModal')).hide();
        
        // Перенаправляем на страницу открытия пака
        window.location.href = `/open_pack/${packId}`;
    });
});
