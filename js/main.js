// Настройки Adsgram (Замените YOUR_ADSGRAM_BLOCK_ID на ваш реальный ID из кабинета)
const ADSGRAM_BLOCK_ID = "YOUR_ADSGRAM_BLOCK_ID";
let AdController = window.Adsgram ? window.Adsgram.init({ blockId: ADSGRAM_BLOCK_ID }) : null;

// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

// Состояние игры (Безопасная загрузка из localStorage с дефолтными значениями)
let state = {
    coins: parseFloat(localStorage.getItem('nk_coins')) || 0,
    diamonds: parseInt(localStorage.getItem('nk_diamonds')) || 0,
    clickLevel: parseInt(localStorage.getItem('nk_click_lvl')) || 1
};

// МАТЕМАТИКА ЭКОНОМИКИ (Формула защиты от миллиардов монет)
// Сила клика растет через квадратный корень, замедляя прогресс с каждым уровнем
function getClickPower() {
    return Math.floor(1 + Math.sqrt(state.clickLevel - 1) * 2);
}

// Стоимость улучшения равна текущему уровню (1 уровень = 1 алмаз, 5 уровень = 5 алмазов)
function getUpgradeCost() {
    return state.clickLevel; 
}

// Функция сохранения прогресса в память браузера
function saveGame() {
    localStorage.setItem('nk_coins', state.coins.toString());
    localStorage.setItem('nk_diamonds', state.diamonds.toString());
    localStorage.setItem('nk_click_lvl', state.clickLevel.toString());
}

// Функция обновления текста и состояния элементов на экране
function updateUI() {
    const coinsEl = document.getElementById('coins');
    const diamondsEl = document.getElementById('diamonds');
    const clickLvlEl = document.getElementById('click-lvl');
    const upgradeBtn = document.getElementById('buy-click-btn');

    if (coinsEl) coinsEl.innerText = Math.floor(state.coins).toLocaleString();
    if (diamondsEl) diamondsEl.innerText = state.diamonds.toString();
    if (clickLvlEl) clickLvlEl.innerText = state.clickLevel.toString();
    
    if (upgradeBtn) {
        const cost = getUpgradeCost();
        upgradeBtn.innerText = `${cost} 💎`;
        upgradeBtn.disabled = state.diamonds < cost;
    }
}

// ЛОГИКА КЛИКА ПО МОНЕТЕ
const coinTrigger = document.getElementById('coin-trigger');
if (coinTrigger) {
    coinTrigger.addEventListener('click', () => {
        state.coins += getClickPower();
        saveGame();
        updateUI();
        // Легкая вибрация телефона при клике для Telegram
        if (tg && tg.HapticFeedback) {
            tg.HapticFeedback.impactOccurred('medium');
        }
    });
}

// МОНЕТИЗАЦИЯ ADSGRAM (Заработок алмазов строго за досмотренное видео)
const adBtn = document.getElementById('ad-btn');
if (adBtn) {
    adBtn.addEventListener('click', async () => {
        if (!AdController) {
            alert("Рекламная сеть загружается или заблокирована. Пожалуйста, подождите.");
            return;
        }

        adBtn.disabled = true;
        adBtn.innerText = "Загрузка видео...";

        try {
            // Ждем завершения показа видеоролика
            await AdController.show(); 
            
            // Награда за успешный просмотр
            state.diamonds += 1; 
            saveGame();
            updateUI();
            
            if (tg && tg.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('success');
            }
        } catch (err) {
            alert("Чтобы получить алмаз, необходимо досмотреть видеорекламу до конца! 💎");
            console.error("Adsgram skip or error:", err);
        } finally {
            adBtn.disabled = false;
            adBtn.innerText = "Получить +1 💎 за видео";
        }
    });
}

// ПОКУПКА АПГРЕЙДА В МАГАЗИНЕ ЗА АЛМАЗЫ
const buyClickBtn = document.getElementById('buy-click-btn');
if (buyClickBtn) {
    buyClickBtn.addEventListener('click', () => {
        const cost = getUpgradeCost();
        if (state.diamonds >= cost) {
            state.diamonds -= cost;
            state.clickLevel += 1;
            saveGame();
            updateUI();
            if (tg && tg.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('success');
            }
        }
    });
}

// Запуск первоначального рендеринга интерфейса при открытии приложения
updateUI();
