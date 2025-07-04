// Card game functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize card dragging
    const cards = document.querySelectorAll('.card-draggable');
    const teamSlots = document.querySelectorAll('.team-slot');
    let draggedCard = null;

    // Add drag events to cards
    cards.forEach(card => {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });

    // Add drop events to team slots
    teamSlots.forEach(slot => {
        slot.addEventListener('dragover', handleDragOver);
        slot.addEventListener('dragenter', handleDragEnter);
        slot.addEventListener('dragleave', handleDragLeave);
        slot.addEventListener('drop', handleDrop);
    });

    // Pack opening functionality
    const openPackBtn = document.getElementById('open-pack');
    if (openPackBtn) {
        openPackBtn.addEventListener('click', openPack);
    }

    // Card flip animation for pack opening
    const packCards = document.querySelectorAll('.pack-card');
    if (packCards.length > 0) {
        packCards.forEach((card, index) => {
            // Add delay for each card flip
            setTimeout(() => {
                card.classList.add('flipped');
            }, 300 * index);
        });
    }


    function handleDragStart(e) {
        draggedCard = this;
        this.classList.add('opacity-50');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.innerHTML);
    }

    function handleDragEnd() {
        this.classList.remove('opacity-50');
        draggedCard = null;
    }

    function handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        e.dataTransfer.dropEffect = 'move';
        return false;
    }

    function handleDragEnter(e) {
        e.preventDefault();
        this.classList.add('border-blue-500', 'bg-blue-900/20');
    }

    function handleDragLeave() {
        this.classList.remove('border-blue-500', 'bg-blue-900/20');
    }

    function handleDrop(e) {
        e.stopPropagation();
        e.preventDefault();
        
        if (draggedCard) {
            // If there's already a card in the slot, swap them
            if (this.firstChild) {
                const existingCard = this.firstChild;
                draggedCard.parentNode.appendChild(existingCard);
            }
            
            // Move the dragged card to the new slot
            this.innerHTML = '';
            this.appendChild(draggedCard);
            
            // Update UI
            this.classList.remove('border-blue-500', 'bg-blue-900/20');
            
            updateTeam();
        }
        
        return false;
    }

    function updateTeam() {
        // Here you would typically update the team in your backend
        console.log('Team updated');
        
        // Get all team slots and their contents
        const teamSlots = document.querySelectorAll('.team-slot');
        const team = [];
        
        teamSlots.forEach((slot, index) => {
            const card = slot.querySelector('.card-draggable');
            if (card) {
                team.push({
                    position: index + 1,
                    cardId: card.dataset.cardId
                });
            }
        });
        
        // In a real app, you would send this data to your backend
        // fetch('/api/update-team', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        //     body: JSON.stringify({ team })
        // });
    }

    function openPack() {
        const packContainer = document.getElementById('pack-container');
        const openPackBtn = document.getElementById('open-pack');
        
        if (!packContainer) return;
        
        // Disable button while opening
        openPackBtn.disabled = true;
        openPackBtn.classList.add('opacity-50', 'cursor-not-allowed');
        
        // Clear previous cards
        packContainer.innerHTML = '';
        
        // Show loading state
        packContainer.innerHTML = `
            <div class="flex items-center justify-center h-64">
                <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
        `;
        
        // Simulate API call to open pack
        setTimeout(() => {
            // In a real app, this would be an API call to your backend
            const cards = generateRandomCards(3);
            displayOpenedCards(cards);
            
            // Re-enable button
            openPackBtn.disabled = false;
            openPackBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }, 1500);
    }
    
    function generateRandomCards(count) {
        const mockCards = [
            { id: 1, name: 'Темный Маг', rarity: 'legendary', stars: 5, image: '🧙‍♂️' },
            { id: 2, name: 'Огненный Дракон', rarity: 'epic', stars: 4, image: '🐉' },
            { id: 3, name: 'Лесной Эльф', rarity: 'rare', stars: 3, image: '🧝‍♀️' },
            { id: 4, name: 'Воин Света', rarity: 'common', stars: 2, image: '⚔️' },
            { id: 5, name: 'Ледяная Королева', rarity: 'legendary', stars: 5, image: '👸' },
            { id: 6, name: 'Теневой Убийца', rarity: 'epic', stars: 4, image: '🗡️' },
        ];
        
        const result = [];
        for (let i = 0; i < count; i++) {
            const randomCard = mockCards[Math.floor(Math.random() * mockCards.length)];
            result.push({
                ...randomCard,
                id: randomCard.id + '-' + Date.now() + '-' + i // Make ID unique
            });
        }
        return result;
    }
    
    function displayOpenedCards(cards) {
        const packContainer = document.getElementById('pack-container');
        if (!packContainer) return;
        
        packContainer.innerHTML = `
            <div class="flex flex-wrap justify-center gap-6">
                ${cards.map((card, index) => `
                    <div class="pack-card relative w-48 h-64 perspective-1000" style="transform-style: preserve-3d;">
                        <div class="card-face card-back absolute w-full h-full rounded-lg flex items-center justify-center text-6xl" style="backface-visibility: hidden;">
                            🃏
                        </div>
                        <div class="card-face card-front absolute w-full h-full rounded-lg flex flex-col items-center justify-center p-4 ${getRarityClass(card.rarity)} ${card.stars === 4 ? 'four-star' : ''}" style="backface-visibility: hidden; transform: rotateY(180deg);">
                            <div class="text-6xl mb-4">${card.image}</div>
                            <h3 class="text-lg font-bold text-center">${card.name}</h3>
                            <div class="text-yellow-400 mt-2">${'★'.repeat(card.stars)}</div>
                            <div class="absolute bottom-2 right-2 text-xs opacity-70">${card.rarity}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="mt-8 text-center">
                <button id="close-pack" class="btn btn-primary">Добавить в коллекцию</button>
            </div>
        `;
        
        // Add flip animation with delay
        const packCards = packContainer.querySelectorAll('.pack-card');
        packCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.transform = 'rotateY(180deg)';
            }, 500 + (index * 200));
        });
        
        // Add event listener to close button
        const closeBtn = document.getElementById('close-pack');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                // In a real app, this would add the cards to the user's collection
                alert('Карты добавлены в вашу коллекцию!');
                
                // Reset pack container
                packContainer.innerHTML = `
                    <div class="text-center py-12">
                        <p class="text-lg mb-4">Хотите открыть еще один пак?</p>
                        <button id="open-pack" class="btn btn-primary">Открыть пак (100 монет)</button>
                    </div>
                `;
                
                // Re-attach event listener
                document.getElementById('open-pack').addEventListener('click', openPack);
            });
        }
    }
    
    function getRarityClass(rarity) {
        const classes = {
            'common': 'border-gray-500',
            'rare': 'border-blue-500 shadow-glow',
            'epic': 'border-purple-500 shadow-glow-purple',
            'legendary': 'border-yellow-500 shadow-glow-purple animate-glow'
        };
        return classes[rarity] || 'border-gray-500';
    }
    
    function updateTeam() {
        // In a real app, this would send the updated team to your backend
        const team = [];
        document.querySelectorAll('.team-slot').forEach((slot, index) => {
            const card = slot.querySelector('.card-draggable');
            if (card) {
                team.push({
                    position: index,
                    cardId: card.dataset.cardId
                });
            }
        });
        
        console.log('Team updated:', team);
        // Here you would typically make an API call to update the team
    }
});
