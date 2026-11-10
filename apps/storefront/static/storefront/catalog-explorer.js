// Small, same-origin progressive enhancement. No network requests, cookies or analytics.
(() => {
  "use strict";

  function normalizeText(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("pt-PT")
      .trim();
  }

  function readPrice(value, currency) {
    const text = String(value || "").trim();
    const amount = text ? Number(text.replace(",", ".")) : NaN;
    const code = String(currency || "").trim().toUpperCase();
    return Number.isFinite(amount) && amount >= 0 && /^[A-Z]{3}$/.test(code)
      ? { amount, currency: code }
      : null;
  }

  function withinBudget(price, limit) {
    if (!limit) return true;
    if (limit === "unknown") return price === null;
    const ceiling = Number(limit);
    return Number.isFinite(ceiling) && price !== null
      && price.currency === "EUR" && price.amount <= ceiling;
  }

  function comparePrices(left, right, direction) {
    // Non-comparable currencies stay in separate groups; no exchange rate guessed.
    if (left === null) return right === null ? 0 : 1;
    if (right === null) return -1;
    if (left.currency !== right.currency) {
      return left.currency.localeCompare(right.currency);
    }
    return (left.amount - right.amount) * (direction === "desc" ? -1 : 1);
  }

  // Export pure business rules for Node regression tests; browser usage is unchanged.
  if (typeof module === "object" && module.exports) {
    module.exports = { normalizeText, readPrice, comparePrices, withinBudget };
  }
  if (typeof document === "undefined") return;

  // Server-rendered, escaped labels. Portuguese remains the fallback.
  const uiLabels = (() => {
    try {
      return JSON.parse(document.getElementById("lowcost-js-i18n")?.textContent || "{}");
    } catch {
      return {};
    }
  })();
  const uiT = (key) => Object.prototype.hasOwnProperty.call(uiLabels, key)
    ? uiLabels[key] : key;

  function addText(parent, tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = text || "";
    parent.appendChild(element);
    return element;
  }

  // Share the exact owner-provided URL with a visible product identity;
  // never regenerate/normalize the link or share the current AliExpress page.
  async function copyOriginalAffiliateUrl(input, content = input.value) {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(content);
        return true;
      } catch {
        // Embedded browsers can block Clipboard API access.
      }
    }
    const isRawLink = content === input.value;
    const target = isRawLink ? input : document.createElement("textarea");
    if (!isRawLink) {
      target.value = content;
      target.readOnly = true;
      target.style.position = "fixed";
      target.style.opacity = "0";
      document.body.appendChild(target);
    }
    target.focus();
    target.select();
    try {
      return document.execCommand("copy");
    } catch {
      // The original link remains selectable in the visible input.
      return false;
    } finally {
      if (!isRawLink) target.remove();
    }
  }

  document.querySelectorAll("[data-affiliate-share-button]").forEach((button) => {
    button.addEventListener("click", async () => {
      const root = button.closest("[data-affiliate-actions]");
      const input = root?.querySelector("[data-affiliate-copy-value]");
      const status = root?.querySelector("[data-affiliate-share-status]");
      if (!input || !status) return;
      const productTitle = (button.dataset.shareProductTitle || "Produto").trim();
      const productId = (button.dataset.shareProductId || "").trim();
      const heading = (button.dataset.shareHeading || "Produto Low Cost Europa").trim();
      const description = heading + ": " + productTitle
        + (productId ? "\nAliExpress ID: " + productId : "");
      const completeMessage = description + "\n" + input.value;
      // Share-target apps can ignore the title. The text itself identifies
      // this product, while the original owner URL remains the URL field.
      if (typeof navigator.share === "function") {
        try {
          await navigator.share({
            title: productTitle + " | Low Cost Europa",
            text: description,
            url: input.value,
          });
          status.textContent = button.dataset.shareSuccess;
          return;
        } catch (error) {
          if (error?.name === "AbortError") return;
          // Unsupported/failed share falls back to one copyable full message.
        }
      }
      const copied = await copyOriginalAffiliateUrl(input, completeMessage);
      status.textContent = copied
        ? button.dataset.shareCopySuccess : button.dataset.shareCopyFailure;
    });
  });

  document.querySelectorAll("[data-affiliate-copy-button]").forEach((button) => {
    button.addEventListener("click", async () => {
      const root = button.closest("[data-affiliate-copy]");
      const input = root?.querySelector("[data-affiliate-copy-value]");
      const status = root?.querySelector("[data-affiliate-copy-status]");
      if (!input || !status) return;
      const copied = await copyOriginalAffiliateUrl(input);
      status.textContent = copied ? button.dataset.copySuccess : button.dataset.copyFailure;
    });
  });

  document.querySelectorAll("[data-catalog-explorer]").forEach((root) => {
    const cards = Array.from(root.querySelectorAll("[data-offer-card]"));
    const controls = root.querySelector("[data-explorer-controls]");
    if (!cards.length || !controls) return;

    const search = root.querySelector("[data-explorer-search]");
    const type = root.querySelector("[data-explorer-type]");
    const budget = root.querySelector("[data-explorer-budget]");
    const sort = root.querySelector("[data-explorer-sort]");
    const count = root.querySelector("[data-explorer-count]");
    const empty = root.querySelector("[data-explorer-empty]");
    const currencyNotice = root.querySelector("[data-currency-notice]");
    const panel = root.querySelector("[data-compare-panel]");
    const grid = root.querySelector("[data-compare-results]");
    const dock = root.querySelector("[data-compare-dock]");
    const dockCount = root.querySelector("[data-compare-dock-count]");
    const dockOpen = root.querySelector("[data-compare-show]");
    const compareMessage = root.querySelector("[data-compare-message]");
    const selected = new Map();
    const lists = Array.from(root.querySelectorAll("[data-offer-list], .offer-list"));
    const sourceOrder = new Map(lists.map((list) => [
      list, Array.from(list.querySelectorAll("[data-offer-card]"))
    ]));
    const prices = new Map(cards.map((card) => [
      card, readPrice(card.dataset.price, card.dataset.currency)
    ]));
    const labels = new Map(cards.map((card) => [
      card, normalizeText(card.querySelector(".offer-title")?.textContent || "")
    ]));

    function refresh() {
      const terms = normalizeText(search.value).split(/\s+/).filter(Boolean);
      const kind = type.value;
      let visible = 0;
      cards.forEach((card) => {
        const isType = !kind ||
          (kind === "OTHER"
            ? !["DEDICATED", "COMBO"].includes(card.dataset.equipmentType)
            : card.dataset.equipmentType === kind);
        const matched = isType && withinBudget(prices.get(card), budget.value)
          && terms.every((term) => labels.get(card).includes(term));
        card.hidden = !matched;
        if (matched) visible++;
      });
      for (const [list, original] of sourceOrder) {
        const arranged = original.slice();
        if (sort.value !== "editorial") {
          arranged.sort((a, b) => {
            const result = comparePrices(
              prices.get(a), prices.get(b),
              sort.value === "price-desc" ? "desc" : "asc"
            );
            return result || original.indexOf(a) - original.indexOf(b);
          });
        }
        arranged.forEach((card) => list.appendChild(card));
        const group = list.closest("[data-offer-group]");
        if (group) group.hidden = !arranged.some((card) => !card.hidden);
      }
      count.textContent = visible + " " + uiT("de") + " " + cards.length
        + " " + uiT("ofertas nesta lista");
      empty.hidden = visible !== 0;
      const currencies = new Set(
        cards.filter((card) => !card.hidden).map((card) => prices.get(card)?.currency)
          .filter(Boolean)
      );
      currencyNotice.hidden = !budget.value
        && (sort.value === "editorial" || currencies.size < 2);
      currencyNotice.textContent = budget.value && budget.value !== "unknown"
        ? uiT("O limite aplica-se só a preços em EUR; valores de outras moedas não são convertidos.")
        : uiT("Preços de moedas diferentes não são comparados nem convertidos. Ofertas sem preço ficam no fim.");
    }

    function renderCompare() {
      grid.replaceChildren();
      for (const card of selected.values()) {
        const tile = document.createElement("article");
        tile.className = "compare-panel__item";
        const title = card.querySelector(".offer-title")?.textContent?.trim()
          || uiT("Equipamento");
        const image = card.querySelector(".offer-card__image");
        if (image && /^https:\/\//.test(image.src)) {
          const photo = document.createElement("img");
          photo.src = image.src;
          photo.alt = title;
          photo.loading = "lazy";
          tile.appendChild(photo);
        }
        addText(tile, "h4", "", title);
        addText(tile, "small", "", uiT("Preço observado"));
        addText(tile, "strong", "compare-panel__price",
          card.querySelector(".offer-price-block .price")?.textContent?.trim()
          || uiT("Não disponível"));
        addText(tile, "small", "", uiT("Logística observada"));
        addText(tile, "p", "",
          card.querySelector(".facts dd")?.textContent?.trim() || uiT("Prazo não confirmado"));
        const actions = document.createElement("div");
        actions.className = "compare-panel__actions";
        const href = card.querySelector('.offer-cta a[href^="/go/"]')?.getAttribute("href");
        if (href && /^\/go\/\d+\/$/.test(href)) {
          const link = document.createElement("a");
          link.href = href;
          link.target = "_blank";
          link.rel = "sponsored nofollow noopener";
          link.textContent = uiT("Ver no AliExpress") + " ↗";
          link.className = "button button--secondary";
          actions.appendChild(link);
        }
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "compare-panel__remove";
        remove.textContent = uiT("Retirar");
        remove.addEventListener("click", () => toggle(card));
        actions.appendChild(remove);
        tile.appendChild(actions);
        grid.appendChild(tile);
      }
      panel.hidden = selected.size === 0;
      if (dock && dockCount) {
        dock.hidden = selected.size === 0;
        dockCount.textContent = selected.size + " " + uiT("de 3 equipamentos selecionados");
      }
    }

    function toggle(card) {
      const key = card.dataset.offerId;
      const button = card.querySelector("[data-compare-toggle]");
      if (selected.has(key)) selected.delete(key);
      else if (selected.size < 3) selected.set(key, card);
      else {
        if (compareMessage) compareMessage.textContent = uiT("Limite de três equipamentos. Retire um para acrescentar outro.");
        return;
      }
      if (compareMessage) compareMessage.textContent = "";
      for (const item of cards) {
        const active = selected.has(item.dataset.offerId);
        const control = item.querySelector("[data-compare-toggle]");
        if (!control) continue;
        control.setAttribute("aria-pressed", String(active));
        control.textContent = active ? "✓ " + uiT("Na comparação") : uiT("+ Comparar equipamento");
      }
      renderCompare();
    }

    cards.forEach((card) => {
      const button = card.querySelector("[data-compare-toggle]");
      if (!button) return;
      button.hidden = false;
      button.addEventListener("click", () => toggle(card));
    });

    if (dockOpen) dockOpen.addEventListener("click", () => {
      if (panel.hidden) return;
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      panel.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
      panel.querySelector("[data-compare-heading]")?.focus({ preventScroll: true });
    });

    root.querySelector("[data-explorer-reset]").addEventListener("click", () => {
      search.value = "";
      type.value = "";
      budget.value = "";
      sort.value = "editorial";
      refresh();
      search.focus();
    });
    root.querySelector("[data-compare-clear]").addEventListener("click", () => {
      Array.from(selected.values()).forEach((card) => toggle(card));
    });
    search.addEventListener("input", refresh);
    type.addEventListener("change", refresh);
    budget.addEventListener("change", refresh);
    sort.addEventListener("change", refresh);
    controls.hidden = false;
    refresh();
  });
})();
