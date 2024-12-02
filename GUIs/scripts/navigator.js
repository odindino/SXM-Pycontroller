const NavigatorModule = {
    init() {
        this.setupTabHandlers();
    },

    setupTabHandlers() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(e.target.dataset.target);
            });
        });
    },

    switchTab(targetId) {
        // 更新導航連結狀態
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.target === targetId);
        });

        // 切換內容區塊
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.toggle('active', section.id === targetId);
        });
    }
};

export default NavigatorModule;