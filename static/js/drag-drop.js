// Drag and drop functionality for team management

document.addEventListener('DOMContentLoaded', function() {
    // Initialize drag and drop when the DOM is fully loaded
    initDragAndDrop();
});

function initDragAndDrop() {
    // Make team slots droppable
    const teamSlots = document.querySelectorAll('.team-slot');
    teamSlots.forEach(slot => {
        slot.addEventListener('dragover', handleDragOver);
        slot.addEventListener('drop', handleDrop);
        slot.addEventListener('dragenter', handleDragEnter);
        slot.addEventListener('dragleave', handleDragLeave);
    });

    // Make cards draggable
    const cards = document.querySelectorAll('.fifa-card-wrapper');
    cards.forEach(card => {
        card.setAttribute('draggable', 'true');
        card.addEventListener('dragstart', handleDragStart);
    });
}

function handleDragStart(e) {
    e.dataTransfer.setData('text/plain', this.dataset.cardId);
    this.classList.add('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
}

function handleDrop(e) {
    e.preventDefault();
    this.classList.remove('drag-over');
    
    const cardId = e.dataTransfer.getData('text/plain');
    const slotId = this.dataset.slot;
    
    // Call the API to update the team
    updateTeamSlot(slotId, cardId);
}

function handleDragEnter(e) {
    e.preventDefault();
    this.classList.add('drag-over');
}

function handleDragLeave() {
    this.classList.remove('drag-over');
}

function updateTeamSlot(slotId, cardId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    if (!csrfToken) {
        console.error('CSRF token not found');
        return;
    }
    
    fetch('/api/team/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({
            slot: slotId,
            card_id: cardId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload the page to show updated team
            window.location.reload();
        } else {
            console.error('Failed to update team:', data.error);
            alert('Не удалось обновить команду: ' + (data.error || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('Error updating team:', error);
        alert('Произошла ошибка при обновлении команды');
    });
}

// Make the function available globally
window.initDragAndDrop = initDragAndDrop;
