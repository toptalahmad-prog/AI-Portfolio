# Floating Bottom Nav Dock - Code Template

## HTML

```html
<nav>
    <!-- Utility Zone - Left Icons -->
    <ul class="nav-utility">
        <li><a href="#home" class="active">
            <svg>...</svg>
            <span class="nav-label">Home</span>
        </a></li>
        <li><a href="#about">
            <svg>...</svg>
            <span class="nav-label">About</span>
        </a></li>
        <li><a href="#projects">
            <svg>...</svg>
            <span class="nav-label">Projects</span>
        </a></li>
        <li><a href="#contact">
            <svg>...</svg>
            <span class="nav-label">Contact</span>
        </a></li>
    </ul>

    <!-- Action Zone - Right Buttons -->
    <div class="nav-actions">
        <a href="#" class="nav-action-btn jogi">Get Started</a>
        <a href="#" class="nav-action-btn book">Book Call</a>
    </div>
</nav>
```

## CSS

```css
/* Main Dock */
nav {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: rgba(12, 12, 18, 0.95);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 50px;
    box-shadow: 
        0 15px 50px rgba(0, 0, 0, 0.6),
        0 0 30px rgba(0, 240, 255, 0.2),
        0 0 60px rgba(0, 240, 255, 0.1);
    max-width: 95vw;
}

/* Utility Zone */
.nav-utility {
    display: flex;
    align-items: center;
    gap: 4px;
    list-style: none;
    margin: 0;
    padding: 0;
}

.nav-utility a {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    position: relative;
    width: 44px;
    height: 44px;
    padding-left: 11px;
    border-radius: 14px;
    color: #8a8a8a;
    text-decoration: none;
    transition: all 0.3s ease-out;
}

.nav-utility a svg {
    width: 22px;
    height: 22px;
    fill: currentColor;
}

.nav-utility a .nav-label {
    position: absolute;
    left: 42px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #f5f5f5;
    white-space: nowrap;
    opacity: 0;
    transform: translateX(-10px);
    transition: all 0.3s ease-out;
    pointer-events: none;
}

.nav-utility a:hover {
    width: 105px;
    background: rgba(255, 255, 255, 0.08);
    color: #f5f5f5;
}

.nav-utility a:hover .nav-label {
    opacity: 1;
    transform: translateX(0);
}

.nav-utility a.active {
    color: #00f0ff;
}

/* Action Zone */
.nav-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-left: 4px;
    padding-left: 8px;
    border-left: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px 18px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    text-decoration: none;
    border-radius: 20px;
    transition: all 0.3s ease;
    white-space: nowrap;
}

/* Primary CTA */
.nav-action-btn.jogi {
    background: linear-gradient(135deg, #00f0ff, #ff00ff);
    color: #ffffff;
    box-shadow: 0 4px 15px rgba(0, 240, 255, 0.25);
}

.nav-action-btn.jogi:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(0, 240, 255, 0.4);
}

/* Secondary CTA */
.nav-action-btn.book {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #f5f5f5;
}

.nav-action-btn.book:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #00f0ff;
    color: #00f0ff;
}
```

## Mobile Responsive

```css
@media (max-width: 600px) {
    nav {
        bottom: 15px;
        padding: 8px 10px;
        border-radius: 30px;
        max-width: 95%;
        gap: 4px;
    }

    .nav-utility a {
        width: 38px;
        height: 38px;
    }

    .nav-utility a svg {
        width: 18px;
        height: 18px;
    }

    .nav-utility a .nav-label {
        display: none;
    }

    .nav-utility a:hover {
        width: 38px;
        background: transparent;
    }

    .nav-action-btn {
        padding: 8px 10px;
        font-size: 0.55rem;
    }
}
```