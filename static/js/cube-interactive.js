document.addEventListener('DOMContentLoaded', () => {
    // Configuration
    const STICKER_COLORS = ['W', 'R', 'G', 'Y', 'O', 'B'];
    const DEFAULT_FACE_COLORS = { U: 'W', R: 'R', F: 'G', D: 'Y', L: 'O', B: 'B' };
    const FACE_ORDER = ['U', 'L', 'F', 'R', 'B', 'D'];

    const cubeElement = document.querySelector('.cube');
    const sceneElement = document.querySelector('.scene');
    const outputElement = document.getElementById('output');
    const solveBtn = document.getElementById('solveBtn');
    const resetBtn = document.getElementById('resetBtn');

    // --- Cube Initialization ---
    function createStickers() {
        FACE_ORDER.forEach(face => {
            const grid = document.querySelector(`.grid[data-face="${face}"]`);
            grid.innerHTML = ''; // Clear previous stickers
            for (let i = 0; i < 9; ++i) {
                const sticker = document.createElement('div');
                sticker.className = 'sticker';
                const defaultColor = DEFAULT_FACE_COLORS[face];
                sticker.dataset.value = defaultColor;
                sticker.style.backgroundColor = getHexColor(defaultColor);
                sticker.addEventListener('click', () => cycleStickerColor(sticker));
                grid.appendChild(sticker);
            }
        });
    }

    function cycleStickerColor(sticker) {
        const currentColor = sticker.dataset.value;
        const currentIndex = STICKER_COLORS.indexOf(currentColor);
        const nextIndex = (currentIndex + 1) % STICKER_COLORS.length;
        const nextColor = STICKER_COLORS[nextIndex];
        sticker.dataset.value = nextColor;
        sticker.style.backgroundColor = getHexColor(nextColor);
    }

    function getHexColor(code) {
        return {
            W: '#f5f6fa', R: '#e84118', G: '#4cd137',
            Y: '#fbc531', O: '#e67e22', B: '#0097e6'
        }[code] || '#333';
    }

    // --- Cube Validation and API Call ---
    function getCubeState() {
        const cube = {};
        FACE_ORDER.forEach(face => {
            const grid = document.querySelector(`.grid[data-face="${face}"]`);
            const stickers = [...grid.children].map(s => s.dataset.value);
            cube[face] = [stickers.slice(0, 3), stickers.slice(3, 6), stickers.slice(6, 9)];
        });
        return cube;
    }

    function isValidCube(cube) {
        const counts = STICKER_COLORS.reduce((acc, color) => ({ ...acc, [color]: 0 }), {});
        for (const face of Object.values(cube)) {
            for (const row of face) {
                for (const color of row) {
                    if (counts[color] !== undefined) {
                        counts[color]++;
                    }
                }
            }
        }
        return Object.values(counts).every(count => count === 9);
    }

    async function solveCube() {
        solveBtn.disabled = true;
        outputElement.textContent = "Validating and solving...";

        const cubeState = getCubeState();

        if (!isValidCube(cubeState)) {
            outputElement.textContent = "Error: Invalid cube state. Each of the 6 colors must be used exactly 9 times.";
            solveBtn.disabled = false;
            return;
        }

        try {
            const response = await fetch('/solve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cube: cubeState })
            });

            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const result = await response.json();
            if (result.error) {
                outputElement.textContent = `Error: ${result.error}`;
            } else if (result.solution && result.solution.length > 0) {
                outputElement.textContent = `Solution Sequence: ${result.sequence}`;
            } else {
                outputElement.textContent = "The cube is already solved!";
            }
        } catch (err) {
            outputElement.textContent = `An error occurred: ${err.message}`;
        } finally {
            solveBtn.disabled = false;
        }
    }

    // --- Cube Rotation Animation ---
    let isDragging = false;
    let previousX, previousY;
    let rotationX = -33, rotationY = -45;
    let velocityX = 0, velocityY = 0;
    const damping = 0.95; // Slower decay for a longer spin

    sceneElement.addEventListener('mousedown', (e) => {
        isDragging = true;
        previousX = e.clientX;
        previousY = e.clientY;
        sceneElement.style.cursor = 'grabbing';
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            sceneElement.style.cursor = 'grab';
        }
    });

    document.addEventListener('mouseleave', () => {
        if (isDragging) {
            isDragging = false;
            sceneElement.style.cursor = 'grab';
        }
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = e.clientX - previousX;
        const dy = e.clientY - previousY;

        // Velocity is the change in position
        velocityY = dx * 0.5;
        velocityX = dy * 0.5;

        rotationY += velocityY;
        rotationX -= velocityX;

        previousX = e.clientX;
        previousY = e.clientY;
    });

    function animateCube() {
        if (!isDragging) {
            // Apply damping to velocity
            velocityX *= damping;
            velocityY *= damping;
        }

        if (Math.abs(velocityX) > 0.01 || Math.abs(velocityY) > 0.01) {
            rotationX -= velocityX;
            rotationY += velocityY;
        }

        // Clamp rotation on X-axis to prevent flipping upside down
        rotationX = Math.max(-90, Math.min(90, rotationX));

        cubeElement.style.transform = `rotateX(${rotationX}deg) rotateY(${rotationY}deg)`;
        requestAnimationFrame(animateCube);
    }

    // --- Event Listeners ---
    solveBtn.addEventListener('click', solveCube);
    resetBtn.addEventListener('click', () => {
        createStickers();
        outputElement.textContent = 'Cube has been reset to solved state.';
    });

    // --- Initial setup ---
    createStickers();
    animateCube();
});