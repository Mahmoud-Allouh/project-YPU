/** Precise filter for Website "+ New" tiles (frontend, editor, backend) **/
(function () {
    const CONFIG_URL = "/website_new_menu_control/config";

    function norm(s) { return (s || "").trim().toLowerCase(); }

    async function getConfig() {
        try {
            const res = await fetch(CONFIG_URL, { method: "GET", credentials: "same-origin" });
            if (!res.ok) return null;
            return await res.json();
        } catch (_) {
            return null;
        }
    }

    function buildSelectors(cfg) {
        const sels = [];
        if (cfg.wnm_hide_page)     sels.push('.o_new_content_element[aria-label="New Page"]');
        if (cfg.wnm_hide_blog)     sels.push('.o_new_content_element[aria-label="Blog Post"]', '[data-module-xml-id*="website_blog"]');
        if (cfg.wnm_hide_event)    sels.push('.o_new_content_element[aria-label="Event"]',     '[data-module-xml-id*="website_event"]');
        if (cfg.wnm_hide_forum)    sels.push('.o_new_content_element[aria-label="Forum"]',     '[data-module-xml-id*="website_forum"]');
        if (cfg.wnm_hide_job)      sels.push('.o_new_content_element[aria-label="Job Position"]', '[data-module-xml-id*="website_hr_recruitment"]');
        if (cfg.wnm_hide_product)  sels.push('.o_new_content_element[aria-label="Product"]',   '[data-module-xml-id*="website_sale"]');
        if (cfg.wnm_hide_course)   sels.push('.o_new_content_element[aria-label="Course"]',    '[data-module-xml-id*="website_slides"]');
        if (cfg.wnm_hide_appointment) {
            sels.push(
                '.o_new_content_element[aria-label="Livechat Widget"]',
                '.o_new_content_element[aria-label="Live Chat Widget"]',
                '[data-module-xml-id*="website_livechat"]'
            );
        }
        return sels.map(s => s.startsWith('.') || s.startsWith('[') ? s : `.o_new_content_element${s}`);
    }

    function hideMatches(selectors) {
        if (!selectors.length) return;
        const combined = selectors.join(", ");
        document.querySelectorAll(combined).forEach((el) => {
            const tile = el.closest("button.o_new_content_element, a.o_new_content_element");
            (tile || el).remove();
        });
    }

    function burstHide(selectors, times = 8, everyMs = 120) {
        let i = 0;
        const id = setInterval(() => {
            try { hideMatches(selectors); } catch (_) {}
            if (++i >= times) clearInterval(id);
        }, everyMs);
    }

    async function boot() {
        const cfg = await getConfig();
        if (!cfg) return;

        const selectors = buildSelectors(cfg);
        const run = () => burstHide(selectors);

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", run, { once: true });
        } else {
            run();
        }

        const mo = new MutationObserver(() => hideMatches(selectors));
        mo.observe(document.body, { childList: true, subtree: true });

        document.addEventListener("click", (ev) => {
            const t = ev.target;
            if (!t) return;
            if (
                t.closest(".o_website_new_menu") ||
                t.closest(".o_new_content_menu") ||
                t.closest(".o_new_content_menu_choices") ||
                t.closest(".dropdown-toggle") ||
                norm(t.innerText).includes("+ new")
            ) {
                setTimeout(() => burstHide(selectors), 0);
            }
        }, true);
    }

    boot();
})();
