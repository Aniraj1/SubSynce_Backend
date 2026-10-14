// 3-state theme toggle: light -> dark -> system. Any element with
// [data-theme-toggle] cycles the theme; the choice persists per browser.
(function () {
    var ORDER = ['light', 'dark', 'system'];
    var ICONS = { light: 'light_mode', dark: 'dark_mode', system: 'contrast' };
    var LABELS = { light: 'Light theme', dark: 'Dark theme', system: 'System theme' };
    var media = window.matchMedia('(prefers-color-scheme: dark)');

    function current() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    function apply(theme) {
        var dark = theme === 'dark' || (theme === 'system' && media.matches);
        var root = document.documentElement;
        root.classList.toggle('dark', dark);
        root.setAttribute('data-theme', theme);
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', dark ? '#1B1B1A' : '#F5F3F1');
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            var next = ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length];
            btn.setAttribute('aria-label', LABELS[theme] + ' (switch to ' + next + ')');
            btn.setAttribute('title', LABELS[theme]);
            var icon = btn.querySelector('[data-theme-icon]');
            if (icon) icon.textContent = ICONS[theme];
        });
    }

    document.addEventListener('click', function (event) {
        var btn = event.target.closest('[data-theme-toggle]');
        if (!btn) return;
        var next = ORDER[(ORDER.indexOf(current()) + 1) % ORDER.length];
        try { localStorage.setItem('subsync-theme', next); } catch (e) {}
        apply(next);
    });

    media.addEventListener('change', function () {
        if (current() === 'system') apply('system');
    });

    apply(current());
})();
