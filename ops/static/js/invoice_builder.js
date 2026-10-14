// Invoice builder: add/remove line items and keep totals live.
// Rows are renumbered on every change so Django's formset sees
// items-0..items-(n-1) and TOTAL_FORMS matches.
(function () {
    var form = document.getElementById('invoice-form');
    if (!form) return;
    var list = document.getElementById('items');
    var template = document.getElementById('item-template');
    var totalForms = form.querySelector('input[name="items-TOTAL_FORMS"]');
    var gstBox = document.getElementById('id_gst');
    var money = new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' });

    function cents(value) {
        var n = parseFloat(value);
        return isFinite(n) ? Math.round(n * 100) : 0;
    }

    function renumber() {
        var rows = list.querySelectorAll('.item-row');
        rows.forEach(function (row, i) {
            row.querySelectorAll('input').forEach(function (input) {
                input.name = input.name.replace(/items-(\d+|__i__)-/, 'items-' + i + '-');
            });
            row.querySelector('.remove-item').disabled = rows.length === 1;
        });
        totalForms.value = rows.length;
    }

    function recalc() {
        var total = 0, qty = 0, rows = list.querySelectorAll('.item-row');
        rows.forEach(function (row) {
            var q = row.querySelector('[name$="-quantity"]').value;
            var p = row.querySelector('[name$="-unit_price"]').value;
            // quantity has 2 decimals, so cents * cents / 100 keeps it in cents
            var line = Math.round(cents(q) * cents(p) / 100);
            row.querySelector('.line-total').textContent = money.format(line / 100);
            total += line;
            qty += parseFloat(q) || 0;
        });
        // GST is 10% of the ex-GST subtotal, rounded to the cent (ops.services.invoice_totals).
        var gst = gstBox && gstBox.checked ? Math.round(total / 10) : 0;
        form.querySelectorAll('[data-gst-row]').forEach(function (row) {
            row.classList.toggle('hidden', !(gstBox && gstBox.checked));
        });
        document.getElementById('subtotal').textContent = money.format(total / 100);
        document.getElementById('gst-total').textContent = money.format(gst / 100);
        document.getElementById('grand-total').textContent = money.format((total + gst) / 100);
        document.getElementById('line-count').textContent = rows.length;
        document.getElementById('qty-total').textContent = Math.round(qty * 100) / 100;
    }

    document.getElementById('add-item').addEventListener('click', function () {
        list.appendChild(template.content.cloneNode(true));
        renumber();
        recalc();
        list.lastElementChild.querySelector('input').focus();
    });

    list.addEventListener('click', function (event) {
        var btn = event.target.closest('.remove-item');
        if (!btn || btn.disabled) return;
        btn.closest('.item-row').remove();
        renumber();
        recalc();
    });

    list.addEventListener('input', recalc);
    if (gstBox) gstBox.addEventListener('change', recalc);

    // Client invoices: show who is billed and suggest the site's price.
    var sitePicker = form.querySelector('[data-site-picker]');
    function showBillTo(suggestPrice) {
        var opt = sitePicker.options[sitePicker.selectedIndex];
        var picked = opt && opt.value;
        document.getElementById('bill-to-name').textContent = picked ? opt.dataset.client.trim() : 'Choose a site';
        document.getElementById('bill-to-contact').textContent = picked
            ? [opt.dataset.email, opt.dataset.phone].filter(Boolean).join(' · ') : '';
        document.getElementById('bill-to-address').textContent = picked ? opt.dataset.address : '';
        if (!picked || !suggestPrice) return;
        // Only fill a single untouched row, never overwrite what was typed.
        var rows = list.querySelectorAll('.item-row');
        var price = rows.length === 1 && rows[0].querySelector('[name$="-unit_price"]');
        var desc = rows.length === 1 && rows[0].querySelector('[name$="-description"]');
        if (price && !price.value) {
            price.value = opt.dataset.price;
            if (!desc.value) desc.value = 'Cleaning services · ' + opt.textContent.split(' · ')[0].trim();
            recalc();
        }
    }
    if (sitePicker) {
        sitePicker.addEventListener('change', function () { showBillTo(true); });
        showBillTo(false);
    }

    form.addEventListener('submit', function () {
        var btn = form.querySelector('button:not([type="button"])');
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
    });

    // Focus the first field with an error after a failed submit.
    var invalid = form.querySelector('[aria-invalid="true"]');
    if (invalid) invalid.focus();

    renumber();
    recalc();
})();
