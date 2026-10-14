// Static, same-origin progressive enhancement: never fetches remote data itself.
(() => {
  const MIN_WIDTH = 360;
  const MIN_HEIGHT = 270;

  for (const image of document.querySelectorAll("img[data-product-image]")) {
    const container = image.parentElement;
    const fallback = container.querySelector("[data-image-fallback]");
    const qualityNote = container.querySelector("[data-image-quality]");

    const showFallback = () => {
      image.hidden = true;
      if (qualityNote) qualityNote.hidden = true;
      container.classList.add(
        container.classList.contains("offer-card__media")
          ? "offer-card__media--placeholder"
          : "product-card__media--placeholder"
      );
      if (fallback) fallback.hidden = false;
    };

    const assessResolution = () => {
      if (!image.naturalWidth || !image.naturalHeight) {
        showFallback();
        return;
      }
      if (image.naturalWidth < MIN_WIDTH || image.naturalHeight < MIN_HEIGHT) {
        // Never enlarge a low-resolution supplier photograph to fill the card.
        image.style.maxWidth = image.naturalWidth + "px";
        image.style.maxHeight = image.naturalHeight + "px";
        if (qualityNote) qualityNote.hidden = false;
      }
    };

    image.addEventListener("error", showFallback);
    image.addEventListener("load", assessResolution);
    // Lazy images can report complete before the browser has requested them.
    // Do not show a false "unavailable" warning while they are still pending.
    if (image.complete && image.naturalWidth > 0) {
      assessResolution();
    } else if (image.complete && image.loading !== "lazy") {
      showFallback();
    }
  }
})();
