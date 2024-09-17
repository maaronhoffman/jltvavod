document.addEventListener('DOMContentLoaded', function() {
    const colorThief = new ColorThief();
    const showItems = document.querySelectorAll('.show-item');
    const episodeThumbnails = document.querySelectorAll('.show-detail-episode-thumbnail');

    showItems.forEach(item => {
        const img = item.querySelector('.image-wrapper img');
        if (img) {
            if (img.complete) {
                setGlowColor(item, img, colorThief);
            } else {
                img.addEventListener('load', () => setGlowColor(item, img, colorThief));
            }
        }
    });

    episodeThumbnails.forEach(img => {
        if (img.complete) {
            setGlowColor(img.closest('.show-detail-episode-card'), img, colorThief);
        } else {
            img.addEventListener('load', () => setGlowColor(img.closest('.show-detail-episode-card'), img, colorThief));
        }
    });
});

function setGlowColor(item, img, colorThief) {
    const themeColor = item.dataset.themeColor;
    if (themeColor) {
        item.style.setProperty('--glow-color', themeColor);
        console.log(`Glow color set for ${img.alt}: ${themeColor}`);
    } else {
        try {
            const dominantColor = colorThief.getColor(img);
            const [r, g, b] = dominantColor;
            
            // Increase brightness while maintaining hue
            const brightness = Math.max(r, g, b);
            const scale = Math.max(1, 255 / brightness);
            const adjustedColor = [
                Math.min(255, Math.round(r * scale)),
                Math.min(255, Math.round(g * scale)),
                Math.min(255, Math.round(b * scale))
            ];
            
            const glowColor = `rgba(${adjustedColor[0]}, ${adjustedColor[1]}, ${adjustedColor[2]}, 0.3)`;
            item.style.setProperty('--glow-color', glowColor);
            console.log(`Glow color set for ${img.alt}: ${glowColor}`);
        } catch (error) {
            console.error(`Error setting glow color for ${img.alt}:`, error);
        }
    }
}
